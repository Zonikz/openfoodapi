"""Validate OpenFoodFacts database import"""
import sys
from pathlib import Path
from sqlmodel import Session, select, func
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine
from app.data.schema import FoodOFF


def validate_off():
    """Validate OFF data import"""
    print("=" * 60)
    print("🧪 VALIDATING OPENFOODFACTS DATABASE")
    print("=" * 60)
    
    passed = []
    failed = []
    
    with Session(engine) as session:
        # Test 1: Check table exists and has data
        total_count = session.exec(select(func.count(FoodOFF.id))).one()
        
        if total_count > 0:
            print(f"✅ OFF table has {total_count} entries")
            passed.append(f"OFF entries: {total_count}")
        else:
            print("❌ OFF table is empty")
            print("   Run: python seeds/import_off.py")
            failed.append("No OFF entries found")
            return passed, failed
        
        # Test 2: Random sampling
        print("\n📊 Sampling random products...")
        
        # Get random sample
        all_products = session.exec(select(FoodOFF)).all()
        sample_size = min(10, len(all_products))
        sample = random.sample(all_products, sample_size)
        
        enrichment_scores = {
            "has_nutrition": 0,
            "has_nova": 0,
            "has_nutriscore": 0,
            "has_additives": 0,
            "has_brands": 0,
            "has_categories": 0
        }
        
        for product in sample:
            print(f"\n  Barcode: {product.code}")
            print(f"    Name: {product.product_name}")
            
            # Check nutrition
            if (product.energy_kcal and product.protein_g is not None and 
                product.carb_g is not None and product.fat_g is not None):
                print(f"    ✅ Nutrition: {product.energy_kcal} kcal, P:{product.protein_g}g, C:{product.carb_g}g, F:{product.fat_g}g")
                enrichment_scores["has_nutrition"] += 1
            else:
                print(f"    ⚠️  Incomplete nutrition")
            
            # Check NOVA
            if product.nova_group:
                print(f"    ✅ NOVA: {product.nova_group}")
                enrichment_scores["has_nova"] += 1
            else:
                print(f"    ⚠️  NOVA missing")
            
            # Check NutriScore
            if product.nutriscore_grade:
                print(f"    ✅ NutriScore: {product.nutriscore_grade}")
                enrichment_scores["has_nutriscore"] += 1
            else:
                print(f"    ⚠️  NutriScore missing")
            
            # Check additives
            if product.additives:
                print(f"    ✅ Additives: {product.additives[:50]}...")
                enrichment_scores["has_additives"] += 1
            else:
                print(f"    ⚠️  Additives missing")
            
            # Check brands
            if product.brands:
                print(f"    ✅ Brands: {product.brands}")
                enrichment_scores["has_brands"] += 1
            else:
                print(f"    ⚠️  Brands missing")
            
            # Check categories
            if product.categories:
                print(f"    ✅ Categories: {product.categories[:50]}...")
                enrichment_scores["has_categories"] += 1
            else:
                print(f"    ⚠️  Categories missing")
        
        # Test 3: Calculate enrichment quality
        print("\n📈 Enrichment quality:")
        for key, count in enrichment_scores.items():
            percentage = (count / sample_size) * 100
            print(f"  {key}: {percentage:.1f}% ({count}/{sample_size})")
            
            if percentage >= 50:  # At least 50% coverage
                passed.append(f"{key}: {percentage:.1f}%")
            else:
                failed.append(f"Low {key}: {percentage:.1f}%")
        
        # Test 4: Validate specific known barcodes
        print("\n🔍 Testing known barcodes...")
        known_barcodes = [
            "5000159484695",  # Heinz Beans
            "3017620422003",  # Nutella
            "5449000000996",  # Coca-Cola
        ]
        
        for barcode in known_barcodes:
            product = session.exec(
                select(FoodOFF).where(FoodOFF.code == barcode)
            ).first()
            
            if product:
                print(f"  ✅ Found: {barcode} - {product.product_name}")
                passed.append(f"Known barcode: {barcode}")
            else:
                print(f"  ⚠️  Not found: {barcode}")
                failed.append(f"Missing known barcode: {barcode}")
    
    return passed, failed


def main():
    passed, failed = validate_off()
    
    print("\n" + "=" * 60)
    print("📋 OFF VALIDATION SUMMARY")
    print("=" * 60)
    print(f"\n✅ PASSED: {len(passed)}")
    for item in passed:
        print(f"  • {item}")
    
    if failed:
        print(f"\n❌ FAILED: {len(failed)}")
        for item in failed:
            print(f"  • {item}")
        print("\n⚠️  RESULT: FAIL (Expected - requires OFF data import)")
        sys.exit(1)
    else:
        print("\n✅ RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
