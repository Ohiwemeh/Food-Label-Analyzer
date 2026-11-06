"""JSON-based local scan history storage."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from food_product import FoodProduct

class StorageError(Exception):
    """Base error for scan-history storage."""

class CorruptedLogError(StorageError):
    """Raised when the saved history is not valid JSON data."""

class ScanLogger:
    def __init__(self, file_path: str | Path = "data/scan_history.json"):
        self.file_path = Path(file_path)

    def _read_entries(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise CorruptedLogError(f"Invalid JSON in {self.file_path}") from exc
        except PermissionError as exc:
            raise StorageError(f"Permission denied reading {self.file_path}") from exc
        except OSError as exc:
            raise StorageError(f"Could not read scan history: {exc}") from exc
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise CorruptedLogError("Scan history must be a JSON list of objects.")
        return data

    def save_scan(self, product: FoodProduct) -> None:
        if not isinstance(product, FoodProduct):
            raise TypeError("save_scan expects a FoodProduct object.")
        entries = self._read_entries()
        entry = product.to_dict()
        entry["scanned_at"] = datetime.now(timezone.utc).isoformat()
        entries.append(entry)
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(entries, file, indent=4, ensure_ascii=False)
        except PermissionError as exc:
            raise StorageError(f"Permission denied writing {self.file_path}") from exc
        except OSError as exc:
            raise StorageError(f"Could not save scan history: {exc}") from exc

    def load_scans(self) -> list[dict[str, Any]]:
        return self._read_entries()

    def load_products(self) -> list[FoodProduct]:
        try:
            return [
                FoodProduct.from_dict({k: v for k, v in item.items() if k != "scanned_at"})
                for item in self._read_entries()
            ]
        except (TypeError, ValueError) as exc:
            raise CorruptedLogError(f"Invalid product data in scan history: {exc}") from exc

    def clear_history(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
        except PermissionError as exc:
            raise StorageError(f"Permission denied clearing {self.file_path}") from exc
        except OSError as exc:
            raise StorageError(f"Could not clear scan history: {exc}") from exc
