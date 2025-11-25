"""Validate CoFID database import"""
import sys
from pathlib import Path
from sqlmodel import Session, select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine
from app.data.schema import FoodGeneric


TEST_FOODS = [
    "boiled rice",
    "grilled chicken breast",
    "fried egg",
    "pasta cooked",
    "oats raw",
    "baked beans",
    "chicken curry",
    "salmon grilled",
    "potato boiled",
    "bread white"
]


def validate_cofid():
    """Validate CoFID data import"""
    print("=" * 60)
    print("🧪 VALIDATING CoFID DATABASE")
    print("=" * 60)
    
    passed = []
    failed = []
    
    with Session(engine) as session:
        # Test 1: Check table exists and has data
        total_count = session.exec(
            select(FoodGeneric).where(FoodGeneric.source == "cofid")
        ).all()
        
        if len(total_count) > 0:
            print(f"✅ CoFID table has {len(total_count)} entries")
            passed.append(f"CoFID entries: {len(total_count)}")
        else:
            print("❌ CoFID table is empty")
            failed.append("No CoFID entries found")
            return passed, failed
        
        # Test 2: Check test foods
        print("\n📊 Testing sample foods...")
        for food_name in TEST_FOODS:
            food = session.exec(
                select(FoodGeneric)
                .where(FoodGeneric.name_lower.contains(food_name.lower()))
                .where(FoodGeneric.source == "cofid")
            ).first()
            
            if food:
                print(f"\n  {food_name}:")
                print(f"    Name: {food.name}")
                print(f"    ID: {food.source_id}")
                
                # Validate macronutrients
                macro_checks = []
                if food.energy_kcal and food.energy_kcal > 0:
                    macro_checks.append(f"Energy: {food.energy_kcal} kcal")
                else:
                    macro_checks.append("⚠️ Energy missing")
                
                if food.protein_g is not None and food.protein_g >= 0:
                    macro_checks.append(f"Protein: {food.protein_g}g")
                else:
                    macro_checks.append("⚠️ Protein missing")
                
                if food.carb_g is not None and food.carb_g >= 0:
                    macro_checks.append(f"Carbs: {food.carb_g}g")
                else:
                    macro_checks.append("⚠️ Carbs missing")
                
                if food.fat_g is not None and food.fat_g >= 0:
                    macro_checks.append(f"Fat: {food.fat_g}g")
                else:
                    macro_checks.append("⚠️ Fat missing")
                
                print(f"    Macros: {', '.join(macro_checks)}")
                
                # Check if all core macros present
                if (food.energy_kcal and food.protein_g is not None and 
                    food.carb_g is not None and food.fat_g is not None):
                    passed.append(f"Complete macros: {food.name}")
                else:
                    failed.append(f"Incomplete macros: {food.name}")
                
            else:
                print(f"  ⚠️  Not found: {food_name}")
                failed.append(f"Missing: {food_name}")
        
        # Test 3: Validate data quality
        print("\n📈 Data quality checks...")
        
        # Check for foods with complete nutrition
        complete = session.exec(
            select(FoodGeneric)
            .where(FoodGeneric.source == "cofid")
            .where(FoodGeneric.energy_kcal != None)
            .where(FoodGeneric.protein_g != None)
            .where(FoodGeneric.carb_g != None)
            .where(FoodGeneric.fat_g != None)
        ).all()
        
        completeness = len(complete) / len(total_count) * 100 if total_count else 0
        print(f"  Completeness: {completeness:.1f}% ({len(complete)}/{len(total_count)})")
        
        if completeness > 80:
            passed.append(f"Data completeness: {completeness:.1f}%")
        else:
            failed.append(f"Low completeness: {completeness:.1f}%")
    
    return passed, failed


def main():
    passed, failed = validate_cofid()
    
    print("\n" + "=" * 60)
    print("📋 CoFID VALIDATION SUMMARY")
    print("=" * 60)
    print(f"\n✅ PASSED: {len(passed)}")
    for item in passed:
        print(f"  • {item}")
    
    if failed:
        print(f"\n❌ FAILED: {len(failed)}")
        for item in failed:
            print(f"  • {item}")
        print("\n⚠️  RESULT: FAIL")
        sys.exit(1)
    else:
        print("\n✅ RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
