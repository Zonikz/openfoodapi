"""Food mapping endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
import json
import logging
from typing import Optional

from app.data.db import get_db
from app.data.schema import (
    MapToFoodRequest, CanonicalFood, NutritionPer100g,
    ServingSize, FoodEnrichment, FoodGeneric, FoodOFF, LabelMapping
)
from app.data.search import find_canonical_food
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/map-to-food", response_model=CanonicalFood)
async def map_to_food(
    request: MapToFoodRequest,
    db: Session = Depends(get_db)
):
    """
    Map Food-101 prediction to canonical food
    
    Args:
        query: Food-101 label or food name
        country: Filter by country (e.g., "UK")
    
    Returns:
        Canonical food with nutrition data
    """
    try:
        # 1. Try label map first
        label_mapping = db.exec(
            select(LabelMapping)
            .where(LabelMapping.food101_label == request.query)
        ).first()
        
        if label_mapping:
            # Get canonical food
            source = label_mapping.canonical_source
            canonical_id = label_mapping.canonical_id
            
            if source == "off":
                food = db.exec(
                    select(FoodOFF).where(FoodOFF.code == canonical_id)
                ).first()
                
                if food:
                    return _format_off_food(food)
            
            elif source in ["cofid", "usda"]:
                food = db.exec(
                    select(FoodGeneric)
                    .where(FoodGeneric.source_id == canonical_id)
                ).first()
                
                if food:
                    return _format_generic_food(food)
        
        # 2. Fallback to fuzzy search
        result = find_canonical_food(db, request.query, country=request.country)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No food found for query: {request.query}"
            )
        
        # Format result
        if result["source"] == "off":
            food = db.exec(
                select(FoodOFF).where(FoodOFF.code == result["source_id"])
            ).first()
            if food:
                return _format_off_food(food)
        else:
            food = db.exec(
                select(FoodGeneric)
                .where(FoodGeneric.source_id == result["source_id"])
            ).first()
            if food:
                return _format_generic_food(food)
        
        raise HTTPException(status_code=404, detail="Food not found in database")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mapping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _format_generic_food(food: FoodGeneric) -> CanonicalFood:
    """Format generic food as CanonicalFood"""
    return CanonicalFood(
        canonical_name=food.name,
        source=food.source,
        source_id=food.source_id,
        per_100g=NutritionPer100g(
            energy_kcal=food.energy_kcal or 0,
            protein_g=food.protein_g or 0,
            carb_g=food.carb_g or 0,
            fat_g=food.fat_g or 0,
            fiber_g=food.fiber_g,
            sugar_g=food.sugar_g,
            saturated_fat_g=food.saturated_fat_g,
            sodium_mg=food.sodium_mg
        ),
        servings=[
            ServingSize(name="100 g", grams=100),
            ServingSize(name="1 portion", grams=250)
        ],
        enrichment=None
    )


def _format_off_food(food: FoodOFF) -> CanonicalFood:
    """Format OpenFoodFacts food as CanonicalFood"""
    # Parse additives
    additives = None
    if food.additives:
        try:
            additives = json.loads(food.additives)
        except:
            additives = food.additives.split(",") if food.additives else None
    
    # Parse categories
    categories = None
    if food.categories:
        categories = food.categories.split(",")
    
    return CanonicalFood(
        canonical_name=food.product_name,
        source="off",
        source_id=food.code,
        per_100g=NutritionPer100g(
            energy_kcal=food.energy_kcal or 0,
            protein_g=food.protein_g or 0,
            carb_g=food.carb_g or 0,
            fat_g=food.fat_g or 0,
            fiber_g=food.fiber_g,
            sugar_g=food.sugar_g,
            saturated_fat_g=food.saturated_fat_g,
            sodium_mg=food.sodium_mg
        ),
        servings=[
            ServingSize(name="100 g", grams=100),
            ServingSize(name="1 serving", grams=30)
        ],
        enrichment=FoodEnrichment(
            nova=food.nova_group,
            nutriscore=food.nutriscore_grade,
            additives=additives,
            categories=categories,
            brands=food.brands
        )
    )
