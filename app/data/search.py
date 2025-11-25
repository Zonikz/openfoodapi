"""Food search functionality with fuzzy matching"""
from sqlmodel import Session, select, or_
from rapidfuzz import fuzz, process
from typing import List, Tuple, Optional
import logging

from app.data.schema import FoodGeneric, FoodOFF, FoodAlias

logger = logging.getLogger(__name__)


def search_foods(
    db: Session,
    query: str,
    limit: int = 10,
    country: Optional[str] = None,
    min_score: int = 60
) -> List[Tuple[dict, float]]:
    """
    Fuzzy search foods across all sources
    
    Args:
        db: Database session
        query: Search query
        limit: Max results
        country: Filter by country (e.g., "UK")
        min_score: Minimum fuzzy match score (0-100)
    
    Returns:
        List of (food_dict, score) tuples
    """
    query_lower = query.lower().strip()
    results = []
    
    # 1. Search generic foods (CoFID, USDA)
    generic_foods = db.exec(
        select(FoodGeneric)
        .where(FoodGeneric.name_lower.contains(query_lower))
        .limit(limit * 2)
    ).all()
    
    for food in generic_foods:
        score = fuzz.token_set_ratio(query_lower, food.name_lower)
        if score >= min_score:
            results.append(({
                "source": food.source,
                "source_id": food.source_id,
                "name": food.name,
                "nutrition": {
                    "energy_kcal": food.energy_kcal,
                    "protein_g": food.protein_g,
                    "carb_g": food.carb_g,
                    "fat_g": food.fat_g,
                }
            }, score))
    
    # 2. Search OpenFoodFacts
    off_foods = db.exec(
        select(FoodOFF)
        .where(FoodOFF.product_name_lower.contains(query_lower))
        .limit(limit * 2)
    ).all()
    
    for food in off_foods:
        score = fuzz.token_set_ratio(query_lower, food.product_name_lower)
        if score >= min_score:
            # Filter by country if specified
            if country and food.countries:
                if country.lower() not in food.countries.lower():
                    continue
            
            results.append(({
                "source": "off",
                "source_id": food.code,
                "name": food.product_name,
                "brand": food.brands,
                "nutrition": {
                    "energy_kcal": food.energy_kcal,
                    "protein_g": food.protein_g,
                    "carb_g": food.carb_g,
                    "fat_g": food.fat_g,
                },
                "enrichment": {
                    "nova": food.nova_group,
                    "nutriscore": food.nutriscore_grade,
                }
            }, score))
    
    # 3. Search aliases
    aliases = db.exec(
        select(FoodAlias)
        .where(FoodAlias.alias_lower.contains(query_lower))
        .limit(limit * 2)
    ).all()
    
    for alias in aliases:
        score = fuzz.token_set_ratio(query_lower, alias.alias_lower)
        if score >= min_score:
            # Fetch canonical food
            if alias.canonical_source == "off":
                food = db.exec(
                    select(FoodOFF).where(FoodOFF.code == alias.canonical_id)
                ).first()
                if food:
                    results.append(({
                        "source": "off",
                        "source_id": food.code,
                        "name": food.product_name,
                        "alias": alias.alias,
                        "nutrition": {
                            "energy_kcal": food.energy_kcal,
                            "protein_g": food.protein_g,
                            "carb_g": food.carb_g,
                            "fat_g": food.fat_g,
                        }
                    }, score))
            else:
                food = db.exec(
                    select(FoodGeneric)
                    .where(FoodGeneric.source_id == alias.canonical_id)
                ).first()
                if food:
                    results.append(({
                        "source": food.source,
                        "source_id": food.source_id,
                        "name": food.name,
                        "alias": alias.alias,
                        "nutrition": {
                            "energy_kcal": food.energy_kcal,
                            "protein_g": food.protein_g,
                            "carb_g": food.carb_g,
                            "fat_g": food.fat_g,
                        }
                    }, score))
    
    # Sort by score and deduplicate
    results.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    unique_results = []
    
    for food, score in results:
        key = (food["source"], food["source_id"])
        if key not in seen:
            seen.add(key)
            unique_results.append((food, score))
            if len(unique_results) >= limit:
                break
    
    return unique_results


def find_canonical_food(
    db: Session,
    query: str,
    country: Optional[str] = None
) -> Optional[dict]:
    """
    Find best matching canonical food
    
    Args:
        db: Database session
        query: Food name or label
        country: Filter by country
    
    Returns:
        Food dict or None
    """
    results = search_foods(db, query, limit=1, country=country)
    if results:
        return results[0][0]
    return None
