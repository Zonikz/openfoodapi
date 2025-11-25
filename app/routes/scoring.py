"""GAINS scoring endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
import json
import logging

from app.data.db import get_db
from app.data.schema import (
    GAINSRequest, GAINSResponse, FoodGeneric, FoodOFF
)
from app.scoring.gains import calculate_gains_score

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/score/gains", response_model=GAINSResponse)
async def calculate_gains(
    request: GAINSRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate GAINS score for a food portion
    
    Args:
        canonical_id: Food source ID (e.g., "COFID:12345", "5000159407236")
        grams: Portion size in grams
    
    Returns:
        GAINS score with macros and grade
    """
    try:
        # Parse source from canonical_id
        parts = request.canonical_id.split(":")
        
        if len(parts) == 2:
            source = parts[0].lower()
            source_id = parts[1]
        else:
            # Assume barcode
            source = "off"
            source_id = request.canonical_id
        
        # Fetch food
        nutrition = None
        nova = None
        nutriscore = None
        additives = None
        
        if source == "off":
            food = db.exec(
                select(FoodOFF).where(FoodOFF.code == source_id)
            ).first()
            
            if food:
                nutrition = {
                    "energy_kcal": food.energy_kcal or 0,
                    "protein_g": food.protein_g or 0,
                    "carb_g": food.carb_g or 0,
                    "fat_g": food.fat_g or 0,
                    "fiber_g": food.fiber_g,
                    "sugar_g": food.sugar_g,
                    "saturated_fat_g": food.saturated_fat_g,
                    "sodium_mg": food.sodium_mg
                }
                nova = food.nova_group
                nutriscore = food.nutriscore_grade
                
                if food.additives:
                    try:
                        additives = json.loads(food.additives)
                    except:
                        additives = food.additives.split(",") if food.additives else None
        
        elif source in ["cofid", "usda"]:
            food = db.exec(
                select(FoodGeneric)
                .where(FoodGeneric.source_id == source_id)
            ).first()
            
            if food:
                nutrition = {
                    "energy_kcal": food.energy_kcal or 0,
                    "protein_g": food.protein_g or 0,
                    "carb_g": food.carb_g or 0,
                    "fat_g": food.fat_g or 0,
                    "fiber_g": food.fiber_g,
                    "sugar_g": food.sugar_g,
                    "saturated_fat_g": food.saturated_fat_g,
                    "sodium_mg": food.sodium_mg
                }
        
        if not nutrition:
            raise HTTPException(
                status_code=404,
                detail=f"Food not found: {request.canonical_id}"
            )
        
        # Calculate GAINS score
        macros, score, grade = calculate_gains_score(
            nutrition=nutrition,
            grams=request.grams,
            nova=nova,
            nutriscore=nutriscore,
            additives=additives
        )
        
        return GAINSResponse(
            macros=macros,
            score=score,
            grade=grade
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GAINS scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
