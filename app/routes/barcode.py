"""Barcode lookup endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
import logging

from app.data.db import get_db
from app.data.schema import CanonicalFood, FoodOFF, FoodGeneric
from app.routes.mapping import _format_off_food, _format_generic_food

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/barcode/{gtin}", response_model=CanonicalFood)
async def lookup_barcode(
    gtin: str,
    db: Session = Depends(get_db)
):
    """
    Lookup product by barcode/GTIN
    
    Args:
        gtin: Barcode (GTIN-8, GTIN-12, GTIN-13, GTIN-14)
    
    Returns:
        Canonical food with nutrition data
    """
    try:
        # Normalize barcode
        gtin = gtin.strip()
        
        # 1. Try OpenFoodFacts
        food_off = db.exec(
            select(FoodOFF).where(FoodOFF.code == gtin)
        ).first()
        
        if food_off:
            return _format_off_food(food_off)
        
        # 2. Fallback to generic foods (some have barcodes)
        food_generic = db.exec(
            select(FoodGeneric).where(FoodGeneric.source_id == gtin)
        ).first()
        
        if food_generic:
            return _format_generic_food(food_generic)
        
        # Not found
        raise HTTPException(
            status_code=404,
            detail=f"No product found for barcode: {gtin}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Barcode lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
