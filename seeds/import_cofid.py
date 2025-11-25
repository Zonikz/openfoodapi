"""Import CoFID (UK government) nutrition data"""
import pandas as pd
import sys
from pathlib import Path
from sqlmodel import Session, select
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import FoodGeneric
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_cofid():
    """Import CoFID data from CSV"""
    try:
        logger.info("📦 Importing CoFID data...")
        
        # Initialize database
        init_db()
        
        # Check if CSV exists
        csv_path = Path(settings.COFID_CSV_PATH)
        
        if not csv_path.exists():
            logger.warning(f"⚠️  CoFID CSV not found at {csv_path}")
            logger.info("📥 Creating sample CoFID data...")
            _create_sample_cofid()
            return
        
        # Read CSV
        logger.info(f"📖 Reading {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Process and insert
        with Session(engine) as session:
            count = 0
            
            for _, row in df.iterrows():
                # Check if already exists
                existing = session.exec(
                    select(FoodGeneric)
                    .where(FoodGeneric.source_id == f"COFID:{row['code']}")
                ).first()
                
                if existing:
                    continue
                
                food = FoodGeneric(
                    source="cofid",
                    source_id=f"COFID:{row['code']}",
                    name=row['name'],
                    name_lower=row['name'].lower(),
                    energy_kcal=row.get('energy_kcal'),
                    protein_g=row.get('protein_g'),
                    carb_g=row.get('carb_g'),
                    fat_g=row.get('fat_g'),
                    fiber_g=row.get('fiber_g'),
                    sugar_g=row.get('sugar_g'),
                    saturated_fat_g=row.get('saturated_fat_g'),
                    sodium_mg=row.get('sodium_mg'),
                    category=row.get('category'),
                    subcategory=row.get('subcategory')
                )
                
                session.add(food)
                count += 1
                
                if count % 100 == 0:
                    logger.info(f"  Processed {count} foods...")
            
            session.commit()
            logger.info(f"✅ Imported {count} CoFID foods")
    
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise


def _create_sample_cofid():
    """Create sample CoFID data for testing"""
    sample_foods = [
        {
            "code": "1001", "name": "Chicken curry", "category": "Meat dishes",
            "energy_kcal": 148, "protein_g": 16.5, "carb_g": 5.8, "fat_g": 6.1,
            "fiber_g": 1.2, "sugar_g": 2.1, "saturated_fat_g": 1.8, "sodium_mg": 380
        },
        {
            "code": "1002", "name": "Pizza, cheese and tomato", "category": "Cereals",
            "energy_kcal": 271, "protein_g": 11.2, "carb_g": 31.4, "fat_g": 10.5,
            "fiber_g": 2.1, "sugar_g": 2.8, "saturated_fat_g": 4.8, "sodium_mg": 598
        },
        {
            "code": "1003", "name": "Sushi, mixed", "category": "Fish",
            "energy_kcal": 143, "protein_g": 6.4, "carb_g": 24.1, "fat_g": 1.8,
            "fiber_g": 0.5, "sugar_g": 3.2, "saturated_fat_g": 0.4, "sodium_mg": 428
        },
        {
            "code": "1004", "name": "Hamburger, beef patty", "category": "Meat",
            "energy_kcal": 295, "protein_g": 17.2, "carb_g": 24.3, "fat_g": 13.8,
            "fiber_g": 1.5, "sugar_g": 3.1, "saturated_fat_g": 5.2, "sodium_mg": 512
        },
        {
            "code": "1005", "name": "Ice cream, vanilla", "category": "Dairy",
            "energy_kcal": 207, "protein_g": 3.5, "carb_g": 23.6, "fat_g": 11.0,
            "fiber_g": 0.0, "sugar_g": 21.2, "saturated_fat_g": 6.8, "sodium_mg": 80
        },
        {
            "code": "1006", "name": "Apple pie", "category": "Desserts",
            "energy_kcal": 237, "protein_g": 2.1, "carb_g": 34.2, "fat_g": 10.6,
            "fiber_g": 1.6, "sugar_g": 16.4, "saturated_fat_g": 4.5, "sodium_mg": 252
        }
    ]
    
    with Session(engine) as session:
        for food_data in sample_foods:
            food = FoodGeneric(
                source="cofid",
                source_id=f"COFID:{food_data['code']}",
                name=food_data['name'],
                name_lower=food_data['name'].lower(),
                energy_kcal=food_data['energy_kcal'],
                protein_g=food_data['protein_g'],
                carb_g=food_data['carb_g'],
                fat_g=food_data['fat_g'],
                fiber_g=food_data['fiber_g'],
                sugar_g=food_data['sugar_g'],
                saturated_fat_g=food_data['saturated_fat_g'],
                sodium_mg=food_data['sodium_mg'],
                category=food_data['category']
            )
            session.add(food)
        
        session.commit()
        logger.info(f"✅ Created {len(sample_foods)} sample CoFID foods")


if __name__ == "__main__":
    import_cofid()
