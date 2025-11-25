"""Validate Food-101 classifier model"""
import sys
from pathlib import Path
import asyncio
from PIL import Image
import io
import base64

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.vision_classifier import FoodClassifier
from app.config import settings

# Sample base64 test image (1x1 pixel placeholder - in production use real Food-101 samples)
SAMPLE_IMAGES = {
    "chicken_curry": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "pizza": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "hamburger": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
}


async def validate_model():
    """Validate model loading and inference"""
    print("=" * 60)
    print("🧪 VALIDATING FOOD-101 CLASSIFIER MODEL")
    print("=" * 60)
    
    passed = []
    failed = []
    
    # Test 1: Model file exists
    model_path = Path(settings.MODEL_PATH)
    if model_path.exists():
        print(f"✅ Model file exists: {model_path}")
        passed.append("Model file exists")
    else:
        print(f"⚠️  Model file not found: {model_path}")
        print("   Run: python tools/download_model.py")
        failed.append("Model file missing - using untrained weights")
    
    # Test 2: Load model
    try:
        classifier = FoodClassifier()
        await classifier.load()
        print("✅ Model loaded successfully")
        passed.append("Model loads")
    except Exception as e:
        print(f"❌ Model load failed: {e}")
        failed.append(f"Model load error: {e}")
        return passed, failed
    
    # Test 3: Verify model is ready
    if classifier.ready:
        print("✅ Model ready for inference")
        passed.append("Model ready")
    else:
        print("❌ Model not ready")
        failed.append("Model not ready")
        return passed, failed
    
    # Test 4: Run inference on sample images
    print("\n📊 Running inference tests...")
    inference_times = []
    
    for food_name, b64_data in SAMPLE_IMAGES.items():
        try:
            # Decode sample image
            img_data = base64.b64decode(b64_data)
            image = Image.open(io.BytesIO(img_data))
            
            # Run prediction
            labels, scores, inference_ms = await classifier.predict(image, top_k=5)
            inference_times.append(inference_ms)
            
            print(f"\n  {food_name}:")
            print(f"    Top prediction: {labels[0]} ({scores[0]:.3f})")
            print(f"    Inference time: {inference_ms}ms")
            print(f"    Top-5: {', '.join(labels[:5])}")
            
            # Validate outputs
            if len(labels) == 5 and len(scores) == 5:
                passed.append(f"Inference on {food_name}")
            else:
                failed.append(f"Incorrect output shape for {food_name}")
            
            # Check if predictions are valid Food-101 classes
            from app.models.vision_classifier import FOOD101_CLASSES
            if all(label in FOOD101_CLASSES for label in labels):
                passed.append(f"Valid Food-101 classes for {food_name}")
            else:
                failed.append(f"Invalid classes returned for {food_name}")
            
        except Exception as e:
            print(f"  ❌ Inference failed for {food_name}: {e}")
            failed.append(f"Inference error on {food_name}: {e}")
    
    # Test 5: Check inference latency
    if inference_times:
        avg_latency = sum(inference_times) / len(inference_times)
        print(f"\n📈 Average inference latency: {avg_latency:.1f}ms")
        
        if avg_latency < 500:  # Should be fast on CPU
            print("✅ Inference latency acceptable")
            passed.append(f"Inference latency: {avg_latency:.1f}ms")
        else:
            print(f"⚠️  Inference latency high: {avg_latency:.1f}ms")
            failed.append(f"High latency: {avg_latency:.1f}ms")
    
    return passed, failed


async def main():
    passed, failed = await validate_model()
    
    print("\n" + "=" * 60)
    print("📋 MODEL VALIDATION SUMMARY")
    print("=" * 60)
    print(f"\n✅ PASSED: {len(passed)}")
    for item in passed:
        print(f"  • {item}")
    
    if failed:
        print(f"\n❌ FAILED: {len(failed)}")
        for item in failed:
            print(f"  • {item}")
        print("\n⚠️  RESULT: FAIL")
        sys.exit(1)
    else:
        print("\n✅ RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
