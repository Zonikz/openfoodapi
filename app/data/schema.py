"""Database schemas using SQLModel"""
from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict, List
from datetime import datetime


class FoodGeneric(SQLModel, table=True):
    """Generic foods from CoFID, USDA, etc."""
    __tablename__ = "foods_generic"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)  # "cofid", "usda"
    source_id: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    name_lower: str = Field(index=True)  # For case-insensitive search
    
    # Nutrition per 100g
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carb_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    
    # Optional enrichment
    category: Optional[str] = None
    subcategory: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FoodOFF(SQLModel, table=True):
    """OpenFoodFacts products"""
    __tablename__ = "foods_off"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)  # Barcode/GTIN
    product_name: str = Field(index=True)
    product_name_lower: str = Field(index=True)
    
    # Nutrition per 100g
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carb_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    
    # OpenFoodFacts enrichment
    nova_group: Optional[int] = None
    nutriscore_grade: Optional[str] = None
    additives: Optional[str] = None  # JSON array as string
    categories: Optional[str] = None
    brands: Optional[str] = None
    countries: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LabelMapping(SQLModel, table=True):
    """Mapping from Food-101 labels to canonical foods"""
    __tablename__ = "label_map"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    food101_label: str = Field(unique=True, index=True)
    canonical_source: str  # "cofid", "off", "usda"
    canonical_id: str = Field(index=True)
    confidence: float = Field(default=1.0)  # Mapping confidence
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FoodAlias(SQLModel, table=True):
    """Alternative names for foods"""
    __tablename__ = "aliases"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = Field(index=True)
    alias_lower: str = Field(index=True)
    canonical_source: str
    canonical_id: str = Field(index=True)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Pydantic models for API

class NutritionPer100g(SQLModel):
    """Nutrition information per 100g"""
    energy_kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class ServingSize(SQLModel):
    """Serving size"""
    name: str
    grams: float


class FoodEnrichment(SQLModel):
    """Additional food metadata"""
    nova: Optional[int] = None
    nutriscore: Optional[str] = None
    additives: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    brands: Optional[str] = None


class CanonicalFood(SQLModel):
    """Canonical food with full nutrition data"""
    canonical_name: str
    source: str
    source_id: str
    per_100g: NutritionPer100g
    servings: List[ServingSize]
    enrichment: Optional[FoodEnrichment] = None


class ClassificationResult(SQLModel):
    """Vision classification result"""
    label: str
    score: float


class ClassifyResponse(SQLModel):
    """Response from /classify endpoint"""
    model: str
    top_k: List[ClassificationResult]
    inference_ms: int


class MapToFoodRequest(SQLModel):
    """Request to map prediction to food"""
    query: str
    country: Optional[str] = "UK"


class DetectionBox(SQLModel):
    """Bounding box detection"""
    label: str
    score: float
    box: List[float]  # [x1, y1, x2, y2]


class DetectResponse(SQLModel):
    """Response from /detect-foods endpoint"""
    model: str
    detections: List[DetectionBox]
    inference_ms: int


class MacroNutrition(SQLModel):
    """Macro nutrition for a portion"""
    energy_kcal: float
    protein_g: float
    carb_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class GAINSScore(SQLModel):
    """GAINS scoring components"""
    protein_density: float
    carb_quality: float
    fat_quality: float
    processing: float
    transparency: float
    overall: float


class GAINSRequest(SQLModel):
    """Request for GAINS scoring"""
    canonical_id: str
    grams: float


class GAINSResponse(SQLModel):
    """Response from /score/gains endpoint"""
    macros: MacroNutrition
    score: GAINSScore
    grade: str  # A, B, C, D, E, F
