# 🍽️ GAINS Food Vision API

Free, self-hosted food recognition + nutrition + GAINS scoring API for the GAINS mobile app.

**Zero paid APIs. Runs anywhere. Production-ready.**


---

## ⚡ Quick Start

### 🏠 Local (5 minutes)

```bash
git clone https://github.com/your-username/gains-food-vision-api.git
cd gains-food-vision-api
make setup-validate  # Downloads model, imports data, runs tests
source venv/bin/activate
uvicorn main:app --reload
```

**API ready**: http://localhost:8000 | **Docs**: http://localhost:8000/docs

### 🌍 Deploy Public (2 minutes)

**Railway** (recommended):
1. Fork this repo
2. [Railway](https://railway.app) → New Project → Deploy from GitHub
3. Set build: `pip install -r requirements.txt && make setup-validate`
4. Set start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `DEFAULT_COUNTRY=UK`, `ENABLE_DETECTOR=false`

**Public URL**: `https://your-app.railway.app`

**Other platforms**: See [DEPLOYMENT.md](./DEPLOYMENT.md) for Render, Fly.io, Replit

**Quickstart guide**: [QUICKSTART.md](./QUICKSTART.md)

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

If you prefer step-by-step or need to troubleshoot:

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

# OpenFoodFacts - Quick sample (15k UK products)
python seeds/import_off.py

# OpenFoodFacts - Full UK import (150k+ products, streaming)
# First, download the dump (10+ GB, takes 10-30 min)
mkdir -p seeds/data
curl -L -o seeds/data/off.jsonl.gz https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz

# Then import (streams line-by-line, no RAM spike)
python -m seeds.import_off --file seeds/data/off.jsonl.gz --country UK --limit 0

# Build label map (101 Food-101 classes → CoFID foods)
python tools/build_label_map.py
```

**Docker users**: See "Docker Import" section below.

### 4. Run Server

```bash
# Local development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Server starts at `http://localhost:8000`

**Docs:** `http://localhost:8000/docs`

---

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

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start
docker compose up -d --build

# Check health
curl http://localhost:8000/health

# View logs
docker compose logs -f
```

### Full UK Import (150k+ products)

For production with complete OpenFoodFacts data:

```bash
# 1. Download OFF dump on host (10+ GB, avoids container disk issues)
mkdir -p seeds/data
curl -L -o seeds/data/off.jsonl.gz https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz

# 2. Import 12k UK products (quick smoke test)
docker compose run --rm api \
  python -m seeds.import_off --file /app/seeds/data/off.jsonl.gz --country UK --limit 12000

# 3. Import ALL UK products (150k+, takes ~30-60 min on 4GB VPS)
docker compose run --rm api \
  python -m seeds.import_off --file /app/seeds/data/off.jsonl.gz --country UK --limit 0

# 4. Build label map
docker compose run --rm api python -m tools.build_label_map

# 5. Health check
curl http://localhost:8000/api/health
```

**Note**: Use `docker compose exec -T` (not `exec`) when piping heredocs to avoid TTY errors.

### Troubleshooting

**Disk full during build**:
```bash
docker system prune -af
docker compose build --no-cache
```

**Container can't see seeds/data**:
- Check `docker-compose.yml` has `./seeds/data:/app/seeds/data:ro` volume mount
- Ensure seeds/data/ is NOT in `.dockerignore`

**OFF download blocked**:
- Download on host first, then use `--file` flag
- Alternative URL: `https://static.openfoodfacts.org/data/openfoodfacts-products-latest.jsonl.gz`

**UNIQUE constraint errors on re-run**:
- Handled automatically via IntegrityError catching
- Duplicates are skipped, not inserted

**MemoryError on 4GB VPS**:
- Use `--file` flag for streaming import (no full file load)
- Reduce batch size: `OFF_BATCH_SIZE=250` in docker-compose.yml

---

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
- `OFF_BATCH_SIZE=500` - Batch size for OFF import (reduce if low RAM)
- `TORCH_NUM_THREADS=4` - CPU threads for inference

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

Quick example for React Native / Expo:

```typescript
// .env
EXPO_PUBLIC_GAINS_API_BASE_URL=https://your-app.railway.app
EXPO_PUBLIC_GAINS_API_KEY=your-key-here  # if using API key auth

// 1. Classify photo
const formData = new FormData();
formData.append('file', {
  uri: photoUri,
  type: 'image/jpeg',
  name: 'photo.jpg'
});

const predictions = await fetch(
  `${process.env.EXPO_PUBLIC_GAINS_API_BASE_URL}/api/classify?top_k=5`,
  {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.EXPO_PUBLIC_GAINS_API_KEY  // if enabled
    },
    body: formData
  }
).then(r => r.json());

// 2. User selects prediction → Map to food → Calculate score
// See GAINS_INTEGRATION.md for complete examples
```

**Full integration guide**: [GAINS_INTEGRATION.md](./GAINS_INTEGRATION.md)

## 🚀 Public Deployment

Deploy in minutes to Railway, Render, Fly.io, or Replit.

### Railway (Recommended - 2 minutes)

1. **Connect GitHub**
   - Fork this repo
   - Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub

2. **Configure**
   ```
   Build: pip install -r requirements.txt && make setup-validate
   Start: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables**
   ```
   DEFAULT_COUNTRY=UK
   ENABLE_DETECTOR=false
   DATABASE_URL=sqlite:///./data/gains_food.db
   
   # Optional API Key Protection
   API_KEY=your-secure-key-here
   ```

4. **Deploy**
   - First build: ~5-10 minutes (downloads model + imports data)
   - Public URL: `https://your-app.railway.app`

**Smoke Test**:
```bash
# Check health
curl https://your-app.railway.app/health

# Test classification (with API key if enabled)
curl -X POST "https://your-app.railway.app/api/classify?top_k=5" \
  -H "X-API-Key: your-key" \
  -F "file=@examples/pizza.jpg"

# View docs
open https://your-app.railway.app/docs
```

### Other Platforms

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for complete guides:
- **Render**: One-click with `render.yaml`
- **Fly.io**: Global edge deployment
- **Replit**: Quick demos

---

## 🔐 Optional API Key Auth

Protect your API by setting the `API_KEY` environment variable:

```bash
# Generate secure key
openssl rand -hex 32

# Set in Railway/Render/Fly.io
API_KEY=your-generated-key
```

All endpoints (except `/health` and `/docs`) will require the `X-API-Key` header.

**Client usage**:
```typescript
// React Native
fetch('https://your-api.com/api/classify', {
  headers: { 'X-API-Key': 'your-key' }
})
```

---

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
