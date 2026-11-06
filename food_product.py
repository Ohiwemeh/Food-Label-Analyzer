"""Food product data model."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class FoodProduct:
    name: str
    barcode: str
    ingredients: list[str] = field(default_factory=list)
    nutrition_facts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "barcode": self.barcode,
            "ingredients": self.ingredients,
            "nutrition_facts": self.nutrition_facts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FoodProduct":
        for key in ("name", "barcode"):
            if key not in data:
                raise ValueError(f"Missing required product field: {key}")
        return cls(
            name=str(data["name"]),
            barcode=str(data["barcode"]),
            ingredients=list(data.get("ingredients", [])),
            nutrition_facts=dict(data.get("nutrition_facts", {})),
        )
