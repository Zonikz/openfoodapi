"""Build label map from Food-101 to canonical foods with 100% coverage"""
import json
import sys
from pathlib import Path
from sqlmodel import Session, select
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine, init_db
from app.data.schema import LabelMapping, FoodGeneric
from app.data.search import find_canonical_food
from app.config import settings
from app.models.vision_classifier import FOOD101_CLASSES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Manual mappings for classes that don't match CoFID exactly
MANUAL_MAPPINGS = {
    "baby_back_ribs": {"query": "pork ribs", "fallback": "pork chop grilled"},
    "baklava": {"query": "pastry", "fallback": "cake"},
    "beef_carpaccio": {"query": "beef raw", "fallback": "beef steak raw"},
    "beef_tartare": {"query": "beef raw", "fallback": "beef steak raw"},
    "beet_salad": {"query": "beetroot salad", "fallback": "salad mixed"},
    "beignets": {"query": "donut", "fallback": "doughnut"},
    "bibimbap": {"query": "rice mixed", "fallback": "rice cooked"},
    "bread_pudding": {"query": "pudding", "fallback": "bread pudding"},
    "breakfast_burrito": {"query": "burrito", "fallback": "wrap filled"},
    "bruschetta": {"query": "bread toasted", "fallback": "toast"},
    "caesar_salad": {"query": "salad", "fallback": "salad mixed"},
    "cannoli": {"query": "pastry cream", "fallback": "dessert"},
    "caprese_salad": {"query": "salad", "fallback": "salad mixed"},
    "carrot_cake": {"query": "cake", "fallback": "cake"},
    "ceviche": {"query": "fish raw", "fallback": "fish white raw"},
    "cheese_plate": {"query": "cheese", "fallback": "cheese cheddar"},
    "cheesecake": {"query": "cheesecake", "fallback": "cake"},
    "chicken_curry": {"query": "chicken curry", "fallback": "chicken curry"},
    "chicken_quesadilla": {"query": "chicken", "fallback": "chicken breast grilled"},
    "chicken_wings": {"query": "chicken wings", "fallback": "chicken roasted"},
    "chocolate_cake": {"query": "chocolate cake", "fallback": "cake chocolate"},
    "chocolate_mousse": {"query": "chocolate mousse", "fallback": "mousse"},
    "churros": {"query": "donut", "fallback": "doughnut"},
    "clam_chowder": {"query": "soup", "fallback": "soup"},
    "club_sandwich": {"query": "sandwich", "fallback": "sandwich"},
    "crab_cakes": {"query": "crab", "fallback": "fish cake"},
    "creme_brulee": {"query": "cream dessert", "fallback": "custard"},
    "croque_madame": {"query": "sandwich cheese ham", "fallback": "sandwich"},
    "cup_cakes": {"query": "cake", "fallback": "cake"},
    "deviled_eggs": {"query": "egg", "fallback": "egg boiled"},
    "donuts": {"query": "doughnut", "fallback": "doughnut"},
    "dumplings": {"query": "dumpling", "fallback": "pasta filled"},
    "edamame": {"query": "beans", "fallback": "soya beans"},
    "eggs_benedict": {"query": "egg", "fallback": "egg poached"},
    "escargots": {"query": "snails", "fallback": "fish"},
    "falafel": {"query": "falafel", "fallback": "chickpea"},
    "filet_mignon": {"query": "beef steak", "fallback": "beef steak grilled"},
    "fish_and_chips": {"query": "fish fried chips", "fallback": "fish fried"},
    "foie_gras": {"query": "pate", "fallback": "liver pate"},
    "french_fries": {"query": "chips", "fallback": "potato chips fried"},
    "french_onion_soup": {"query": "soup onion", "fallback": "soup"},
    "french_toast": {"query": "toast", "fallback": "bread fried"},
    "fried_calamari": {"query": "squid fried", "fallback": "fish fried"},
    "fried_rice": {"query": "rice fried", "fallback": "rice cooked"},
    "frozen_yogurt": {"query": "yogurt frozen", "fallback": "ice cream"},
    "garlic_bread": {"query": "bread garlic", "fallback": "bread"},
    "gnocchi": {"query": "gnocchi", "fallback": "pasta"},
    "greek_salad": {"query": "salad", "fallback": "salad mixed"},
    "grilled_cheese_sandwich": {"query": "sandwich cheese", "fallback": "sandwich toasted"},
    "grilled_salmon": {"query": "salmon grilled", "fallback": "salmon"},
    "guacamole": {"query": "avocado", "fallback": "avocado"},
    "gyoza": {"query": "dumpling", "fallback": "dumpling"},
    "hamburger": {"query": "burger beef", "fallback": "beef burger"},
    "hot_and_sour_soup": {"query": "soup", "fallback": "soup"},
    "hot_dog": {"query": "hot dog", "fallback": "sausage"},
    "huevos_rancheros": {"query": "egg fried", "fallback": "egg fried"},
    "hummus": {"query": "hummus", "fallback": "chickpea dip"},
    "ice_cream": {"query": "ice cream", "fallback": "ice cream vanilla"},
    "lasagna": {"query": "lasagna", "fallback": "lasagne"},
    "lobster_bisque": {"query": "soup", "fallback": "soup cream"},
    "lobster_roll_sandwich": {"query": "sandwich", "fallback": "sandwich"},
    "macaroni_and_cheese": {"query": "macaroni cheese", "fallback": "pasta cheese"},
    "macarons": {"query": "biscuit", "fallback": "cookie"},
    "miso_soup": {"query": "soup", "fallback": "soup"},
    "mussels": {"query": "mussels", "fallback": "shellfish"},
    "nachos": {"query": "nachos", "fallback": "tortilla chips"},
    "omelette": {"query": "omelette", "fallback": "egg fried"},
    "onion_rings": {"query": "onion fried", "fallback": "onion"},
    "oysters": {"query": "oyster", "fallback": "shellfish"},
    "pad_thai": {"query": "noodles", "fallback": "noodles"},
    "paella": {"query": "rice", "fallback": "rice cooked"},
    "pancakes": {"query": "pancake", "fallback": "pancakes"},
    "panna_cotta": {"query": "cream dessert", "fallback": "custard"},
    "peking_duck": {"query": "duck roasted", "fallback": "duck"},
    "pho": {"query": "soup noodles", "fallback": "soup"},
    "pizza": {"query": "pizza", "fallback": "pizza cheese tomato"},
    "pork_chop": {"query": "pork chop", "fallback": "pork chop grilled"},
    "poutine": {"query": "chips gravy cheese", "fallback": "chips"},
    "prime_rib": {"query": "beef roast", "fallback": "beef roasted"},
    "pulled_pork_sandwich": {"query": "pork sandwich", "fallback": "sandwich"},
    "ramen": {"query": "noodles", "fallback": "noodles"},
    "ravioli": {"query": "ravioli", "fallback": "pasta filled"},
    "red_velvet_cake": {"query": "cake", "fallback": "cake"},
    "risotto": {"query": "risotto", "fallback": "rice cooked"},
    "samosa": {"query": "samosa", "fallback": "pastry filled"},
    "sashimi": {"query": "fish raw", "fallback": "salmon raw"},
    "scallops": {"query": "scallop", "fallback": "shellfish"},
    "seaweed_salad": {"query": "seaweed", "fallback": "salad"},
    "shrimp_and_grits": {"query": "shrimp", "fallback": "prawn"},
    "spaghetti_bolognese": {"query": "spaghetti bolognese", "fallback": "pasta meat sauce"},
    "spaghetti_carbonara": {"query": "spaghetti carbonara", "fallback": "pasta cream"},
    "spring_rolls": {"query": "spring roll", "fallback": "roll"},
    "steak": {"query": "beef steak", "fallback": "beef steak grilled"},
    "strawberry_shortcake": {"query": "cake strawberry", "fallback": "cake"},
    "sushi": {"query": "sushi", "fallback": "sushi mixed"},
    "tacos": {"query": "taco", "fallback": "taco"},
    "takoyaki": {"query": "fish ball", "fallback": "fish"},
    "tiramisu": {"query": "tiramisu", "fallback": "dessert"},
    "tuna_tartare": {"query": "tuna raw", "fallback": "tuna"},
    "waffles": {"query": "waffle", "fallback": "waffles"},
    "apple_pie": {"query": "apple pie", "fallback": "pie fruit"}
}


def build_label_map():
    """Build label map from Food-101 classes to canonical foods with 100% coverage"""
    try:
        logger.info("🚀 GAINS Food Vision - Label Map Builder")
        logger.info("=" * 60)
        logger.info(f"📊 Building map for {len(FOOD101_CLASSES)} Food-101 classes...")
        
        # Initialize database
        init_db()
        
        label_map = {}
        mapped_count = 0
        fallback_count = 0
        
        with Session(engine) as session:
            for food101_label in FOOD101_CLASSES:
                # Try manual mapping first
                if food101_label in MANUAL_MAPPINGS:
                    mapping_info = MANUAL_MAPPINGS[food101_label]
                    query = mapping_info["query"]
                    fallback_query = mapping_info.get("fallback")
                else:
                    # Convert underscore to space
                    query = food101_label.replace("_", " ")
                    fallback_query = None
                
                # Find canonical food
                result = find_canonical_food(session, query)
                
                # Try fallback if no result
                if not result and fallback_query:
                    logger.info(f"  ⚠️  {food101_label}: no match for '{query}', trying fallback '{fallback_query}'...")
                    result = find_canonical_food(session, fallback_query)
                    if result:
                        fallback_count += 1
                
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
                    
                    if existing:
                        existing.canonical_source = result["source"]
                        existing.canonical_id = result["source_id"]
                        existing.confidence = 1.0
                    else:
                        mapping = LabelMapping(
                            food101_label=food101_label,
                            canonical_source=result["source"],
                            canonical_id=result["source_id"],
                            confidence=1.0
                        )
                        session.add(mapping)
                    
                    mapped_count += 1
                    logger.info(f"  ✓ {food101_label} → {result['name']} ({result['source_id']})")
                else:
                    logger.warning(f"  ✗ {food101_label} → NOT FOUND (query: '{query}')")
            
            session.commit()
        
        # Save to JSON
        json_path = settings.label_map_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w') as f:
            json.dump({
                "_note": "Mapping from Food-101 labels to canonical food IDs. Build with: python tools/build_label_map.py",
                **label_map
            }, f, indent=2)
        
        coverage = (mapped_count / len(FOOD101_CLASSES)) * 100
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ LABEL MAP BUILD COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"📊 Mapped: {mapped_count}/{len(FOOD101_CLASSES)} ({coverage:.1f}%)")
        logger.info(f"🔄 Fallbacks used: {fallback_count}")
        logger.info(f"📁 Saved to: {json_path}")
        
        if coverage < 100:
            missing = len(FOOD101_CLASSES) - mapped_count
            logger.warning(f"⚠️  {missing} classes still missing!")
            logger.warning("💡 Add more CoFID data or update MANUAL_MAPPINGS")
        else:
            logger.info("🎉 100% COVERAGE ACHIEVED!")
        
        logger.info("")
    
    except Exception as e:
        logger.error(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    build_label_map()
