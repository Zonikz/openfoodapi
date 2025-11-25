# GAINS Food Vision API - Quick Start

Get the API running in 5 minutes locally, or deploy publicly in 2 minutes.

---

## 🏠 Local Development (5 minutes)

### Prerequisites
- Python 3.11+
- 2 GB RAM
- 500 MB disk space

### One-Command Setup

```bash
# Clone
git clone https://github.com/your-username/gains-food-vision-api.git
cd gains-food-vision-api

# Setup everything (venv, deps, model, data, tests)
make setup-validate
```

This command will:
1. ✅ Create virtual environment
2. ✅ Install dependencies
3. ✅ Download Food-101 model (~100MB)
4. ✅ Import CoFID data (3,000+ UK foods)
5. ✅ Import OpenFoodFacts data (15,000 UK products)
6. ✅ Build label map (101/101 classes)
7. ✅ Run validation tests

**First run takes ~5-10 minutes.** Subsequent runs are instant.

### Start Server

```bash
# Activate venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Start API
uvicorn main:app --reload
```

Server running at: **http://localhost:8000**

### Test It

```bash
# Health check
curl http://localhost:8000/health

# API docs (interactive)
open http://localhost:8000/docs

# Classify food
curl -X POST "http://localhost:8000/api/classify?top_k=5" \
  -F "file=@examples/pizza.jpg"
```

**Expected response**:
```json
{
  "model": "food101-resnet50",
  "top_k": [
    {"label": "pizza", "score": 0.89},
    {"label": "flatbread", "score": 0.06}
  ],
  "inference_ms": 185
}
```

---

## 🐳 Docker Deployment (4GB VPS)

### Quick Start

```bash
# Build and run
docker compose up -d --build

# Check health
curl http://localhost:8000/health
```

### Full UK OFF Import (150k+ products)

For production with complete OpenFoodFacts data:

```bash
# 1. Download OFF dump on host (avoids container disk/RAM issues)
mkdir -p seeds/data
curl -L -o seeds/data/off.jsonl.gz \
  https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz

# 2. Import 12k UK (smoke test, ~2-3 min)
docker compose run --rm api \
  python -m seeds.import_off --file /app/seeds/data/off.jsonl.gz --country UK --limit 12000

# 3. Import ALL UK (150k+, ~30-60 min on 4GB VPS, streams line-by-line)
docker compose run --rm api \
  python -m seeds.import_off --file /app/seeds/data/off.jsonl.gz --country UK --limit 0

# 4. Build label map
docker compose run --rm api python -m tools.build_label_map

# 5. Verify
curl http://localhost:8000/api/health | jq '.data_counts.off_products'
# Expected: 150000+
```

**Benefits of streaming import**:
- ✅ Works on 4GB VPS (no MemoryError)
- ✅ Handles duplicates automatically (IntegrityError)
- ✅ Resume-safe (re-run won't duplicate data)
- ✅ Batch inserts for speed (500 products/batch)

---

## 🌍 Public Deployment (2 minutes)

### Railway (Recommended)

1. **Fork this repo** on GitHub

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `gains-food-vision-api`

3. **Configure** (in Railway dashboard)
   
   **Build Command**:
   ```
   pip install -r requirements.txt && make setup-validate
   ```
   
   **Start Command**:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
   
   **Environment Variables**:
   ```
   DEFAULT_COUNTRY=UK
   ENABLE_DETECTOR=false
   DATABASE_URL=sqlite:///./data/gains_food.db
   ```
   
   **Optional - API Key** (for protection):
   ```
   API_KEY=<generate with: openssl rand -hex 32>
   ```

4. **Deploy**
   - First build: ~5-10 minutes
   - Get your public URL: `https://gains-food-vision-api-production.up.railway.app`

### Verify Deployment

```bash
# Set your Railway URL
export API_URL="https://your-app.railway.app"

# Check health
curl $API_URL/health

# Expected: "status": "healthy", "classifier": "loaded", 3k+ CoFID, 15k+ OFF

# View docs
open $API_URL/docs

# Test classify (with API key if enabled)
curl -X POST "$API_URL/api/classify?top_k=5" \
  -H "X-API-Key: your-key" \
  -F "file=@examples/pizza.jpg"
```

---

## 📱 Connect GAINS Mobile App

### Set Environment Variables

```bash
# .env in your Expo project
EXPO_PUBLIC_GAINS_API_BASE_URL=https://your-app.railway.app
EXPO_PUBLIC_GAINS_API_KEY=your-key-here  # if using API key auth
```

### Example Usage

```typescript
// services/gainsApi.ts
const API_URL = process.env.EXPO_PUBLIC_GAINS_API_BASE_URL;
const API_KEY = process.env.EXPO_PUBLIC_GAINS_API_KEY;

// Classify food
const formData = new FormData();
formData.append('file', {
  uri: photoUri,
  type: 'image/jpeg',
  name: 'food.jpg'
});

const response = await fetch(`${API_URL}/api/classify?top_k=5`, {
  method: 'POST',
  headers: {
    ...(API_KEY && { 'X-API-Key': API_KEY })
  },
  body: formData
});

const result = await response.json();
// { model: "food101-resnet50", top_k: [...], inference_ms: 185 }
```

**Full integration guide**: [GAINS_INTEGRATION.md](./GAINS_INTEGRATION.md)

---

## ⚡ Architecture Flow

```
📸 User takes photo in GAINS app
    ↓
🔄 POST /api/classify → Top 5 predictions
    ↓
👆 User selects prediction
    ↓
🗺️  POST /api/map-to-food → Canonical food + nutrition
    ↓
⚖️  User estimates portion (on-device)
    ↓
🏆 POST /api/score/gains → GAINS score (A-F)
    ↓
📊 Display score in app
```

---

## 🛠️ Other Deployment Options

- **Render**: `render.yaml` included → One-click blueprint deploy
- **Fly.io**: Global edge deployment with `fly.toml`
- **Replit**: `.replit` config for instant demo/dev environment

Full guides: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🔐 Security

### API Key Protection (Optional)

Restrict access by setting `API_KEY` environment variable:

```bash
# Generate secure key
openssl rand -hex 32

# Set in Railway/Render/Fly.io
API_KEY=<your-generated-key>
```

All endpoints require `X-API-Key` header (except `/health` and `/docs`).

### CORS

Default: `*` (all origins) for Expo/React Native development.

**Production**: Tighten in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gains.app", "https://staging.gains.app"],
    ...
)
```

---

## 📊 Expected Performance

- **Inference**: ~150-250ms (CPU, Food-101 ResNet-50)
- **Database queries**: <50ms
- **Throughput**: ~50 req/s (single worker)

Free tier platforms (Railway, Render) will be slower but functional.

---

## 🚨 Troubleshooting

### Local Setup Issues

**"Model not found"**
```bash
python tools/download_model.py
```

**"Database empty"**
```bash
python seeds/import_cofid.py
python seeds/import_off.py
python tools/build_label_map.py
```

**"Tests failing"**
```bash
pytest tests/ -v
```

### Docker Issues

**"Disk full during build"**
```bash
docker system prune -af
docker compose build --no-cache
```

**"Container can't see seeds/data"**
- Check volume mount in `docker-compose.yml`: `./seeds/data:/app/seeds/data:ro`
- Download OFF dump on host, not in container

**"MemoryError on OFF import"**
- Use `--file` flag for streaming import (no full file load)
- Reduce batch size: `OFF_BATCH_SIZE=250` in docker-compose.yml
- Ensure you're using the new streaming importer (not old version)

**"TTY error with heredocs"**
```bash
# Use -T flag
docker compose exec -T api python ...
```

**"UNIQUE constraint errors"**
- Already handled automatically (duplicates skipped)
- Safe to re-run import

### Deployment Issues

**"503 Service Unavailable"**
- Check health: `curl https://your-app.railway.app/health`
- If `classifier: "not_loaded"`, check build logs for model download errors

**"Build timeout"**
- Railway: Increase timeout in settings
- Render: Upgrade plan or reduce OFF import size

**"Slow inference (>2s)"**
- Free tier CPU throttling
- Set `TORCH_NUM_THREADS=2` to reduce resource usage

**"OFF download blocked"**
- Use alternate URL: `https://static.openfoodfacts.org/data/openfoodfacts-products-latest.jsonl.gz`
- Or download on host and use `--file` flag

---

## 📚 Next Steps

1. **Read API docs**: http://localhost:8000/docs
2. **Integration guide**: [GAINS_INTEGRATION.md](./GAINS_INTEGRATION.md)
3. **Deployment guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
4. **Data sources**: [DATA_SOURCES.md](./DATA_SOURCES.md)

---

**Questions?** Open an issue or check the [full README](./README.md).
