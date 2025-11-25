# 🍽️ GAINS Food Vision API

Free, self-hosted food recognition + nutrition + GAINS scoring API for the GAINS mobile app.

**Zero paid APIs. Runs anywhere. Production-ready.**

---

## ⚡ 5-Minute Quick Start

**One command sets up everything:**

```bash
make setup-validate
```

This will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Download Food-101 model weights (~100MB)
- ✅ Import UK CoFID nutrition data (3,000+ foods)
- ✅ Import OpenFoodFacts products (15,000 items)
- ✅ Build label map (100% coverage, all 101 classes)
- ✅ Run validation tests

**Then start the server:**

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Start server
uvicorn main:app --reload
```

**API ready at:** `http://localhost:8000` | **Docs:** `http://localhost:8000/docs`

---

## 🎯 Features

- 🧠 **Food-101 Classifier** - ResNet-50, CPU-optimized, ~200ms inference
- 🔍 **YOLOv8 Detector** - Optional bounding boxes (feature-flagged)
- 📊 **UK CoFID** - 3,000+ government nutrition database foods
- 🌍 **OpenFoodFacts** - 15,000+ UK products with barcodes
- 🏆 **GAINS Scoring** - Protein density, carb quality, processing, transparency
- 🔎 **Fuzzy Search** - RapidFuzz-powered typo-tolerant search
- 📷 **Barcode Lookup** - GTIN → nutrition + enrichment
- 🗺️ **Label Mapping** - 100% coverage (all 101 Food-101 classes)
- 🚀 **Zero Config** - Works on Replit, Render, Railway, localhost
- 🔒 **Privacy-First** - All data stored locally, no external API calls

---

## 📦 Manual Setup (Alternative)

If you prefer step-by-step setup:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Model Weights

```bash
python tools/download_model.py
```

Downloads Food-101 ResNet-50 model (~100MB) with auto-retry.

### 3. Import Data

```bash
# UK CoFID (3,000+ generic foods)
python seeds/import_cofid.py

# OpenFoodFacts (15,000 UK products)
python seeds/import_off.py

# Build label map (101 Food-101 classes → CoFID foods)
python tools/build_label_map.py
```

### 4. Run Server

```bash
# Local development
uvicorn main:app --reload

# Production (Replit/Render/Railway)
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Server starts at `http://localhost:8000`

**Docs:** `http://localhost:8000/docs`

## 📡 API Endpoints

### 🧠 Vision

#### POST `/api/classify`

Classify food from image.

```bash
curl -X POST "http://localhost:8000/api/classify?top_k=5" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@examples/chicken_curry.jpg"
```

Response:
```json
{
  "model": "food101-resnet50",
  "top_k": [
    {"label": "chicken_curry", "score": 0.78},
    {"label": "butter_chicken", "score": 0.14},
    {"label": "currywurst", "score": 0.04}
  ],
  "inference_ms": 42
}
```

#### POST `/api/detect-foods` (optional)

Return bounding boxes + labels.

```bash
curl -X POST "http://localhost:8000/api/detect-foods" \
  -F "file=@examples/plate.jpg"
```

### 🗺️ Mapping

#### POST `/api/map-to-food`

Map prediction → canonical food.

```bash
curl -X POST "http://localhost:8000/api/map-to-food" \
  -H "Content-Type: application/json" \
  -d '{"query": "chicken_curry", "country": "UK"}'
```

Response:
```json
{
  "canonical_name": "Chicken curry",
  "source": "cofid",
  "source_id": "COFID:12345",
  "per_100g": {
    "energy_kcal": 148,
    "protein_g": 16.5,
    "carb_g": 5.8,
    "fat_g": 6.1,
    "fiber_g": 1.2,
    "sugar_g": 2.1,
    "saturated_fat_g": 1.8,
    "sodium_mg": 380
  },
  "servings": [
    {"name": "100 g", "grams": 100},
    {"name": "1 portion", "grams": 250}
  ],
  "enrichment": {
    "nova": 3,
    "nutriscore": "C",
    "additives": ["E412"]
  }
}
```

### 📷 Barcode

#### GET `/api/barcode/{gtin}`

Lookup product by barcode.

```bash
curl "http://localhost:8000/api/barcode/5000159407236"
```

### 🔎 Search

#### GET `/api/foods/search`

Fuzzy search foods.

```bash
curl "http://localhost:8000/api/foods/search?q=chicken&limit=10&country=UK"
```

### 🏆 GAINS Scoring

#### POST `/api/score/gains`

Calculate GAINS score.

```bash
curl -X POST "http://localhost:8000/api/score/gains" \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_id": "COFID:12345",
    "grams": 250
  }'
```

Response:
```json
{
  "macros": {
    "energy_kcal": 370,
    "protein_g": 41.25,
    "carb_g": 14.5,
    "fat_g": 15.25
  },
  "score": {
    "protein_density": 0.82,
    "carb_quality": 0.64,
    "fat_quality": 0.58,
    "processing": 0.35,
    "transparency": 0.76,
    "overall": 0.63
  },
  "grade": "B"
}
```

## 🔧 Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings:

- `ENABLE_DETECTOR=false` - Enable YOLOv8 detector
- `TOP_K_PREDICTIONS=5` - Number of predictions to return
- `MODEL_NAME=food101-resnet50` - Model architecture
- `DATABASE_URL=sqlite:///./data/gains_food.db` - Database path

## 🗄️ Database Schema

```
foods_generic   # CoFID, USDA generic foods
foods_off       # OpenFoodFacts products
label_map       # Food-101 → canonical food
aliases         # Alternative names → canonical food
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📊 Benchmarking

```bash
python tools/benchmark.py
```

Tests inference speed, accuracy, and throughput.

## 🏗️ Architecture

```
Camera (GAINS App)
    ↓
POST /classify
    ↓
Food-101 Classifier → Top-K predictions
    ↓
User selects prediction
    ↓
POST /map-to-food
    ↓
Label Map → CoFID/OFF/USDA
    ↓
Canonical Food + Nutrition
    ↓
User estimates portion
    ↓
POST /score/gains
    ↓
GAINS Score (A-F)
    ↓
Display in GAINS App
```

## 🌍 Data Sources

### CoFID (UK)
Government nutrition database. High-quality, generic foods.

**Download:** https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid

### OpenFoodFacts
2M+ products, crowdsourced. NOVA, NutriScore, additives.

**Download:** https://world.openfoodfacts.org/data

### USDA FDC (Optional)
US government database for fallback.

**Download:** https://fdc.nal.usda.gov/download-datasets.html

## 🎯 GAINS App Integration

From GAINS mobile app:

```typescript
// 1. Classify photo
const formData = new FormData();
formData.append('file', {
  uri: photoUri,
  type: 'image/jpeg',
  name: 'photo.jpg'
});

const predictions = await fetch('https://api.gains.app/api/classify?top_k=5', {
  method: 'POST',
  body: formData
}).then(r => r.json());

// 2. User selects prediction
const selectedFood = predictions.top_k[0].label;

// 3. Map to canonical food
const food = await fetch('https://api.gains.app/api/map-to-food', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: selectedFood,
    country: 'UK'
  })
}).then(r => r.json());

// 4. User estimates portion (on-device)
const portionGrams = 250;

// 5. Calculate GAINS score
const score = await fetch('https://api.gains.app/api/score/gains', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    canonical_id: food.source_id,
    grams: portionGrams
  })
}).then(r => r.json());

// 6. Display score in UI
console.log(`GAINS Score: ${score.score.overall} (${score.grade})`);
```

## 🚀 Deployment

### Replit

1. Create new Repl
2. Upload code
3. `pip install -r requirements.txt`
4. `python tools/download_model.py`
5. `python seeds/import_cofid.py`
6. Run `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Render / Railway

1. Connect GitHub repo
2. Set build command: `pip install -r requirements.txt && python tools/download_model.py && python seeds/import_cofid.py`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy

## 📈 Performance

- **Inference:** ~150-250ms (CPU)
- **Top-1 Accuracy:** ~75% (Food-101)
- **Database:** <100ms queries
- **Throughput:** ~50 req/s (single worker)

## 🤝 Contributing

PRs welcome! Focus areas:

- New data sources
- Model improvements
- Faster inference
- Better label mapping
- GAINS scoring refinements

## 📄 License

MIT

## 🙏 Acknowledgments

- Food-101 dataset
- UK CoFID
- OpenFoodFacts
- PyTorch / FastAPI teams

---

**Questions?** Open an issue or contact GAINS team.
