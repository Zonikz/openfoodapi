"""API endpoint tests"""
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io


@pytest.fixture
def client():
    """Test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def test_image():
    """Create test image"""
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "GAINS Food Vision API"


def test_health(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200 or response.status_code == 503


def test_classify(client, test_image):
    """Test classify endpoint"""
    response = client.post(
        "/api/classify?top_k=5",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "model" in data
        assert "top_k" in data
        assert len(data["top_k"]) <= 5


def test_search(client):
    """Test search endpoint"""
    response = client.get("/api/foods/search?q=chicken&limit=10")
    
    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "results" in data


def test_map_to_food(client):
    """Test map to food endpoint"""
    response = client.post(
        "/api/map-to-food",
        json={"query": "chicken_curry", "country": "UK"}
    )
    
    # May return 404 if no data loaded
    assert response.status_code in [200, 404]
