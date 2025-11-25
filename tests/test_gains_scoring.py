"""Test GAINS scoring endpoint"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestGAINSScoring:
    """Test /api/score/gains endpoint"""
    
    def test_gains_scoring_cofid(self):
        """Test GAINS scoring with CoFID food"""
        # Use sample CoFID food from import_cofid.py
        request = {
            "canonical_id": "COFID:1001",  # Chicken curry
            "grams": 200
        }
        
        response = client.post("/api/score/gains", json=request)
        
        if response.status_code == 404:
            pytest.skip("CoFID data not imported yet")
            return
        
        assert response.status_code == 200, \
            f"GAINS scoring failed: {response.status_code}"
        
        data = response.json()
        
        # Check response structure
        assert "macros" in data, "Missing 'macros'"
        assert "score" in data, "Missing 'score'"
        assert "grade" in data, "Missing 'grade'"
        
        # Validate macros
        macros = data["macros"]
        assert "energy_kcal" in macros, "Missing energy_kcal"
        assert "protein_g" in macros, "Missing protein_g"
        assert "carb_g" in macros, "Missing carb_g"
        assert "fat_g" in macros, "Missing fat_g"
        
        # Check macros are scaled correctly for portion
        assert macros["energy_kcal"] > 0, "Energy should be positive"
        assert macros["protein_g"] >= 0, "Protein should be non-negative"
        
        print(f"✅ Macros for 200g: {macros}")
        
        # Validate score components
        score = data["score"]
        components = [
            "protein_density",
            "carb_quality",
            "fat_quality",
            "processing",
            "transparency",
            "overall"
        ]
        
        for component in components:
            assert component in score, f"Missing score component: {component}"
            value = score[component]
            
            assert isinstance(value, (int, float)), \
                f"{component} should be numeric, got {type(value)}"
            
            assert 0 <= value <= 1, \
                f"{component} should be 0-1, got {value}"
            
            assert value == value, f"{component} is NaN"  # Check not NaN
        
        print(f"✅ Score components: {score}")
        
        # Validate grade
        grade = data["grade"]
        assert grade in ["A", "B", "C", "D", "E", "F"], \
            f"Invalid grade: {grade}"
        
        print(f"✅ GAINS grade: {grade}")
    
    def test_gains_scoring_portion_scaling(self):
        """Test that macros scale correctly with portion size"""
        request_100g = {
            "canonical_id": "COFID:1001",
            "grams": 100
        }
        
        request_200g = {
            "canonical_id": "COFID:1001",
            "grams": 200
        }
        
        response_100 = client.post("/api/score/gains", json=request_100g)
        response_200 = client.post("/api/score/gains", json=request_200g)
        
        if response_100.status_code == 404:
            pytest.skip("CoFID data not imported")
            return
        
        assert response_100.status_code == 200
        assert response_200.status_code == 200
        
        data_100 = response_100.json()
        data_200 = response_200.json()
        
        # Macros should double
        macros_100 = data_100["macros"]
        macros_200 = data_200["macros"]
        
        # Allow 10% tolerance for rounding
        tolerance = 0.1
        
        ratio = macros_200["energy_kcal"] / macros_100["energy_kcal"]
        assert abs(ratio - 2.0) < tolerance, \
            f"Energy should double, got ratio: {ratio}"
        
        ratio = macros_200["protein_g"] / macros_100["protein_g"]
        assert abs(ratio - 2.0) < tolerance, \
            f"Protein should double, got ratio: {ratio}"
        
        # Score components should be identical (per 100g basis)
        score_100 = data_100["score"]
        score_200 = data_200["score"]
        
        assert score_100["protein_density"] == score_200["protein_density"], \
            "Protein density should not change with portion size"
        
        assert score_100["overall"] == score_200["overall"], \
            "Overall score should not change with portion size"
        
        print("✅ Portion scaling works correctly")
    
    def test_gains_scoring_with_enrichment(self):
        """Test GAINS scoring with OFF enrichment data"""
        # Test with barcode (if available)
        request = {
            "canonical_id": "3017620422003",  # Nutella barcode
            "grams": 150
        }
        
        response = client.post("/api/score/gains", json=request)
        
        if response.status_code == 404:
            pytest.skip("OFF data not available")
            return
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have processing score based on NOVA/NutriScore
        score = data["score"]
        
        assert 0 <= score["processing"] <= 1, \
            f"Invalid processing score: {score['processing']}"
        
        print(f"✅ Processing score (with enrichment): {score['processing']}")
        print(f"✅ Grade: {data['grade']}")
    
    def test_gains_invalid_food(self):
        """Test GAINS scoring with invalid food ID"""
        request = {
            "canonical_id": "INVALID:99999",
            "grams": 100
        }
        
        response = client.post("/api/score/gains", json=request)
        assert response.status_code == 404, \
            "Should return 404 for invalid food"
    
    def test_gains_zero_grams(self):
        """Test GAINS scoring with zero grams"""
        request = {
            "canonical_id": "COFID:1001",
            "grams": 0
        }
        
        response = client.post("/api/score/gains", json=request)
        
        if response.status_code == 404:
            pytest.skip("CoFID data not imported")
            return
        
        assert response.status_code == 200
        data = response.json()
        
        # Macros should all be 0
        macros = data["macros"]
        assert macros["energy_kcal"] == 0
        assert macros["protein_g"] == 0
        assert macros["carb_g"] == 0
        assert macros["fat_g"] == 0
        
        print("✅ Zero grams handled correctly")
    
    def test_gains_large_portion(self):
        """Test GAINS scoring with large portion"""
        request = {
            "canonical_id": "COFID:1001",
            "grams": 1000  # 1kg
        }
        
        response = client.post("/api/score/gains", json=request)
        
        if response.status_code == 404:
            pytest.skip("CoFID data not imported")
            return
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle large portions
        macros = data["macros"]
        assert macros["energy_kcal"] > 1000, \
            "1kg should have significant calories"
        
        print(f"✅ Large portion (1kg): {macros['energy_kcal']} kcal")
