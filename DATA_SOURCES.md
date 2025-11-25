# Data Sources

The GAINS Food Vision API uses free, publicly available datasets to provide comprehensive food recognition and nutrition information.

## Primary Data Sources

### 1. CoFID (Composition of Foods Integrated Dataset)
**Source**: UK Government - Public Health England  
**License**: Open Government License v3.0  
**URL**: https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid

**Description**:
- Official UK government nutrition database
- Contains detailed macro and micronutrient data for generic foods
- Per-100g nutritional values
- Covers traditional UK foods and common ingredients

**Coverage**:
- 3,000+ generic food items
- Focus on UK-specific foods and preparations
- Primary source for generic food nutrition

**Import**: Automated via `seeds/import_cofid.py`

---

### 2. OpenFoodFacts (OFF)
**Source**: OpenFoodFacts.org - Collaborative open database  
**License**: Open Database License (ODbL) v1.0  
**URL**: https://world.openfoodfacts.org

**Description**:
- Crowd-sourced product database with barcode lookups
- Contains branded/packaged food products
- Includes NOVA scores, NutriScores, additives, and allergens
- Real product data with ingredients lists

**Coverage**:
- 10,000+ UK products (filtered subset)
- Barcode-based lookups
- Enrichment data (NOVA, NutriScore, additives, allergens)

**Import**: Automated via `seeds/import_off.py`

**Data Fields**:
- Barcode (EAN/GTIN)
- Product name and brand
- Ingredients list
- Nutrition per 100g
- NOVA group (1-4, processing level)
- NutriScore grade (A-E)
- Additives (E-numbers)
- Allergens

---

### 3. Food-101 Model
**Source**: ETH Zürich - Food-101 Dataset  
**License**: Research use  
**URL**: https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/

**Description**:
- 101 food classes for image classification
- ImageNet-pretrained ResNet-50 adapted for food recognition
- Used for plate image classification

**Model**:
- Architecture: ResNet-50
- Classes: 101 common food types
- Base weights: ImageNet
- Fine-tuning: Food-101 dataset (optional)

**Download**: Automated via `tools/download_model.py`

---

## Data Usage

### CoFID Usage
```python
# Generic foods like "chicken breast grilled"
result = find_canonical_food(session, "grilled chicken")
# Returns: CoFID entry with full nutrition profile
```

### OpenFoodFacts Usage
```python
# Barcode lookups for packaged foods
GET /api/barcode/5000159484695
# Returns: Heinz Beans with NOVA, NutriScore, additives
```

### Food-101 Usage
```python
# Image classification
POST /api/classify
# Returns: Top-K predicted food classes
# Maps to CoFID via label_map.json
```

---

## Data Pipeline

```
1. User captures food image
   ↓
2. Food-101 classifier → "chicken_curry" (label)
   ↓
3. label_map.json → maps to CoFID:12345
   ↓
4. CoFID database → nutrition data
   ↓
5. OFF enrichment → NOVA, NutriScore, additives
   ↓
6. GAINS scoring → final score
```

---

## Data Licensing

All data sources used are:
- ✅ **Free** to use
- ✅ **Open** licenses (ODbL, OGL)
- ✅ **No API keys** required
- ✅ **Self-hostable** (no external API calls)

### License Summary

| Source | License | Commercial Use | Attribution Required |
|--------|---------|----------------|---------------------|
| CoFID | OGL v3.0 | ✅ Yes | ✅ Yes |
| OpenFoodFacts | ODbL v1.0 | ✅ Yes | ✅ Yes |
| Food-101 | Research | ⚠️ Research only | ✅ Yes |

---

## Updating Data

### Update CoFID
```bash
# Delete existing data
rm -rf data/cofid.csv gains_food_vision.db

# Re-import
python seeds/import_cofid.py
```

### Update OpenFoodFacts
```bash
# Delete existing data
rm -rf data/off_en.jsonl* gains_food_vision.db

# Re-import (downloads latest dump)
python seeds/import_off.py
```

### Rebuild Label Map
```bash
# After updating CoFID/OFF
python tools/build_label_map.py
```

---

## Data Quality

### CoFID
- ✅ High quality (government source)
- ✅ Complete nutrition profiles
- ✅ Verified data
- ⚠️ UK-centric (limited international foods)

### OpenFoodFacts
- ✅ Real product data
- ✅ Rich enrichment (NOVA, NutriScore)
- ⚠️ Crowd-sourced (variable quality)
- ⚠️ Some products have incomplete nutrition

### Food-101
- ✅ Good for common foods
- ⚠️ Limited to 101 classes
- ⚠️ Model accuracy depends on training

---

## Attribution

When using this API, please credit:

**CoFID**:  
"Nutrition data from CoFID (Composition of Foods Integrated Dataset), © Crown copyright, licensed under the Open Government Licence v3.0"

**OpenFoodFacts**:  
"Product data from OpenFoodFacts.org, licensed under ODbL"

**Food-101**:  
"Food classification based on Food-101 dataset, ETH Zürich"

---

## Privacy & Data Storage

- All data is stored **locally** in SQLite
- **No external API calls** during inference
- **No user data** is sent to third parties
- Images are processed in-memory (not stored)
- GDPR-compliant (no personal data collected)
