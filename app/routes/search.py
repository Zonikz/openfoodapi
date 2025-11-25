"""Food search endpoints"""
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
import logging

from app.data.db import get_db
from app.data.search import search_foods

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/foods/search")
async def search_foods_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    country: Optional[str] = Query(None, description="Filter by country (e.g., UK)"),
    min_score: int = Query(60, ge=0, le=100, description="Min fuzzy match score"),
    db: Session = Depends(get_db)
):
    """
    Fuzzy search foods across all sources
    
    Args:
        q: Search query (min 2 chars)
        limit: Max results (1-50)
        country: Filter by country
        min_score: Min fuzzy match score (0-100)
    
    Returns:
        List of matching foods with scores
    """
    try:
        results = search_foods(
            db=db,
            query=q,
            limit=limit,
            country=country,
            min_score=min_score
        )
        
        # Format response
        return {
            "query": q,
            "count": len(results),
            "results": [
                {
                    "food": food,
                    "match_score": score
                }
                for food, score in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
