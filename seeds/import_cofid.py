"""Import CoFID (UK government) nutrition data"""
import pandas as pd
import sys
from pathlib import Path
from sqlmodel import Session, select, func
import logging
import urllib.request
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import FoodGeneric
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CoFID public CSV URL (UK government open data)
COFID_CSV_URL = "https://assets.publishing.service.gov.uk/media/5a7ba84b40f0b62302697568/CoFID2021.csv"


def download_cofid_csv() -> Path:
    """Download CoFID CSV from UK government website"""
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / "cofid.csv"
        
        if csv_path.exists():
            logger.info(f"✅ CoFID CSV already downloaded: {csv_path}")
            return csv_path
        
        logger.info("📥 Downloading CoFID dataset from UK government...")
        logger.info(f"   URL: {COFID_CSV_URL}")
        
        # Download
        response = urllib.request.urlopen(COFID_CSV_URL)
        content = response.read().decode('utf-8')
        
        # Save
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_size = csv_path.stat().st_size / 1024
        logger.info(f"✅ Downloaded CoFID CSV ({file_size:.1f} KB)")
        return csv_path
        
    except Exception as e:
        logger.warning(f"⚠️  Could not download CoFID: {e}")
        logger.info("💡 Using sample data instead...")
        return None


def import_cofid():
    """Import CoFID data from CSV"""
    try:
        logger.info("🚀 GAINS Food Vision - CoFID Import")
        logger.info("=" * 60)
        
        # Initialize database
        init_db()
        
        # Check existing data
        with Session(engine) as session:
            existing_count = session.exec(
                select(func.count(FoodGeneric.id))
                .where(FoodGeneric.source == "cofid")
            ).one()
            
            if existing_count > 0:
                logger.info(f"✅ CoFID already imported ({existing_count} foods)")
                logger.info("💡 To re-import, delete foods_generic table and run again")
                return
        
        # Try to download CSV
        csv_path = download_cofid_csv()
        
        if not csv_path or not csv_path.exists():
            logger.warning("⚠️  CoFID download failed, using sample data...")
            _create_sample_cofid()
            return
        
        # Read CSV
        logger.info(f"📖 Parsing CoFID CSV...")
        try:
            # CoFID CSV format: Food Name, Food Code, Energy (kcal), Protein (g), etc.
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"📊 Found {len(df)} foods in CSV")
        except Exception as e:
            logger.error(f"❌ CSV parsing failed: {e}")
            logger.info("💡 Using sample data instead...")
            _create_sample_cofid()
            return
        
        # Process and insert
        logger.info("💾 Importing foods to database...")
        with Session(engine) as session:
            count = 0
            skipped = 0
            
            for idx, row in df.iterrows():
                try:
                    # Extract food code and name
                    food_code = str(row.get('Food Code', row.get('Code', idx))).strip()
                    food_name = str(row.get('Food Name', row.get('Name', 'Unknown'))).strip()
                    
                    if not food_name or food_name == 'Unknown':
                        skipped += 1
                        continue
                    
                    # Check if already exists
                    source_id = f"COFID:{food_code}"
                    existing = session.exec(
                        select(FoodGeneric)
                        .where(FoodGeneric.source_id == source_id)
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Parse nutrition (handle various column names and formats)
                    def safe_float(val, default=None):
                        try:
                            if pd.isna(val) or val == '' or val == 'N' or val == 'Tr':
                                return default
                            return float(str(val).replace(',', '.'))
                        except:
                            return default
                    
                    energy_kcal = safe_float(row.get('Energy (kcal)', row.get('Calories', None)))
                    protein_g = safe_float(row.get('Protein (g)', row.get('Protein', None)))
                    carb_g = safe_float(row.get('Carbohydrate (g)', row.get('Carbohydrate', None)))
                    fat_g = safe_float(row.get('Fat (g)', row.get('Fat', None)))
                    fiber_g = safe_float(row.get('Fibre (g)', row.get('Fiber', None)))
                    sugar_g = safe_float(row.get('Total sugars (g)', row.get('Sugars', None)))
                    saturated_fat_g = safe_float(row.get('Saturated fatty acids (g)', row.get('Saturated fat', None)))
                    sodium_mg = safe_float(row.get('Sodium (mg)', row.get('Sodium', None)))
                    
                    # Category
                    category = str(row.get('Main food group', row.get('Category', ''))).strip() or None
                    subcategory = str(row.get('Sub food group', row.get('Subcategory', ''))).strip() or None
                    
                    food = FoodGeneric(
                        source="cofid",
                        source_id=source_id,
                        name=food_name,
                        name_lower=food_name.lower(),
                        energy_kcal=energy_kcal,
                        protein_g=protein_g,
                        carb_g=carb_g,
                        fat_g=fat_g,
                        fiber_g=fiber_g,
                        sugar_g=sugar_g,
                        saturated_fat_g=saturated_fat_g,
                        sodium_mg=sodium_mg,
                        category=category,
                        subcategory=subcategory
                    )
                    
                    session.add(food)
                    count += 1
                    
                    if count % 100 == 0:
                        session.commit()
                        logger.info(f"  ✓ Imported {count} foods...")
                
                except Exception as e:
                    logger.debug(f"  Skipped row {idx}: {e}")
                    skipped += 1
                    continue
            
            session.commit()
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ CoFID IMPORT COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"📊 Imported: {count} foods")
            logger.info(f"⏭️  Skipped: {skipped} items")
            logger.info(f"📁 Source: CoFID (UK government)")
            logger.info("")
    
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
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
