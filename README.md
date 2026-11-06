# Food Label Analyzer — Data Model & File Logger

This module is one contribution to the team project. It provides the `FoodProduct` data model and local JSON scan-history storage.

## Files
- `food_product.py`: FoodProduct data class and dictionary conversion.
- `storage.py`: ScanLogger for saving and loading scan history.
- `main.py`: runnable demonstration.
- `data/`: directory created/used for local scan history.

## Requirements
Python 3.9 or newer. No third-party packages are required.

## Run
Open a terminal in this folder and run:
```bash
python main.py
```
The program saves a sample scan to `data/scan_history.json` and loads the history. Run it again to add another sample entry.

## Integrate with the team project
```python
from food_product import FoodProduct
from storage import ScanLogger, StorageError

product = FoodProduct(
    name="Example Biscuit",
    barcode="1234567890123",
    ingredients=["Wheat flour", "Sugar"],
    nutrition_facts={"calories": 150, "protein_g": 2},
)
logger = ScanLogger()
logger.save_scan(product)
history = logger.load_scans()       # dictionaries, including scanned_at
products = logger.load_products()   # FoodProduct objects
```

## Error handling
- Missing history file: returns an empty list.
- Missing parent directory: created automatically on save.
- Invalid JSON or invalid entries: raises `CorruptedLogError`.
- Permission and other operating-system errors: raises `StorageError`.
- Wrong object passed to `save_scan`: raises `TypeError`.

Catch `StorageError` in the main application and show the user a friendly message.

## JSON format
The history is a JSON list. Each entry contains the product fields and a UTC `scanned_at` timestamp.

## GitHub note
Upload the files to your team's repository. `.gitignore` excludes local scan history so personal scan records are not committed.
