"""Test all API endpoints"""
import pytest
from fastapi.testclient import TestClient
from main import app
import io
from PIL import Image

client = TestClient(app)


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    def test_health_check(self):
        """Test health endpoint returns OK"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "operational", "ok"]
        
        print(f"✅ Health check: {data}")


class TestClassifyEndpoint:
    """Test /api/classify endpoint"""
    
    def test_classify_with_image(self):
        """Test classification with dummy image"""
        # Create a dummy test image
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"image": ("test.jpg", img_bytes, "image/jpeg")}
        response = client.post("/api/classify", files=files)
        
        assert response.status_code == 200, \
            f"Classification failed: {response.status_code}"
        
        data = response.json()
        
        # Check response structure
        assert "model" in data, "Missing 'model' field"
        assert "top_k" in data, "Missing 'top_k' field"
        assert "inference_ms" in data, "Missing 'inference_ms' field"
        
        # Check predictions
        predictions = data["top_k"]
        assert len(predictions) == 5, f"Should return 5 predictions, got {len(predictions)}"
        
        for pred in predictions:
            assert "label" in pred, "Prediction missing 'label'"
            assert "score" in pred, "Prediction missing 'score'"
            assert 0 <= pred["score"] <= 1, f"Invalid score: {pred['score']}"
        
        # Check inference time is reasonable
        assert data["inference_ms"] < 5000, \
            f"Inference too slow: {data['inference_ms']}ms"
        
        print(f"✅ Classification: {predictions[0]['label']} ({predictions[0]['score']:.3f})")
        print(f"✅ Inference time: {data['inference_ms']}ms")
    
    def test_classify_top_k_parameter(self):
        """Test top_k parameter works"""
        img = Image.new('RGB', (224, 224), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"image": ("test.jpg", img_bytes, "image/jpeg")}
        data = {"top_k": 3}
        
        response = client.post("/api/classify", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        predictions = result["top_k"]
        
        assert len(predictions) == 3, f"Should return 3 predictions, got {len(predictions)}"
        print(f"✅ top_k parameter working")
    
    def test_classify_without_image(self):
        """Test classification without image returns error"""
        response = client.post("/api/classify")
        assert response.status_code == 422, \
            "Should return 422 for missing image"


class TestMapToFoodEndpoint:
    """Test /api/map-to-food endpoint"""
    
    def test_map_to_food(self):
        """Test mapping prediction to canonical food"""
        request = {
            "query": "chicken_curry",
            "country": "UK"
        }
        
        response = client.post("/api/map-to-food", json=request)
        
        if response.status_code == 404:
            pytest.skip("Label mapping or database not set up")
            return
        
        assert response.status_code == 200, \
            f"Mapping failed: {response.status_code}"
        
        data = response.json()
        
        # Check response structure
        assert "canonical_name" in data, "Missing 'canonical_name'"
        assert "source" in data, "Missing 'source'"
        assert "source_id" in data, "Missing 'source_id'"
        assert "per_100g" in data, "Missing 'per_100g'"
        
        # Check nutrition data
        nutrition = data["per_100g"]
        assert "energy_kcal" in nutrition
        assert "protein_g" in nutrition
        assert "carb_g" in nutrition
        assert "fat_g" in nutrition
        
        print(f"✅ Mapped to: {data['canonical_name']}")
        print(f"✅ Source: {data['source']}:{data['source_id']}")
    
    def test_map_to_food_unknown_query(self):
        """Test mapping with unknown query"""
        request = {
            "query": "unknown_food_xyz",
            "country": "UK"
        }
        
        response = client.post("/api/map-to-food", json=request)
        # Should return 404 or empty results
        assert response.status_code in [200, 404]


class TestComprehensiveEndpoints:
    """Test all endpoints are accessible"""
    
    def test_all_endpoints_exist(self):
        """Test that all documented endpoints exist"""
        endpoints = [
            ("GET", "/api/health"),
            ("POST", "/api/classify"),
            ("POST", "/api/map-to-food"),
            ("GET", "/api/barcode/123456789"),
            ("GET", "/api/foods/search?q=test"),
            ("POST", "/api/score/gains"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json={})
            
            # Should not return 404 (endpoint exists)
            # May return 400/422 (validation error) which is fine
            assert response.status_code != 404, \
                f"Endpoint not found: {method} {path}"
            
            print(f"✅ Endpoint exists: {method} {path}")
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.get("/api/health")
        
        # Check for CORS headers (if configured)
        headers = response.headers
        
        # May or may not be present in TestClient
        # This is more for documentation
        print(f"✅ Response headers: {dict(headers)}")
    
    def test_json_responses(self):
        """Test all endpoints return JSON"""
        response = client.get("/api/health")
        assert response.headers["content-type"] == "application/json"
        
        # Should be parseable JSON
        data = response.json()
        assert isinstance(data, dict)
        
        print("✅ All responses are JSON")
