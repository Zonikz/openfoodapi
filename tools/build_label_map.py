"""Build label map from Food-101 to canonical foods"""
import json
import sys
from pathlib import Path
from sqlmodel import Session, select
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import LabelMapping, FoodGeneric, FoodOFF
from app.data.search import find_canonical_food
from app.config import settings
from app.models.vision_classifier import FOOD101_CLASSES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_label_map():
    """Build label map from Food-101 classes to canonical foods"""
    try:
        logger.info("🔨 Building label map...")
        
        # Initialize database
        init_db()
        
        label_map = {}
        
        with Session(engine) as session:
            for food101_label in FOOD101_CLASSES:
                # Convert underscore to space
                query = food101_label.replace("_", " ")
                
                # Find canonical food
                result = find_canonical_food(session, query)
                
                if result:
                    label_map[food101_label] = {
                        "source": result["source"],
                        "id": result["source_id"]
                    }
                    
                    # Insert into database
                    existing = session.exec(
                        select(LabelMapping)
                        .where(LabelMapping.food101_label == food101_label)
                    ).first()
                    
                    if not existing:
                        mapping = LabelMapping(
                            food101_label=food101_label,
                            canonical_source=result["source"],
                            canonical_id=result["source_id"],
                            confidence=1.0
                        )
                        session.add(mapping)
                    
                    logger.info(f"  ✓ {food101_label} → {result['name']}")
                else:
                    logger.warning(f"  ✗ {food101_label} → NOT FOUND")
            
            session.commit()
        
        # Save to JSON
        json_path = settings.label_map_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w') as f:
            json.dump(label_map, f, indent=2)
        
        logger.info(f"✅ Label map saved to {json_path}")
        logger.info(f"📊 Mapped {len(label_map)}/{len(FOOD101_CLASSES)} labels")
    
    except Exception as e:
        logger.error(f"❌ Build failed: {e}")
        raise


if __name__ == "__main__":
    build_label_map()
