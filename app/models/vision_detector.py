"""YOLOv8 food detector (optional)"""
from ultralytics import YOLO
from PIL import Image
import time
from pathlib import Path
import logging
from typing import List, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class FoodDetector:
    """YOLOv8 food detector for bounding boxes"""
    
    def __init__(self):
        self.model = None
        self.ready = False
    
    async def load(self) -> None:
        """Load YOLOv8 model"""
        try:
            model_path = Path(settings.models_dir) / settings.DETECTOR_MODEL
            
            if model_path.exists():
                logger.info(f"📦 Loading YOLOv8 from {model_path}")
                self.model = YOLO(str(model_path))
            else:
                logger.info(f"📥 Downloading YOLOv8 {settings.DETECTOR_MODEL}")
                self.model = YOLO(settings.DETECTOR_MODEL)  # Auto-download
            
            self.ready = True
            logger.info("✅ Detector ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to load detector: {e}")
            raise
    
    async def detect(
        self,
        image: Image.Image,
        conf_threshold: float = 0.25
    ) -> Tuple[List[dict], int]:
        """
        Detect food objects with bounding boxes
        
        Args:
            image: PIL Image
            conf_threshold: Confidence threshold
        
        Returns:
            (detections, inference_ms)
        """
        if not self.ready:
            raise RuntimeError("Detector not loaded")
        
        start = time.time()
        
        try:
            # Run detection
            results = self.model(image, conf=conf_threshold, verbose=False)
            
            detections = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = result.names[cls]
                    
                    detections.append({
                        "label": label,
                        "score": conf,
                        "box": [x1, y1, x2, y2]
                    })
            
            inference_ms = int((time.time() - start) * 1000)
            
            return detections, inference_ms
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            raise
