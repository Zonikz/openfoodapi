"""Import OpenFoodFacts (OFF) data - streaming, production-ready"""
import json
import sys
import os
import argparse
from pathlib import Path
from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError
import logging
import urllib.request
import gzip

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import FoodOFF
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OFF URLs with fallback
OFF_URLS = [
    "https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz",
    "https://static.openfoodfacts.org/data/openfoodfacts-products-latest.jsonl.gz"
]

# Default config
DEFAULT_COUNTRY = os.environ.get("DEFAULT_COUNTRY", "UK")
OFF_BATCH_SIZE = int(os.environ.get("OFF_BATCH_SIZE", "500"))


def download_off_data(output_path: Path) -> bool:
    """Download OFF data dump with fallback URLs"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        logger.info(f"✅ OFF data already exists: {output_path}")
        return True
    
    for url in OFF_URLS:
        try:
            logger.info(f"📥 Downloading OpenFoodFacts from {url}")
            logger.info("   ⏳ This may take 10-30 minutes (10+ GB file)...")
            
            # Download with progress and chunking (streaming)
            def reporthook(count, block_size, total_size):
                if total_size > 0:
                    percent = count * block_size * 100 / total_size
                    mb_downloaded = count * block_size / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    sys.stdout.write(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.0f}/{mb_total:.0f} MB)")
                    sys.stdout.flush()
            
            urllib.request.urlretrieve(url, output_path, reporthook=reporthook)
            print()
            
            file_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Downloaded ({file_size:.1f} MB)")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to download from {url}: {e}")
            if output_path.exists():
                output_path.unlink()
            continue
    
    logger.error("❌ All download URLs failed")
    return False


def parse_nutrition(nutriments: dict, key: str) -> float:
    """Safely parse nutrition value with null handling"""
    val = nutriments.get(key) or nutriments.get(f"{key}_100g")
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def compute_sodium(nutriments: dict) -> float:
    """Compute sodium_mg from salt or sodium with proper conversion"""
    sodium_mg = parse_nutrition(nutriments, 'sodium')
    
    if sodium_mg is not None:
        # If value is very small, likely in grams - convert to mg
        if sodium_mg < 10:
            sodium_mg *= 1000
        return sodium_mg
    
    # Fallback: compute from salt (salt = sodium × 2.5)
    salt_g = parse_nutrition(nutriments, 'salt')
    if salt_g is not None:
        return salt_g * 400  # 1g salt = 400mg sodium
    
    return None


def import_off(
    file_path: Path = None,
    country: str = DEFAULT_COUNTRY,
    limit: int = 12000,
    batch_size: int = OFF_BATCH_SIZE
):
    """
    Import OpenFoodFacts data with streaming (no RAM explosion)
    
    Args:
        file_path: Path to local .jsonl.gz file (if None, downloads from OFF)
        country: Filter by country code (e.g., "UK", "US", "FR")
        limit: Max products to import (0 = unlimited)
        batch_size: Number of products to batch before commit
    """
    try:
        logger.info("🚀 GAINS Food Vision - OpenFoodFacts Import (Streaming)")
        logger.info("=" * 60)
        logger.info(f"   Country: {country}")
        logger.info(f"   Limit: {limit if limit > 0 else 'UNLIMITED'}")
        logger.info(f"   Batch size: {batch_size}")
        logger.info("")
        
        # Initialize database
        init_db()
        
        # Check existing data
        with Session(engine) as session:
            existing_count = session.exec(
                select(func.count(FoodOFF.id))
            ).one()
            
            if existing_count > 0:
                logger.info(f"ℹ️  OFF already has {existing_count} products")
                logger.info(f"   Will skip duplicates (IntegrityError on UNIQUE constraint)")
        
        # Determine file path
        if file_path is None:
            # Check env var first
            env_path = os.environ.get("OFF_DUMP_PATH")
            if env_path:
                file_path = Path(env_path)
                logger.info(f"📁 Using OFF_DUMP_PATH: {file_path}")
            else:
                # Download to default location
                file_path = Path("seeds/data/off.jsonl.gz")
                if not file_path.exists():
                    logger.info("📁 No local file, downloading...")
                    if not download_off_data(file_path):
                        logger.error("❌ Download failed, cannot continue")
                        logger.info("💡 Try: curl -L -o seeds/data/off.jsonl.gz <URL>")
                        return
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return
        
        logger.info(f"📖 Streaming from: {file_path}")
        logger.info(f"   File size: {file_path.stat().st_size / (1024 * 1024):.1f} MB")
        logger.info("")
        
        # Stream parse JSONL (line-by-line, no full file load)
        with Session(engine) as session:
            count = 0
            skipped = 0
            duplicates = 0
            processed = 0
            batch = []
            
            # Open gzipped file and stream lines
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    processed += 1
                    
                    # Check limit
                    if limit > 0 and count >= limit:
                        logger.info(f"  ✓ Reached limit of {limit} products")
                        break
                    
                    # Progress every 1000 lines
                    if processed % 1000 == 0:
                        logger.info(f"  Processing line {processed:,}... (imported: {count:,}, skipped: {skipped:,}, duplicates: {duplicates:,})")
                    
                    try:
                        product = json.loads(line)
                        
                        # Extract barcode
                        barcode = product.get('code', '')
                        if not barcode or not isinstance(barcode, str):
                            skipped += 1
                            continue
                        
                        # Filter by country
                        countries = product.get('countries_tags', [])
                        country_match = False
                        
                        for c in countries:
                            c_str = str(c).lower()
                            if country.lower() == "uk" and ("united-kingdom" in c_str or "gb" in c_str):
                                country_match = True
                                break
                            elif country.lower() in c_str:
                                country_match = True
                                break
                        
                        if not country_match:
                            skipped += 1
                            continue
                        
                        # Extract product name
                        product_name = product.get('product_name', '') or product.get('product_name_en', '')
                        if not product_name:
                            skipped += 1
                            continue
                        
                        # Parse nutrition
                        nutriments = product.get('nutriments', {})
                        
                        energy_kcal = parse_nutrition(nutriments, 'energy-kcal')
                        protein_g = parse_nutrition(nutriments, 'proteins')
                        carb_g = parse_nutrition(nutriments, 'carbohydrates')
                        fat_g = parse_nutrition(nutriments, 'fat')
                        fiber_g = parse_nutrition(nutriments, 'fiber')
                        sugar_g = parse_nutrition(nutriments, 'sugars')
                        saturated_fat_g = parse_nutrition(nutriments, 'saturated-fat')
                        sodium_mg = compute_sodium(nutriments)
                        
                        # Enrichment data
                        nova_group = product.get('nova_group')
                        if nova_group:
                            try:
                                nova_group = int(nova_group)
                            except (ValueError, TypeError):
                                nova_group = None
                        
                        nutriscore_grade = product.get('nutriscore_grade', '').upper() or None
                        
                        # Ingredients
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
                        
                        batch.append(food_off)
                        count += 1
                        
                        # Batch commit
                        if len(batch) >= batch_size:
                            try:
                                session.add_all(batch)
                                session.commit()
                                batch = []
                            except IntegrityError:
                                # Handle duplicates
                                session.rollback()
                                # Insert one by one to identify duplicates
                                for item in batch:
                                    try:
                                        session.add(item)
                                        session.commit()
                                    except IntegrityError:
                                        session.rollback()
                                        duplicates += 1
                                        count -= 1  # Don't count duplicate as imported
                                batch = []
                    
                    except json.JSONDecodeError:
                        skipped += 1
                        continue
                    except Exception as e:
                        logger.debug(f"  Skipped product: {e}")
                        skipped += 1
                        continue
            
            # Final batch commit
            if batch:
                try:
                    session.add_all(batch)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    for item in batch:
                        try:
                            session.add(item)
                            session.commit()
                        except IntegrityError:
                            session.rollback()
                            duplicates += 1
                            count -= 1
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ OPENFOODFACTS IMPORT COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"📊 Imported: {count:,} products")
            logger.info(f"⏭️  Skipped: {skipped:,} items (no barcode/name/country)")
            logger.info(f"🔁 Duplicates: {duplicates:,} items (already in DB)")
            logger.info(f"📁 Source: OpenFoodFacts ({country})")
            logger.info("")
    
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def _create_sample_off():
    """Create sample OFF data for testing (with OR IGNORE for duplicates)"""
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
            try:
                food_off = FoodOFF(**prod_data)
                session.add(food_off)
                session.commit()
            except IntegrityError:
                # Skip duplicate
                session.rollback()
                continue
        
        logger.info(f"✅ Sample OFF products ready")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import OpenFoodFacts data (streaming)")
    parser.add_argument("--file", type=Path, help="Path to local off.jsonl.gz file")
    parser.add_argument("--country", type=str, default=DEFAULT_COUNTRY, help="Filter by country (e.g., UK, US, FR)")
    parser.add_argument("--limit", type=int, default=12000, help="Max products to import (0 = unlimited)")
    parser.add_argument("--batch-size", type=int, default=OFF_BATCH_SIZE, help="Batch size for inserts")
    
    args = parser.parse_args()
    
    import_off(
        file_path=args.file,
        country=args.country,
        limit=args.limit,
        batch_size=args.batch_size
    )
