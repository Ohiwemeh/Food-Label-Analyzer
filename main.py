"""Runnable demonstration of the Food Label Analyzer storage module."""
from food_product import FoodProduct
from storage import ScanLogger, StorageError

def main():
    logger = ScanLogger()
    sample = FoodProduct(
        name="Wholegrain Cereal",
        barcode="8901234567890",
        ingredients=["Whole wheat", "Sugar", "Salt", "Vitamins"],
        nutrition_facts={"serving_size": "30g", "calories": 115, "protein_g": 3.5,
                         "carbohydrates_g": 22, "fat_g": 1.2},
    )
    try:
        logger.save_scan(sample)
        print(f"Saved scan: {sample.name}")
        history = logger.load_scans()
        print(f"Total saved scans: {len(history)}")
        print("Latest scan:", history[-1])
    except StorageError as error:
        print(f"Storage problem: {error}")

if __name__ == "__main__":
    main()
