import re
class MealSuggestionGenerator:
    def _validate_ingredients(self, ingredients):
        if not isinstance(ingredients, list):
            raise TypeError("Ingredients must be provided as a list.")

        if not all(isinstance(item, str) for item in ingredients):
            raise TypeError("Every ingredient must be a string.")

        return ingredients

    def __init__(self):
        self.allergen_keywords ={
            "Milk": ["milk", "whey", "casein", "cheese", "butter", "cream", "yogurt", "lactose"],
            "Peanuts": ["peanut", "groundnut"],
            "Tree nuts": ["almond", "cashew", "walnut", "hazelnut", "pistachio", "pecan", "macadamia", "brazil nut"],
            "Gluten": ["wheat", "barley", "rye", "malt", "semolina", "spelt", "durum"],
            "Eggs": ["egg", "albumin", "ovalbumin"],
            "Soy": ["soy", "soya", "soybean"],
            "Sesame": ["sesame"],
            "Fish": ["fish", "cod", "salmon", "tuna"],
            "Shellfish": ["shrimp", "prawn", "crab", "lobster"]}

    def detect_allergens(self, ingredients):
        ingredients = self._validate_ingredients(ingredients)
        detected = []

        for ingredient in ingredients:
            ingredient = ingredient.lower()

            for allergen, keywords in self.allergen_keywords.items():
                for keyword in keywords:
                    if re.search(r"\b" + re.escape(keyword) + r"\b", ingredient):
                        if allergen not in detected:
                            detected.append(allergen)

        return detected 

    
    def suggest_swaps(self, ingredients):
        ingredients = self._validate_ingredients(ingredients)
        suggestions = []

        detected_allergens = self.detect_allergens(ingredients)

        for ingredient in ingredients:
            ingredient = ingredient.lower()

            if "sugar" in ingredient:
                suggestions.append(
                    "Try fresh fruit for natural sweetness."
                )

            if "wheat flour" in ingredient:
                suggestions.append(
                        "Try certified gluten-free flour instead."
                    )

            if "salt" in ingredient:
                suggestions.append(
                    "Try herbs and spices for flavour instead of extra salt."
                )

        return suggestions[:3]

        

    def suggest_recipes(self, ingredients):
        ingredients = self._validate_ingredients(ingredients)
        detected_allergens = self.detect_allergens(ingredients)

        recipe_options = [
            {"name": "Vegetable rice",
                "description": "Rice cooked with carrots, peas and tomatoes.",
                "allergens": []
            },
            {
                "name": "Fruit salad",
                "description": "Chopped apples, bananas, oranges and watermelon.",
                "allergens": []
            },
            {
                "name": "Sweet potato bowl",
                "description": "Roasted sweet potatoes with steamed vegetables.",
                "allergens": []
            },
            {
                "name": "Yogurt fruit bowl",
                "description": "Fresh fruits mixed with yogurt.",
                "allergens": ["Milk"]
            },
            {"name": "Peanut butter smoothie",
                "description": "Banana blended with peanut butter.",
                "allergens": ["Peanuts"]
            },
            {"name": "Whole-wheat pancakes",
                "description": "Pancakes made with wheat flour, eggs and milk.",
                "allergens": ["Gluten", "Eggs", "Milk"]
            }
        
        ]
        recipes = []

        for recipe in recipe_options:
            if not any(
                allergen in detected_allergens
                for allergen in recipe["allergens"]
            ):
                recipes.append(recipe["description"])

        return recipes[:3]


