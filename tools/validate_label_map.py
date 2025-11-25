"""Validate label mapping coverage"""
import sys
from pathlib import Path
from sqlmodel import Session, select
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.db import engine
from app.data.schema import LabelMapping, FoodGeneric, FoodOFF
from app.models.vision_classifier import FOOD101_CLASSES


def validate_label_map():
    """Validate label mapping"""
    print("=" * 60)
    print("🧪 VALIDATING LABEL MAPPING")
    print("=" * 60)
    
    passed = []
    failed = []
    
    # Test 1: Check label_map.json exists
    label_map_path = Path("app/mapping/label_map.json")
    if label_map_path.exists():
        print(f"✅ label_map.json exists")
        passed.append("label_map.json exists")
        
        with open(label_map_path) as f:
            label_map = json.load(f)
    else:
        print(f"❌ label_map.json not found")
        print("   Run: python tools/build_label_map.py")
        failed.append("label_map.json missing")
        return passed, failed
    
    # Test 2: Check coverage
    total_classes = len(FOOD101_CLASSES)
    mapped_classes = len(label_map)
    coverage = (mapped_classes / total_classes) * 100
    
    print(f"\n📊 Coverage: {coverage:.1f}% ({mapped_classes}/{total_classes})")
    
    if coverage >= 80:
        print("✅ Good coverage")
        passed.append(f"Coverage: {coverage:.1f}%")
    else:
        print(f"⚠️  Low coverage: {coverage:.1f}%")
        failed.append(f"Low coverage: {coverage:.1f}%")
    
    # Test 3: Check for missing classes
    missing = [cls for cls in FOOD101_CLASSES if cls not in label_map]
    if missing:
        print(f"\n⚠️  Missing {len(missing)} classes:")
        for cls in missing[:10]:  # Show first 10
            print(f"    • {cls}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")
        failed.append(f"Missing {len(missing)} classes")
    else:
        print("\n✅ All Food-101 classes mapped")
        passed.append("Complete coverage")
    
    # Test 4: Validate canonical IDs exist
    print("\n🔍 Validating canonical references...")
    
    with Session(engine) as session:
        orphaned = []
        valid = 0
        
        for food_class, mapping in label_map.items():
            canonical_id = mapping.get("canonical_id")
            source = mapping.get("source", "cofid")
            
            if not canonical_id:
                orphaned.append(f"{food_class}: no canonical_id")
                continue
            
            # Check if canonical food exists
            if source == "off":
                exists = session.exec(
                    select(FoodOFF).where(FoodOFF.code == canonical_id)
                ).first()
            else:
                exists = session.exec(
                    select(FoodGeneric).where(FoodGeneric.source_id == canonical_id)
                ).first()
            
            if exists:
                valid += 1
            else:
                orphaned.append(f"{food_class}: {canonical_id} not found")
        
        orphan_rate = (len(orphaned) / mapped_classes) * 100 if mapped_classes > 0 else 0
        
        print(f"  Valid references: {valid}/{mapped_classes} ({100 - orphan_rate:.1f}%)")
        
        if orphan_rate < 20:
            passed.append(f"Valid references: {100 - orphan_rate:.1f}%")
        else:
            failed.append(f"High orphan rate: {orphan_rate:.1f}%")
        
        if orphaned:
            print(f"\n  ⚠️  {len(orphaned)} orphaned mappings:")
            for item in orphaned[:5]:  # Show first 5
                print(f"    • {item}")
            if len(orphaned) > 5:
                print(f"    ... and {len(orphaned) - 5} more")
    
    # Test 5: Check database table
    with Session(engine) as session:
        db_mappings = session.exec(select(LabelMapping)).all()
        
        if db_mappings:
            print(f"\n✅ LabelMapping table has {len(db_mappings)} entries")
            passed.append(f"DB mappings: {len(db_mappings)}")
        else:
            print(f"\n⚠️  LabelMapping table is empty")
            print("   Run: python tools/build_label_map.py")
            failed.append("LabelMapping table empty")
    
    return passed, failed


def main():
    passed, failed = validate_label_map()
    
    print("\n" + "=" * 60)
    print("📋 LABEL MAP VALIDATION SUMMARY")
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
