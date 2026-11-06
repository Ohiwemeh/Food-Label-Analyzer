import streamlit as st

# ---- Real modules if they exist, otherwise mocks so the UI always runs ----
try:
    from food_api import OpenFoodFactsClient, validate_barcode
    from nutrition_analyzer import NutritionAnalyzer
    from meal_suggestions import MealSuggestionGenerator
    from models import FoodProduct
    import storage
    USING_MOCKS = False
except ImportError:
    USING_MOCKS = True

    class FoodProduct:
        def __init__(self, name, barcode, ingredients, nutrition_facts, allergens=None):
            self.name, self.barcode = name, barcode
            self.ingredients, self.nutrition_facts = ingredients, nutrition_facts
            self.allergens = allergens or []

        @classmethod
        def from_api(cls, d):
            return cls(d["name"], d["barcode"], d["ingredients"], d["nutrition"])

        def to_dict(self):
            return self.__dict__

    def validate_barcode(code):
        return code.isdigit() and len(code) in (8, 12, 13)

    class OpenFoodFactsClient:
        def get_by_barcode(self, code):
            return {"name": "Mock Spread", "barcode": code,
                    "ingredients": "sugar, palm oil, hazelnuts, skimmed milk powder",
                    "nutrition": {"sugar_g": 56.3, "fat_g": 30.9, "sodium_g": 0.04, "kcal": 539}}

        def search_by_name(self, name):
            return self.get_by_barcode("3017620422003")

    class NutritionAnalyzer:
        def analyze(self, p):
            return "**Mock verdict:** very high in sugar and fat."

    class MealSuggestionGenerator:
        def detect_allergens(self, p):
            return ["nuts", "dairy"]

        def suggest(self, p):
            return "- Mashed banana on toast\n- Homemade date and nut spread"

    class storage:
        _log = []

        @staticmethod
        def save_scan(p):
            storage._log.append(p.to_dict())

        @staticmethod
        def load_history():
            return storage._log


st.set_page_config(page_title="Food Label Decoder", page_icon="🥗", layout="wide")
st.title("🥗 Food Label Decoder")
if USING_MOCKS:
    st.warning("Running with mock modules. Real teammate modules not found yet.")

tab_scan, tab_history = st.tabs(["Scan", "History"])

with tab_scan:
    mode = st.radio("Look up by", ["Barcode", "Product name"], horizontal=True)
    query = st.text_input("Enter barcode" if mode == "Barcode" else "Enter product name")

    if st.button("Analyze", type="primary"):
        query = query.strip()
        if not query:
            st.error("Please enter something first.")
            st.stop()
        if mode == "Barcode" and not validate_barcode(query):
            st.error("That doesn't look like a valid EAN-13 / UPC-A barcode.")
            st.stop()

        try:
            with st.spinner("Fetching product..."):
                client = OpenFoodFactsClient()
                raw = client.get_by_barcode(query) if mode == "Barcode" else client.search_by_name(query)
                product = FoodProduct.from_api(raw)
        except Exception as e:  # narrow to your teammates' custom exceptions later
            st.error(f"Couldn't fetch that product: {e}")
            st.stop()

        left, right = st.columns(2)
        with left:
            st.subheader(product.name)
            st.caption(f"Barcode: {product.barcode}")
            st.write("**Ingredients:**", product.ingredients)
            st.table(product.nutrition_facts)

        try:
            product.allergens = MealSuggestionGenerator().detect_allergens(product)
        except Exception as e:
            st.warning(f"Allergen check failed: {e}")
        if product.allergens:
            st.error("⚠️ Allergens: " + ", ".join(product.allergens))

        with right:
            try:
                with st.spinner("Asking the AI nutritionist..."):
                    st.markdown(NutritionAnalyzer().analyze(product))
            except Exception as e:
                st.warning(f"AI analysis unavailable: {e}")
            try:
                st.subheader("Healthier ideas")
                st.markdown(MealSuggestionGenerator().suggest(product))
            except Exception as e:
                st.warning(f"Suggestions unavailable: {e}")

        try:
            storage.save_scan(product)
            st.toast("Saved to your food log")
        except Exception as e:
            st.warning(f"Couldn't save to log: {e}")

with tab_history:
    try:
        history = storage.load_history()
        st.dataframe(history, use_container_width=True) if history else st.info("No scans yet.")
    except Exception as e:
        st.error(f"Couldn't load history: {e}")
