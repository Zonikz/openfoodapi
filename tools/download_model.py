"""Download Food-101 model weights"""
import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path
import logging
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_food101_model():
    """Download and save Food-101 ResNet-50 model"""
    try:
        logger.info("📥 Downloading Food-101 ResNet-50 model...")
        
        # Create models directory
        models_dir = settings.models_dir
        model_path = models_dir / "food101_resnet50.pt"
        
        if model_path.exists():
            logger.info(f"✅ Model already exists at {model_path}")
            return
        
        # Load pretrained Food-101 model
        # Note: This is a placeholder. In production, you would:
        # 1. Train on Food-101 dataset, or
        # 2. Download from a model hub (HuggingFace, TorchHub, etc.)
        
        logger.info("🧠 Creating ResNet-50 architecture...")
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        
        # Modify for Food-101 (101 classes)
        num_classes = 101
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        
        # In production, load trained weights here:
        # state_dict = torch.hub.load_state_dict_from_url(
        #     "https://your-model-hub.com/food101_resnet50.pt"
        # )
        # model.load_state_dict(state_dict)
        
        logger.info(f"💾 Saving model to {model_path}...")
        torch.save(model.state_dict(), model_path)
        
        logger.info("✅ Model downloaded successfully!")
        logger.info(f"📁 Location: {model_path}")
        logger.info(f"📏 Size: {model_path.stat().st_size / (1024*1024):.1f} MB")
        
        logger.warning("")
        logger.warning("⚠️  IMPORTANT: This is an untrained model!")
        logger.warning("⚠️  For production use, train on Food-101 or download trained weights.")
        logger.warning("⚠️  See: https://www.kaggle.com/datasets/dansbecker/food-101")
        
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        raise


if __name__ == "__main__":
    download_food101_model()
