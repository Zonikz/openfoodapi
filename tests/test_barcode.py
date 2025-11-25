"""Test barcode lookup endpoint"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


TEST_BARCODES = [
    {
        "code": "5000159484695",
        "name": "Heinz Beans",
        "expected_fields": ["product_name", "per_100g"]
    },
    {
        "code": "5057172289345",
        "name": "Tesco product",
        "expected_fields": ["product_name", "per_100g"]
    },
    {
        "code": "5000112548167",
        "name": "Heinz Soup",
        "expected_fields": ["product_name", "per_100g"]
    },
    {
        "code": "3017620422003",
        "name": "Nutella",
        "expected_fields": ["product_name", "per_100g"]
    }
]


class TestBarcodeEndpoint:
    """Test /api/barcode endpoint"""
    
    @pytest.mark.parametrize("barcode_info", TEST_BARCODES)
    def test_barcode_lookup(self, barcode_info):
        """Test barcode lookup returns valid data"""
        code = barcode_info["code"]
        response = client.get(f"/api/barcode/{code}")
        
        # Should return 200 or 404 (if not in DB)
        assert response.status_code in [200, 404], \
            f"Unexpected status code for {code}: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields exist
            assert "canonical_name" in data or "product_name" in data, \
                f"Missing product name for {code}"
            
            assert "per_100g" in data, \
                f"Missing per_100g nutrition for {code}"
            
            # Check nutrition data structure
            nutrition = data["per_100g"]
            assert "energy_kcal" in nutrition, "Missing energy_kcal"
            assert "protein_g" in nutrition, "Missing protein_g"
            assert "carb_g" in nutrition, "Missing carb_g"
            assert "fat_g" in nutrition, "Missing fat_g"
            
            # Check values are numeric or None
            for key, value in nutrition.items():
                if value is not None:
                    assert isinstance(value, (int, float)), \
                        f"{key} should be numeric, got {type(value)}"
            
            print(f"✅ {code}: {data.get('canonical_name') or data.get('product_name')}")
        else:
            print(f"⚠️  {code}: Not found in database (expected if OFF not imported)")
    
    def test_invalid_barcode(self):
        """Test invalid barcode returns 404"""
        response = client.get("/api/barcode/INVALID123")
        assert response.status_code == 404
    
    def test_barcode_enrichment(self):
        """Test barcode returns enrichment data when available"""
        # Test with Nutella (should have NOVA, NutriScore)
        response = client.get("/api/barcode/3017620422003")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for enrichment
            if "enrichment" in data:
                enrichment = data["enrichment"]
                
                # Should have at least some enrichment fields
                has_enrichment = any([
                    enrichment.get("nova"),
                    enrichment.get("nutriscore"),
                    enrichment.get("additives"),
                    enrichment.get("categories")
                ])
                
                assert has_enrichment, "Enrichment object exists but is empty"
                print(f"✅ Enrichment data present: {enrichment}")
        else:
            pytest.skip("Barcode not in database")
    
    def test_barcode_response_structure(self):
        """Test barcode response has correct structure"""
        # Use first test barcode
        code = TEST_BARCODES[0]["code"]
        response = client.get(f"/api/barcode/{code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check top-level structure
            assert isinstance(data, dict), "Response should be a dict"
            
            # per_100g should be a dict
            assert isinstance(data["per_100g"], dict), "per_100g should be a dict"
            
            # enrichment should be dict or None
            if "enrichment" in data:
                assert isinstance(data["enrichment"], dict), \
                    "enrichment should be a dict"
