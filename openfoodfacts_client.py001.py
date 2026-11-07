import re
import requests
from typing import Dict, Any

class OpenFoodFactsClient:
    """
    Client for interacting with the OpenFoodFacts API, featuring barcode validation,
    robust error handling, and clean dictionary parsing.
    """
    
    # Standard barcode regex patterns (EAN-8, EAN-13, UPC-A, UPC-E)
    BARCODE_PATTERNS = {
        "EAN-8": re.compile(r"^\d{8}$"),
        "UPC-A": re.compile(r"^\d{12}$"),
        "EAN-13": re.compile(r"^\d{13}$"),
        "UPC-E": re.compile(r"^\d{6,8}$")
    }
    
    BASE_URL = "https://world.openfoodfacts.org/api/v2/product"

    def __init__(self, user_agent: str = "BarcodeSpecialistApp - Python - Version 1.0"):
        self.headers = {"User-Agent": user_agent}
        self.timeout = 10.0

    def validate_barcode(self, barcode: str) -> bool:
        """Validates barcode format using Regular Expressions."""
        clean_barcode = barcode.strip()
        for pattern in self.BARCODE_PATTERNS.values():
            if pattern.match(clean_barcode):
                return True
        return False

    def get_product_by_barcode(self, barcode: str) -> Dict[str, Any]:
        """Fetches product details from OpenFoodFacts with full exception handling."""
        clean_barcode = barcode.strip()
        
        # 1. Validate barcode format first
        if not self.validate_barcode(clean_barcode):
            return {
                "success": False,
                "error": "Invalid Barcode Format",
                "message": f"'{barcode}' does not match standard EAN or UPC formats."
            }

        url = f"{self.BASE_URL}/{clean_barcode}.json"

        try:
            # 2. Make API request with timeout
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # 3. Check if product exists in database
            if data.get("status") != 1:
                return {
                    "success": False,
                    "error": "Product Not Found",
                    "message": f"No product found for barcode: {clean_barcode}"
                }

            product_raw = data.get("product", {})
            return {
                "success": True,
                "barcode": clean_barcode,
                "data": {
                    "product_name": product_raw.get("product_name", "Unknown Product"),
                    "brands": product_raw.get("brands", "Unknown Brand"),
                    "categories": product_raw.get("categories", "N/A"),
                    "ingredients_text": product_raw.get("ingredients_text", "Ingredients not listed"),
                    "nutriscore_grade": product_raw.get("nutriscore_grade", "N/A").upper(),
                    "image_url": product_raw.get("image_front_url", None)
                }
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout Error", "message": "The request timed out."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection Error", "message": "Failed to connect to the internet."}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": "Network Error", "message": str(e)}
        except ValueError:
            return {"success": False, "error": "Parsing Error", "message": "Failed to parse JSON response."}


# ==========================================
# Quick Test Block (Runs live when executed)
# ==========================================
if __name__ == "__main__":
    client = OpenFoodFactsClient()

    # Testing with a real product barcode (Nutella: 3017620422003)
    test_barcode = "3017620422003"
    print(f"Testing barcode lookup for: {test_barcode}...")
    
    result = client.get_product_by_barcode(test_barcode)
    
    if result["success"]:
        print("\n✅ Product Found Successfully!")
        print(f"Name: {result['data']['product_name']}")
        print(f"Brand: {result['data']['brands']}")
        print(f"Nutri-Score: {result['data']['nutriscore_grade']}")
    else:
        print(f"\n❌ Error: {result['error']} - {result['message']}")