"""Import OpenFoodFacts (OFF) data - UK subset"""
import json
import sys
from pathlib import Path
from sqlmodel import Session, select, func
import logging
import urllib.request
import gzip
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import FoodOFF
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OFF UK products JSON (smaller subset)
OFF_UK_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.jsonl.gz"
MAX_PRODUCTS = 15000  # Limit for reasonable import time


def download_off_data() -> Path:
    """Download OFF data dump"""
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        gz_path = data_dir / "off_en.jsonl.gz"
        jsonl_path = data_dir / "off_en.jsonl"
        
        if jsonl_path.exists():
            logger.info(f"✅ OFF data already downloaded: {jsonl_path}")
            return jsonl_path
        
        if not gz_path.exists():
            logger.info("📥 Downloading OpenFoodFacts dataset...")
            logger.info(f"   URL: {OFF_UK_URL}")
            logger.info("   ⏳ This may take a few minutes (large file)...")
            
            # Download with progress
            def reporthook(count, block_size, total_size):
                if total_size > 0:
                    percent = count * block_size * 100 / total_size
                    sys.stdout.write(f"\r  Progress: {percent:.1f}%")
                    sys.stdout.flush()
            
            urllib.request.urlretrieve(OFF_UK_URL, gz_path, reporthook=reporthook)
            print()
            
            file_size = gz_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Downloaded ({file_size:.1f} MB)")
        
        # Decompress
        logger.info("📦 Decompressing...")
        with gzip.open(gz_path, 'rb') as f_in:
            with open(jsonl_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info("✅ Decompression complete")
        return jsonl_path
        
    except Exception as e:
        logger.warning(f"⚠️  Could not download OFF data: {e}")
        logger.info("💡 Using sample data instead...")
        return None


def import_off():
    """Import OpenFoodFacts data"""
    try:
        logger.info("🚀 GAINS Food Vision - OpenFoodFacts Import")
        logger.info("=" * 60)
        
        # Initialize database
        init_db()
        
        # Check existing data
        with Session(engine) as session:
            existing_count = session.exec(
                select(func.count(FoodOFF.id))
            ).one()
            
            if existing_count > 0:
                logger.info(f"✅ OFF already imported ({existing_count} products)")
                logger.info("💡 To re-import, delete foods_off table and run again")
                return
        
        # Try to download data
        jsonl_path = download_off_data()
        
        if not jsonl_path or not jsonl_path.exists():
            logger.warning("⚠️  OFF download failed, using sample data...")
            _create_sample_off()
            return
        
        # Process JSONL
        logger.info(f"📖 Parsing OpenFoodFacts data...")
        logger.info(f"   Filtering for UK products (up to {MAX_PRODUCTS} items)...")
        
        with Session(engine) as session:
            count = 0
            skipped = 0
            processed = 0
            
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    processed += 1
                    
                    if count >= MAX_PRODUCTS:
                        logger.info(f"  ✓ Reached max limit of {MAX_PRODUCTS} products")
                        break
                    
                    if processed % 1000 == 0:
                        logger.info(f"  Processing line {processed}... (imported: {count})")
                    
                    try:
                        product = json.loads(line)
                        
                        # Filter for UK products with decent data
                        countries = product.get('countries_tags', [])
                        barcode = product.get('code', '')
                        
                        if not barcode or not isinstance(barcode, str):
                            skipped += 1
                            continue
                        
                        # Check if UK product
                        is_uk = any('united-kingdom' in str(c).lower() or 'en:' in str(c).lower() 
                                   for c in countries)
                        
                        if not is_uk and count > 5000:  # After 5000, only UK products
                            skipped += 1
                            continue
                        
                        # Extract data
                        product_name = product.get('product_name', '') or product.get('product_name_en', '')
                        if not product_name:
                            skipped += 1
                            continue
                        
                        # Nutrition data
                        nutriments = product.get('nutriments', {})
                        
                        def safe_float(key):
                            val = nutriments.get(key) or nutriments.get(f"{key}_100g")
                            try:
                                return float(val) if val is not None else None
                            except:
                                return None
                        
                        energy_kcal = safe_float('energy-kcal')
                        protein_g = safe_float('proteins')
                        carb_g = safe_float('carbohydrates')
                        fat_g = safe_float('fat')
                        fiber_g = safe_float('fiber')
                        sugar_g = safe_float('sugars')
                        saturated_fat_g = safe_float('saturated-fat')
                        sodium_mg = safe_float('sodium')
                        if sodium_mg:  # Convert g to mg if needed
                            if sodium_mg < 10:  # Likely in grams
                                sodium_mg *= 1000
                        
                        # Enrichment data
                        nova_group = product.get('nova_group')
                        if nova_group:
                            try:
                                nova_group = int(nova_group)
                            except:
                                nova_group = None
                        
                        nutriscore_grade = product.get('nutriscore_grade', '').upper() or None
                        
                        ingredients = product.get('ingredients_text_en') or product.get('ingredients_text') or None
                        if ingredients and len(ingredients) > 2000:
                            ingredients = ingredients[:2000]
                        
                        # Additives
                        additives = product.get('additives_tags', [])
                        if additives:
                            additives = ', '.join([str(a).replace('en:', '') for a in additives[:20]])
                        else:
                            additives = None
                        
                        # Allergens
                        allergens = product.get('allergens_tags', [])
                        if allergens:
                            allergens = ', '.join([str(a).replace('en:', '') for a in allergens[:20]])
                        else:
                            allergens = None
                        
                        brands = product.get('brands') or None
                        categories = product.get('categories') or None
                        if categories and len(categories) > 500:
                            categories = categories[:500]
                        
                        # Create record
                        food_off = FoodOFF(
                            code=barcode,
                            product_name=product_name[:200],
                            brands=brands[:100] if brands else None,
                            categories=categories,
                            ingredients_text=ingredients,
                            allergens=allergens,
                            additives=additives,
                            nutriscore_grade=nutriscore_grade,
                            nova_group=nova_group,
                            energy_kcal=energy_kcal,
                            protein_g=protein_g,
                            carb_g=carb_g,
                            fat_g=fat_g,
                            fiber_g=fiber_g,
                            sugar_g=sugar_g,
                            saturated_fat_g=saturated_fat_g,
                            sodium_mg=sodium_mg
                        )
                        
                        session.add(food_off)
                        count += 1
                        
                        if count % 100 == 0:
                            session.commit()
                    
                    except json.JSONDecodeError:
                        skipped += 1
                        continue
                    except Exception as e:
                        logger.debug(f"  Skipped product: {e}")
                        skipped += 1
                        continue
            
            session.commit()
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ OPENFOODFACTS IMPORT COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"📊 Imported: {count} products")
            logger.info(f"⏭️  Skipped: {skipped} items")
            logger.info(f"📁 Source: OpenFoodFacts")
            logger.info("")
    
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def _create_sample_off():
    """Create sample OFF data for testing"""
    sample_products = [
        {
            "code": "5000159484695",
            "product_name": "Heinz Beanz",
            "brands": "Heinz",
            "categories": "Canned foods, Legumes, Beans",
            "ingredients_text": "Beans (51%), Tomatoes (34%), Water, Sugar, Spirit Vinegar, Modified Cornflour, Salt, Spice Extracts, Herb Extract",
            "additives": None,
            "allergens": None,
            "nova_group": 4,
            "nutriscore_grade": "A",
            "energy_kcal": 75.0,
            "protein_g": 4.7,
            "carb_g": 11.5,
            "fat_g": 0.2,
            "fiber_g": 3.7,
            "sugar_g": 4.7,
            "saturated_fat_g": 0.1,
            "sodium_mg": 340.0
        },
        {
            "code": "3017620422003",
            "product_name": "Nutella",
            "brands": "Ferrero",
            "categories": "Spreads, Sweet spreads, Chocolate spreads",
            "ingredients_text": "Sugar, Palm Oil, Hazelnuts (13%), Skimmed Milk Powder (8.7%), Fat-Reduced Cocoa (7.4%), Emulsifier: Lecithins (Soya), Vanillin",
            "additives": "E322",
            "allergens": "Milk, Nuts, Soya",
            "nova_group": 4,
            "nutriscore_grade": "E",
            "energy_kcal": 539.0,
            "protein_g": 6.3,
            "carb_g": 57.5,
            "fat_g": 30.9,
            "fiber_g": 0.0,
            "sugar_g": 56.3,
            "saturated_fat_g": 10.6,
            "sodium_mg": 107.0
        },
        {
            "code": "5449000000996",
            "product_name": "Coca-Cola",
            "brands": "Coca-Cola",
            "categories": "Beverages, Soft drinks, Carbonated drinks",
            "ingredients_text": "Carbonated Water, Sugar, Colour (Caramel E150d), Phosphoric Acid, Natural Flavourings including Caffeine",
            "additives": "E150d, E338",
            "allergens": None,
            "nova_group": 4,
            "nutriscore_grade": "E",
            "energy_kcal": 42.0,
            "protein_g": 0.0,
            "carb_g": 10.6,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sugar_g": 10.6,
            "saturated_fat_g": 0.0,
            "sodium_mg": 0.0
        },
    ]
    
    with Session(engine) as session:
        for prod_data in sample_products:
            food_off = FoodOFF(**prod_data)
            session.add(food_off)
        
        session.commit()
        logger.info(f"✅ Created {len(sample_products)} sample OFF products")


if __name__ == "__main__":
    import_off()
