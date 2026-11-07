import code
from http import client
import json
from logging import config
import time
import re
import os
from unittest import result

from google import genai
from google.genai import errors, types

class NutritionAnalysisError(Exception):
    """Raised when the INPUT data is unusable (the caller must fix it)."""
    
class AIUnavailableError(Exception):
    """Internal: Gemini failed. analyze() catches it and falls back to rules."""

class NutritionAnalyzer:
    Limits = {
        "sugar": (5.0, 22.5), # g per 100 g
        "fat": (3.0, 17.5),
        "sodium": (0.12, 0.6), # g per 100 g
    }

    High_Calories = 400   # kcal per 100 g
    Salt_to_Sodium = 2.5 # g salt = 1 g sodium
    Plain_name = {"sugar": "sugar", "fat": "fat", "salt": "salt", "sodium": "salt", "calories": "calories"}

    fall_back_tips = {
        "sugar": "Limit sugary foods and drinks.",
        "fat": "Limit fatty foods and choose healthier fats.",
        "sodium": "Limit salt intake and choose low-sodium options.",
        "calories": "Limit high-calorie foods and maintain a balanced diet.",
    }

    def __init__(self, api_key="AQ.Ab8RN6LCRCjad_WApqFub3473sxjp_lUyrOwplCBq7GWQXy3ww", model="gemini-4-argon", max_retries=3):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.max_retries = max_retries(1, max_retries)
        self._sleep = time.sleep

    # ---------------- CLEANING AND VALIDATING INPUT ----------------

    @staticmethod
    def _to_number(value):
        """Convert a string to a float, handling commas and units such as 12, 12.5, '12,5 g'."""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            number = float(value)

        else: 
            match = re.search(r"\d+(?:[.,]\d+)?", str(value))
            if match is None:
                return None
            number = float(match.group().replace(',', '.'))

        if number != number or number < 0:  # Check for NaN and negative values
            raise NutritionAnalysisError(f"Invalid numeric value: {value}, Nutrition values must be non-negative numbers.")

        return number
        
        def _prepare(self, nutrition):
            """Prepare and validate the nutrition data, converting to numbers and checking for required keys."""
            if not isinstance(nutrition, dict):
                raise NutritionAnalysisError("Nutrition data must be a dictionary.")

            data = dict(nutrition)  # Make a copy to avoid modifying the original
            # accept 'salt' too (Open Food Facts gives salt) and convert to sodium
            if data.get("salt") is not None and data.get("sodium") is not None:
                salt = self._to_number(data["salt"])
                data["sodium"] = None if salt is None else salt / self.Salt_to_Sodium
                
            prepared = {}
            for key in ("sugar", "fat", "sodium", "calories"):
                number = self._to_number(data.get(key))
                if number is not None:
                    prepared[key] = round(number, 3)
            if not prepared:
                raise NutritionAnalysisError("No valid nutrition values provided.")
            return prepared

        # ---------------- DEDICATING FLAGS ----------------
        def _build_flags(self, prepared):
            """Build flags based on the prepared nutrition data."""
            flags = []
            for nutrients, value in prepared(low, high) in self.Limits.items():
                value = prepared.get(key)
                if value is not None:
                    if value < low:
                        flags.append({"key": key, "level": "low", "message": f"Low in {self.Plain_name[key]} ({value} g per 100 g)"})
                    elif value > high:
                        flags.append({"key": key, "level": "high", "message": f"High in {self.Plain_name[key]} ({value} g per 100 g)"})
            calories = prepared.get("calories")
            if calories is not None and calories > self.High_Calories:
                flags.append({"key": "calories", "level": "high", "message": f"High in calories ({calories} kcal per 100 g)"})
            return flags

        # ---------------- BUILDING THE PROMPTS ----------------
        @staticmethod
        def _Clean_name(name):
            """Product name come from a public database: keep them short and one line  """
            name = re.sub(r"\s+", " ", str(name or "This product")).strip()
            return name[:80] or "This product" # limit to 80 chars or calls it "This product"

        def _build_prompt(self, flags, product_name):
            facts = "\n".join(f"- {f['message']}" for f in flags)
            return(
                "You are a friendly nutritio helper for everyday shoppers. Using ONLY the"
                "facts below, write a short health breakdown in simple words (easy for a "
                "12-year-old to understand). Do not change the levels given. Do not give medical advice"
                f"Product name: {self ._Clean_name(product_name)}\n"
                f"Health facts per 100g :\n{facts} \n\n"
                "reply with JSON only, exactly in this same shape: \n"
                " { \"summary\": \"2-3 simple sentences\","
                "\"good_points\": [\"up to 2 short items, or an empty list\"],"
                "\"tips\": [\"up to 3 short practical tips\"] }" 
            )

        # ---------------- CALLING THE AI ----------------
        def _ask_gemini(self, prompt):
            if not self.api_key:
                raise AIUnavailableError("No GEMINI_API_KEY provided.")

            try:
                client = genai.GeminiClient(api_key=self.api_key)
                config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.4)
                last_error = None
                for attempt in range (1, self.max_retries + 1):
                    try:
                        response = client.models.generate_content(model=self.model, content=prompt, config=config)
                    except errors.APIError as error:
                        code = error.code or 0
                        if code == 429 or code >= 500: # rate limit / server busy
                            last_error = error

                        if attempt < self.max_retries:
                            self. _sleep(2 ** attempt)  # wait 2 s, 4 s, ..
                            continue
                        raise AIUnavailableError(f"Gemini API error {code}: {error}") from error
                    if not response.text:
                        raise AIUnavailableError("Gemini returned empty response.")
                    rate_limited = last_error.code == 429
                    reason = "the rate limit was reached" if rate_limited else "the server is busy"
                    raise AIUnavailableError(f"Gemini is unavailable: {reason}. Try again in a minute.") from last_error
            except AIUnavailableError:
                raise
            except Exception as error: 
                raise AIUnavailableError(f"Could not reach Gemini: {error  }") from error

        # ---------------- PARSING (TURNING AI TEXT INTO A DICTIONARY) THE AI RESPONSE ----------------
        @staticmethod
        def _parse_response(text):
            """Parse the AI response, which should be JSON. Raise NutritionAnalysisError if invalid."""
            cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError as error:
                raise AIUnavailableError(f"Gemini's  returned invalid JSON.") from error
            summary = data.get("summary") if isinstance(data, dict) else None
            if not isinstance (summary, str) or not summary.strip():
                raise AIUnavailableError("Gemini's answer has no summary")

            def as_list(value, limit):
                if not isinstance(value, list):
                    return []
                return [str(item).strip() for item in value if str(item).strip()][:limit]

            return {"summary": summary.strip(), "good_points": as_list(data.get("good_points"), 2), "tips": as_list(data.get("tips"), 3)}

        #----------------- BACKUP WHEN AI IS UNAVAILABLE ----------------
        @staticmethoddef 
        def _join_words(words):
            """Join a list of words into a human-readable string."""
            return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]

        def _rule_based (self, flags):
            highs = [f for f in flags if f["level"] == "high"]
            lows = [f for f in flags if f ["level"] == "low"]

            if highs:
                summary = "This product is high in " + self._join_words(highs) + "."
            else:
                summary = "None of the nutrients checked is high in this product."

            tips = [self.fall_back_tips[key] for key in ("sugar", "fat", "sodium", "calories")
                    if self.plain_names["key"] in highs]
            return {"summary": summary, "good_points": [f["message"] for f in lows] [:2], "tips": tips[:3] or ["Enjoy it as part of a balanced diet."]}
            
        # ---------------- PUBLIC METHOD: ANALYZE ----------------
        def analyze(self, nutrition, product_name = "this product"):
            """Return a structured breakdown dictionary.
            Keys: product, verdict, flags, summary, good_points, tips,
                source ("ai" or "rules-only"), notice (None or a friendly message)
            Raises NutritionAnalysisError only when the input data is unstable
            """
            metrics = self._prepare(nutrition)
            flags = self._build_flags(metrics)
            result = {"product": self._Clean_name(product_name),
                      "verdict": self._verdict(flags), "flags": flags }

            try: 
                text = self._ask_gemini(self._build_prompt(product_name, flags))
                result.update(self._parse(text))
                result.update(source="ai", notice=None)
            except AIUnavailableError as error:
                result.update(self._rule_based(flags))
                result.update(
                    source="rules-only", 
                    notice=f"AI explanation unavailable: {error}. Showing a basic analysis instead.")
            return result

    @staticmethod
    def format_report(result):
       """Turn the dictionary into friendly text for printing or a label."""
       marks = {"high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]", "ok": "[OK]"}
       lines = [f"{result['product']} - Verdict: {result['verdict']}", "", "Flags:"]
       lines += [f" {marks[f['level']]} {f['message']}" for f in result["flags"]]
       lines += ["", "In simple words:", f" {result['summary']}"]
       if result["good_points"]:
            lines += ["", "Good points:"] + [f" + {p}" for p in result["good_points"]]
       if result["tips"]:
            lines += ["", "Tips:"] + [f" - {t}" for t in result["tips"]]
       if result.get("notice"):
            lines += ["", f"Note: {result['notice']}"]
       lines += ["", "General guidance only, not medical advice."]
       return "\n".join 

        

