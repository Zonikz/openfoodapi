"""Food-101 classifier using PyTorch"""
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import time
from pathlib import Path
import logging
from typing import List, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

# Food-101 class names
FOOD101_CLASSES = [
    "apple_pie", "baby_back_ribs", "baklava", "beef_carpaccio", "beef_tartare",
    "beet_salad", "beignets", "bibimbap", "bread_pudding", "breakfast_burrito",
    "bruschetta", "caesar_salad", "cannoli", "caprese_salad", "carrot_cake",
    "ceviche", "cheese_plate", "cheesecake", "chicken_curry", "chicken_quesadilla",
    "chicken_wings", "chocolate_cake", "chocolate_mousse", "churros", "clam_chowder",
    "club_sandwich", "crab_cakes", "creme_brulee", "croque_madame", "cup_cakes",
    "deviled_eggs", "donuts", "dumplings", "edamame", "eggs_benedict",
    "escargots", "falafel", "filet_mignon", "fish_and_chips", "foie_gras",
    "french_fries", "french_onion_soup", "french_toast", "fried_calamari", "fried_rice",
    "frozen_yogurt", "garlic_bread", "gnocchi", "greek_salad", "grilled_cheese_sandwich",
    "grilled_salmon", "guacamole", "gyoza", "hamburger", "hot_and_sour_soup",
    "hot_dog", "huevos_rancheros", "hummus", "ice_cream", "lasagna",
    "lobster_bisque", "lobster_roll_sandwich", "macaroni_and_cheese", "macarons", "miso_soup",
    "mussels", "nachos", "omelette", "onion_rings", "oysters",
    "pad_thai", "paella", "pancakes", "panna_cotta", "peking_duck",
    "pho", "pizza", "pork_chop", "poutine", "prime_rib",
    "pulled_pork_sandwich", "ramen", "ravioli", "red_velvet_cake", "risotto",
    "samosa", "sashimi", "scallops", "seaweed_salad", "shrimp_and_grits",
    "spaghetti_bolognese", "spaghetti_carbonara", "spring_rolls", "steak", "strawberry_shortcake",
    "sushi", "tacos", "takoyaki", "tiramisu", "tuna_tartare",
    "waffles"
]


class FoodClassifier:
    """Food-101 classifier"""
    
    def __init__(self):
        self.device = torch.device("cuda" if settings.USE_GPU and torch.cuda.is_available() else "cpu")
        self.model = None
        self.ready = False
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info(f"🧠 Classifier device: {self.device}")
    
    async def load(self) -> None:
        """Load model weights"""
        try:
            model_path = Path(settings.MODEL_PATH)
            
            # Create ResNet-50 architecture
            self.model = models.resnet50(weights=None)
            num_classes = len(FOOD101_CLASSES)
            self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)
            
            # Load weights if available
            if model_path.exists():
                logger.info(f"📦 Loading weights from {model_path}")
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
            else:
                logger.warning(f"⚠️  Model weights not found at {model_path}")
                logger.warning("⚠️  Using untrained model. Run: python tools/download_model.py")
                # Continue with untrained model for testing
            
            self.model.to(self.device)
            self.model.eval()
            
            # Set thread count for CPU
            if self.device.type == "cpu":
                torch.set_num_threads(settings.TORCH_NUM_THREADS)
            
            self.ready = True
            logger.info("✅ Classifier ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to load classifier: {e}")
            raise
    
    async def predict(
        self,
        image: Image.Image,
        top_k: int = 5
    ) -> Tuple[List[str], List[float], int]:
        """
        Predict food class
        
        Args:
            image: PIL Image
            top_k: Number of top predictions
        
        Returns:
            (labels, scores, inference_ms)
        """
        if not self.ready:
            raise RuntimeError("Model not loaded")
        
        start = time.time()
        
        try:
            # Preprocess
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize if too large
            if max(image.size) > settings.MAX_IMAGE_SIZE:
                image.thumbnail((settings.MAX_IMAGE_SIZE, settings.MAX_IMAGE_SIZE))
            
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
            
            # Get top-k
            top_probs, top_indices = torch.topk(probabilities, top_k)
            
            labels = [FOOD101_CLASSES[idx] for idx in top_indices[0].cpu().numpy()]
            scores = top_probs[0].cpu().numpy().tolist()
            
            inference_ms = int((time.time() - start) * 1000)
            
            return labels, scores, inference_ms
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
