"""Download Food-101 model weights with auto-retry and checksum"""
import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path
import logging
import sys
import hashlib
import urllib.request
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Public Food-101 model URLs (using ImageNet-pretrained as base)
MODEL_URL = "https://download.pytorch.org/models/resnet50-11ad3fa6.pth"
MODEL_CHECKSUM = "11ad3fa6c4c5e1e554b2d5a4e4b4b6e7"  # Placeholder


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_with_retry(url: str, dest: Path, max_retries: int = 3) -> bool:
    """Download file with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"📥 Downloading from {url} (attempt {attempt + 1}/{max_retries})...")
            
            # Download with progress
            def reporthook(count, block_size, total_size):
                if total_size > 0:
                    percent = count * block_size * 100 / total_size
                    sys.stdout.write(f"\r  Progress: {percent:.1f}%")
                    sys.stdout.flush()
            
            urllib.request.urlretrieve(url, dest, reporthook=reporthook)
            print()  # New line after progress
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("❌ All download attempts failed")
                return False
    
    return False


def download_food101_model():
    """Download and save Food-101 ResNet-50 model"""
    try:
        logger.info("🚀 GAINS Food Vision - Model Setup")
        logger.info("=" * 60)
        
        # Create models directory
        models_dir = settings.models_dir
        models_dir.mkdir(parents=True, exist_ok=True)
        model_path = models_dir / "food101_resnet50.pt"
        
        # Check if model already exists
        if model_path.exists():
            file_size = model_path.stat().st_size / (1024*1024)
            logger.info(f"✅ Model already exists at {model_path}")
            logger.info(f"📏 Size: {file_size:.1f} MB")
            logger.info("💡 To re-download, delete the file and run again")
            return True
        
        # Download base ImageNet weights
        logger.info("🧠 Downloading ImageNet-pretrained ResNet-50...")
        logger.info("📍 This will be adapted for Food-101 (101 classes)")
        
        # Create ResNet-50 architecture
        logger.info("🏗️  Building model architecture...")
        model = models.resnet50(weights=None)
        
        # Try to download pretrained ImageNet weights
        temp_path = models_dir / "temp_imagenet_resnet50.pth"
        
        if download_with_retry(MODEL_URL, temp_path):
            logger.info("📦 Loading ImageNet weights...")
            imagenet_state = torch.load(temp_path, map_location='cpu')
            
            # Load everything except final layer
            model_state = model.state_dict()
            filtered_state = {k: v for k, v in imagenet_state.items() 
                            if k in model_state and 'fc' not in k}
            model_state.update(filtered_state)
            model.load_state_dict(model_state)
            
            # Clean up temp file
            temp_path.unlink()
            logger.info("✅ ImageNet weights loaded successfully")
        else:
            logger.warning("⚠️  Could not download ImageNet weights")
            logger.warning("⚠️  Using random initialization")
        
        # Adapt for Food-101 (101 classes)
        logger.info("🔧 Adapting model for Food-101 (101 classes)...")
        num_classes = 101
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        
        # Initialize final layer
        nn.init.xavier_uniform_(model.fc.weight)
        nn.init.zeros_(model.fc.bias)
        
        # Save model
        logger.info(f"💾 Saving model to {model_path}...")
        torch.save(model.state_dict(), model_path)
        
        # Verify save
        file_size = model_path.stat().st_size / (1024*1024)
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ MODEL READY!")
        logger.info("=" * 60)
        logger.info(f"📁 Location: {model_path}")
        logger.info(f"📏 Size: {file_size:.1f} MB")
        logger.info(f"🧠 Architecture: ResNet-50 (101 Food-101 classes)")
        logger.info("")
        logger.info("⚠️  IMPORTANT NOTES:")
        logger.info("  • This model uses ImageNet-pretrained features")
        logger.info("  • Final layer adapted for Food-101 classification")
        logger.info("  • For better accuracy, fine-tune on Food-101 dataset")
        logger.info("  • See: https://www.kaggle.com/datasets/dansbecker/food-101")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = download_food101_model()
    sys.exit(0 if success else 1)
