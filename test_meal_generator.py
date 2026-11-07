from meal_suggestion_generator import MealSuggestionGenerator

generator = MealSuggestionGenerator()

ingredients = [] 

print("Detected allergens:")
print(generator.detect_allergens(ingredients))

print("Recipe suggestions:")
print(generator.suggest_recipes(ingredients))

print("Healthier swaps")
print(generator.suggest_swaps(ingredients))
