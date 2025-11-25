"""Import OpenFoodFacts data"""
import pandas as pd
import sys
from pathlib import Path
from sqlmodel import Session, select
import logging
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import FoodOFF
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_off():
    """Import OpenFoodFacts data from CSV dump"""
    try:
        logger.info("📦 Importing OpenFoodFacts data...")
        
        # Initialize database
        init_db()
        
        # Check if CSV exists
        csv_path = Path(settings.OFF_DUMP_PATH)
        
        if not csv_path.exists():
            logger.warning(f"⚠️  OFF CSV not found at {csv_path}")
            logger.info("📥 Creating sample OFF data...")
            _create_sample_off()
            return
        
        # Read CSV (subset for performance)
        logger.info(f"📖 Reading {csv_path}...")
        logger.info("⏳ This may take a while for large dumps...")
        
        # Read in chunks to avoid memory issues
        chunk_size = 10000
        total_imported = 0
        
        with Session(engine) as session:
            for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
                count = 0
                
                for _, row in chunk.iterrows():
                    # Skip if no barcode
                    if pd.isna(row.get('code')):
                        continue
                    
                    code = str(row['code']).strip()
                    
                    # Check if already exists
                    existing = session.exec(
                        select(FoodOFF).where(FoodOFF.code == code)
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Parse additives
                    additives = None
                    if not pd.isna(row.get('additives_tags')):
                        additives = json.dumps(str(row['additives_tags']).split(','))
                    
                    food = FoodOFF(
                        code=code,
                        product_name=row.get('product_name', 'Unknown'),
                        product_name_lower=str(row.get('product_name', 'unknown')).lower(),
                        energy_kcal=row.get('energy-kcal_100g'),
                        protein_g=row.get('proteins_100g'),
                        carb_g=row.get('carbohydrates_100g'),
                        fat_g=row.get('fat_100g'),
                        fiber_g=row.get('fiber_100g'),
                        sugar_g=row.get('sugars_100g'),
                        saturated_fat_g=row.get('saturated-fat_100g'),
                        sodium_mg=row.get('sodium_100g') * 1000 if not pd.isna(row.get('sodium_100g')) else None,
                        nova_group=int(row['nova_group']) if not pd.isna(row.get('nova_group')) else None,
                        nutriscore_grade=row.get('nutriscore_grade'),
                        additives=additives,
                        categories=row.get('categories'),
                        brands=row.get('brands'),
                        countries=row.get('countries')
                    )
                    
                    session.add(food)
                    count += 1
                
                session.commit()
                total_imported += count
                logger.info(f"  Imported {total_imported} products...")
        
        logger.info(f"✅ Imported {total_imported} OFF products")
    
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise


def _create_sample_off():
    """Create sample OFF data for testing"""
    sample_products = [
        {
            "code": "5000159407236",
            "product_name": "Chicken Tikka Masala",
            "brands": "Tesco",
            "countries": "United Kingdom",
            "energy_kcal": 125,
            "protein_g": 9.2,
            "carb_g": 8.5,
            "fat_g": 6.3,
            "fiber_g": 1.1,
            "sugar_g": 3.2,
            "saturated_fat_g": 2.8,
            "sodium_mg": 420,
            "nova_group": 3,
            "nutriscore_grade": "C",
            "additives": json.dumps(["E412", "E415"])
        },
        {
            "code": "3017620422003",
            "product_name": "Nutella",
            "brands": "Ferrero",
            "countries": "France, United Kingdom",
            "energy_kcal": 539,
            "protein_g": 6.3,
            "carb_g": 57.5,
            "fat_g": 30.9,
            "fiber_g": 0.0,
            "sugar_g": 56.3,
            "saturated_fat_g": 10.6,
            "sodium_mg": 40,
            "nova_group": 4,
            "nutriscore_grade": "E",
            "additives": json.dumps(["E322", "E476"])
        }
    ]
    
    with Session(engine) as session:
        for prod_data in sample_products:
            product = FoodOFF(
                code=prod_data['code'],
                product_name=prod_data['product_name'],
                product_name_lower=prod_data['product_name'].lower(),
                energy_kcal=prod_data['energy_kcal'],
                protein_g=prod_data['protein_g'],
                carb_g=prod_data['carb_g'],
                fat_g=prod_data['fat_g'],
                fiber_g=prod_data['fiber_g'],
                sugar_g=prod_data['sugar_g'],
                saturated_fat_g=prod_data['saturated_fat_g'],
                sodium_mg=prod_data['sodium_mg'],
                nova_group=prod_data['nova_group'],
                nutriscore_grade=prod_data['nutriscore_grade'],
                additives=prod_data['additives'],
                brands=prod_data['brands'],
                countries=prod_data['countries']
            )
            session.add(product)
        
        session.commit()
        logger.info(f"✅ Created {len(sample_products)} sample OFF products")


if __name__ == "__main__":
    import_off()
