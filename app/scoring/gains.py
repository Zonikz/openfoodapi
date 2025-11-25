"""GAINS scoring algorithm"""
from typing import Dict, Tuple
import logging

from app.config import settings
from app.data.schema import GAINSScore, MacroNutrition

logger = logging.getLogger(__name__)


def calculate_gains_score(
    nutrition: Dict[str, float],
    grams: float,
    nova: int = None,
    nutriscore: str = None,
    additives: list = None
) -> Tuple[MacroNutrition, GAINSScore, str]:
    """
    Calculate GAINS score
    
    Components:
    - Protein density (0-1): protein per 100 kcal
    - Carb quality (0-1): fiber ratio, sugar penalty
    - Fat quality (0-1): sat fat ratio
    - Processing (0-1): NOVA score penalty
    - Transparency (0-1): data completeness
    
    Args:
        nutrition: Per-100g nutrition dict
        grams: Portion size
        nova: NOVA group (1-4)
        nutriscore: NutriScore grade (A-E)
        additives: List of additives
    
    Returns:
        (macros, score, grade)
    """
    
    # Calculate macros for portion
    multiplier = grams / 100.0
    macros = MacroNutrition(
        energy_kcal=round(nutrition.get("energy_kcal", 0) * multiplier, 1),
        protein_g=round(nutrition.get("protein_g", 0) * multiplier, 1),
        carb_g=round(nutrition.get("carb_g", 0) * multiplier, 1),
        fat_g=round(nutrition.get("fat_g", 0) * multiplier, 1),
        fiber_g=round(nutrition.get("fiber_g", 0) * multiplier, 1) if nutrition.get("fiber_g") else None,
        sugar_g=round(nutrition.get("sugar_g", 0) * multiplier, 1) if nutrition.get("sugar_g") else None,
        saturated_fat_g=round(nutrition.get("saturated_fat_g", 0) * multiplier, 1) if nutrition.get("saturated_fat_g") else None,
        sodium_mg=round(nutrition.get("sodium_mg", 0) * multiplier, 1) if nutrition.get("sodium_mg") else None,
    )
    
    # 1. Protein density (g protein per 100 kcal)
    energy_kcal = nutrition.get("energy_kcal", 1)  # Avoid division by zero
    protein_g = nutrition.get("protein_g", 0)
    protein_per_100kcal = (protein_g / energy_kcal) * 100 if energy_kcal > 0 else 0
    
    # Scale: 0-10g protein per 100kcal → 0-1
    protein_density = min(protein_per_100kcal / 10.0, 1.0)
    
    # 2. Carb quality
    carb_g = nutrition.get("carb_g", 0)
    fiber_g = nutrition.get("fiber_g", 0)
    sugar_g = nutrition.get("sugar_g", carb_g)  # Assume all carbs are sugar if missing
    
    if carb_g > 0:
        fiber_ratio = fiber_g / carb_g
        sugar_ratio = sugar_g / carb_g
        
        # High fiber = good, high sugar = bad
        carb_quality = fiber_ratio * 0.5 + (1 - sugar_ratio) * 0.5
        carb_quality = max(0, min(carb_quality, 1.0))
    else:
        carb_quality = 0.5  # Neutral if no carbs
    
    # 3. Fat quality
    fat_g = nutrition.get("fat_g", 0)
    saturated_fat_g = nutrition.get("saturated_fat_g", fat_g * 0.5)  # Assume 50% if missing
    
    if fat_g > 0:
        sat_fat_ratio = saturated_fat_g / fat_g
        # Lower saturated fat = better
        fat_quality = 1 - sat_fat_ratio
        fat_quality = max(0, min(fat_quality, 1.0))
    else:
        fat_quality = 0.5  # Neutral if no fat
    
    # 4. Processing score
    if nova:
        # NOVA: 1 (unprocessed) = 1.0, 4 (ultra-processed) = 0.0
        processing = (5 - nova) / 4.0
    elif nutriscore:
        # NutriScore: A=1.0, E=0.0
        nutriscore_map = {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.25, "E": 0.0}
        processing = nutriscore_map.get(nutriscore.upper(), 0.5)
    else:
        processing = 0.5  # Neutral if no data
    
    # Additive penalty
    if additives:
        num_additives = len(additives)
        additive_penalty = min(num_additives * 0.05, 0.3)  # Max 30% penalty
        processing = max(0, processing - additive_penalty)
    
    # 5. Transparency (data completeness)
    fields = [
        nutrition.get("energy_kcal"),
        nutrition.get("protein_g"),
        nutrition.get("carb_g"),
        nutrition.get("fat_g"),
        nutrition.get("fiber_g"),
        nutrition.get("sugar_g"),
        nutrition.get("saturated_fat_g"),
        nutrition.get("sodium_mg"),
    ]
    completeness = sum(1 for f in fields if f is not None) / len(fields)
    transparency = completeness
    
    # Weighted overall score
    overall = (
        protein_density * settings.GAINS_PROTEIN_WEIGHT +
        carb_quality * settings.GAINS_CARB_WEIGHT +
        fat_quality * settings.GAINS_FAT_WEIGHT +
        processing * settings.GAINS_PROCESSING_WEIGHT +
        transparency * settings.GAINS_TRANSPARENCY_WEIGHT
    )
    
    score = GAINSScore(
        protein_density=round(protein_density, 2),
        carb_quality=round(carb_quality, 2),
        fat_quality=round(fat_quality, 2),
        processing=round(processing, 2),
        transparency=round(transparency, 2),
        overall=round(overall, 2)
    )
    
    # Grade: A (0.8+), B (0.6-0.8), C (0.4-0.6), D (0.2-0.4), E (0-0.2), F (<0)
    if overall >= 0.8:
        grade = "A"
    elif overall >= 0.6:
        grade = "B"
    elif overall >= 0.4:
        grade = "C"
    elif overall >= 0.2:
        grade = "D"
    elif overall >= 0:
        grade = "E"
    else:
        grade = "F"
    
    return macros, score, grade
