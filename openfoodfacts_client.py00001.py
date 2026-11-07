import re
import requests

class OpenFoodFactsClient:
    def __init__(self):
        # Regex matching standard barcode formats (EAN-8, UPC-A, EAN-13, UPC-E)
        self.barcode_pattern = re.compile(r"^(\d{8}|\d{12}|\d{13}|\d{6,8})$")
        self.headers = {"User-Agent": "BarcodeApp/1.0"}

    def validate_barcode(self, barcode: str) -> bool:
        """Validates barcode format using Regular Expressions."""
        return bool(self.barcode_pattern.match(barcode.strip()))

    def get_product_by_barcode(self, barcode: str) -> dict:
        """Fetches product details and handles errors gracefully."""
        clean_barcode = barcode.strip()
        
        if not self.validate_barcode(clean_barcode):
            return {"success": False, "error": "Invalid barcode format."}

        url = f"https://world.openfoodfacts.org/api/v2/product/{clean_barcode}.json"

        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Check if product exists in database
            if data.get("status") != 1:
                return {"success": False, "error": "Product not found in database."}

            prod = data.get("product", {})
            return {
                "success": True,
                "barcode": clean_barcode,
                "data": {
                    "name": prod.get("product_name", "Unknown"),
                    "brand": prod.get("brands", "Unknown"),
                    "nutriscore": prod.get("nutriscore_grade", "N/A").upper()
                }
            }

        except requests.RequestException as e:
            return {"success": False, "error": f"Network error: {e}"}
        except ValueError:
            return {"success": False, "error": "Failed to parse JSON response."}

# Test the code directly
if __name__ == "__main__":
    client = OpenFoodFactsClient()
    result = client.get_product_by_barcode("3017620422003") # Nutella
    print(result)