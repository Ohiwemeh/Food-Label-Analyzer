"""
Open Food Facts API client.

Looks up products by UPC/EAN barcode and searches by product name.
API documentation: https://openfoodfacts.github.io/documentation/
"""

import re
from typing import Any, Dict, List

import requests


class OpenFoodFactsClient:
    """Small client for the public Open Food Facts API."""

    PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

    # Common GTIN formats: UPC-E/ EAN-8 (8), UPC-A (12), EAN-13 (13), GTIN-14 (14).
    BARCODE_PATTERN = re.compile(r"^(?:\d{8}|\d{12}|\d{13}|\d{14})$")

    def __init__(self, timeout: int = 10, session: requests.Session | None = None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": "OpenFoodFactsStudentProject/1.0 (educational use)"}
        )

    @classmethod
    def validate_barcode(cls, barcode: str) -> str:
        """Validate numeric barcode length and GTIN check digit; return normalized barcode."""
        normalized = str(barcode).strip()
        if not cls.BARCODE_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Barcode must contain 8, 12, 13, or 14 digits (EAN/UPC/GTIN)."
            )

        # Validate the standard GTIN modulo-10 check digit.
        digits = [int(char) for char in normalized]
        check_digit = digits.pop()
        weighted_sum = 0
        # Starting from the right of the body, weights alternate 3 and 1.
        for index, digit in enumerate(reversed(digits)):
            weighted_sum += digit * (3 if index % 2 == 0 else 1)
        expected = (10 - (weighted_sum % 10)) % 10
        if check_digit != expected:
            raise ValueError("Barcode has an invalid check digit.")
        return normalized

    @staticmethod
    def _clean_product(barcode: str, product: Dict[str, Any]) -> Dict[str, Any]:
        """Return a predictable, simplified dictionary."""
        return {
            "barcode": barcode,
            "product_name": product.get("product_name") or "Unknown",
            "brand": product.get("brands") or "Unknown",
            "categories": product.get("categories") or "Unknown",
            "ingredients": product.get("ingredients_text") or "Unknown",
            "quantity": product.get("quantity") or "Unknown",
            "nutriscore": product.get("nutrition_grades") or "Unknown",
            "image_url": product.get("image_url") or None,
        }

    def get_product(self, barcode: str) -> Dict[str, Any]:
        """Fetch one product by barcode. Raises clear exceptions on failure."""
        normalized = self.validate_barcode(barcode)
        url = self.PRODUCT_URL.format(barcode=normalized)

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.Timeout as exc:
            raise TimeoutError("The Open Food Facts request timed out.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError("Could not connect to Open Food Facts.") from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(f"Open Food Facts returned an HTTP error: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Network request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("The API returned invalid JSON.") from exc

        if payload.get("status") != 1 or not payload.get("product"):
            raise LookupError(f"No product found for barcode {normalized}.")

        return self._clean_product(normalized, payload["product"])

    def search_product(self, product_name: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Search products by name and return a list of simplified dictionaries."""
        if not isinstance(product_name, str) or not product_name.strip():
            raise ValueError("Product name cannot be empty.")

        params = {
            "search_terms": product_name.strip(),
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": max(1, min(int(page_size), 50)),
        }

        try:
            response = self.session.get(
                self.SEARCH_URL, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.Timeout as exc:
            raise TimeoutError("The product search request timed out.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError("Could not connect to Open Food Facts.") from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Product search request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("The API returned invalid JSON.") from exc

        products = payload.get("products") or []
        results = []
        for item in products:
            code = str(item.get("code") or "").strip()
            results.append(
                {
                    "barcode": code or "Unknown",
                    "product_name": item.get("product_name") or "Unknown",
                    "brand": item.get("brands") or "Unknown",
                }
            )
        if not results:
            raise LookupError(f"No products found matching {product_name!r}.")
        return results
