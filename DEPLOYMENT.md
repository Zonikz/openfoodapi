# GAINS Food Vision API - Deployment Guide

This guide covers deploying the GAINS Food Vision API to various platforms.

---

## 🚂 Railway (Recommended)

Railway provides the simplest deployment with automatic builds and free tier.

### Quick Deploy

1. **Fork/Clone this repository**
   ```bash
   git clone https://github.com/your-username/gains-food-vision-api.git
   cd gains-food-vision-api
   ```

2. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository
   - Railway will auto-detect Python and create the service

3. **Configure Build & Start Commands**
   
   In Railway dashboard → Settings:
   
   **Build Command**:
   ```bash
   pip install -r requirements.txt && python tools/download_model.py && python seeds/import_cofid.py && python seeds/import_off.py && python tools/build_label_map.py
   ```
   
   **Start Command**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Set Environment Variables**
   
   In Railway dashboard → Variables, add:
   
   ```
   DEBUG=false
   DEFAULT_COUNTRY=UK
   ENABLE_DETECTOR=false
   DATABASE_URL=sqlite:///./data/gains_food.db
   MAX_IMAGE_SIZE=1024
   TOP_K_PREDICTIONS=5
   TORCH_NUM_THREADS=4
   USE_GPU=false
   ```
   
   **Optional - API Key Protection**:
   ```
   API_KEY=your-secure-random-key-here
   ```
   (Generate with: `openssl rand -hex 32`)

5. **Deploy**
   - Railway will automatically build and deploy
   - First build takes ~5-10 minutes (model download + data import)
   - Get your public URL from Railway dashboard

### Post-Deploy Verification

```bash
# Check health
curl https://your-app.railway.app/health

# View API docs
open https://your-app.railway.app/docs

# Test classification (with API key if enabled)
curl -X POST "https://your-app.railway.app/api/classify?top_k=5" \
  -H "X-API-Key: your-key-here" \
  -F "file=@examples/food101/pizza.jpg"
```

**Expected Health Response**:
```json
{
  "status": "healthy",
  "classifier": "loaded",
  "data_counts": {
    "cofid_foods": 3000,
    "off_products": 15000
  },
  "label_map": {
    "coverage_percent": 100.0
  }
}
```

---

## 🎨 Render

Render offers a `render.yaml` blueprint for one-click deploys.

### Deploy Steps

1. **Push to GitHub** (if not already)
   ```bash
   git remote add origin https://github.com/your-username/gains-food-vision-api.git
   git push -u origin main
   ```

2. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Click "New" → "Blueprint"
   - Select your GitHub repository
   - Render will detect `render.yaml` and create the service

3. **Set Environment Variables** (in Render dashboard)
   
   Same as Railway:
   ```
   DEBUG=false
   DEFAULT_COUNTRY=UK
   ENABLE_DETECTOR=false
   DATABASE_URL=sqlite:///./data/gains_food.db
   ```
   
   Optional:
   ```
   API_KEY=your-secure-key
   ```

4. **Deploy**
   - First build: ~8-12 minutes
   - Public URL: `https://gains-food-vision-api.onrender.com`

### Render Free Tier Notes
- Service spins down after 15 min inactivity
- First request after spin-down takes ~30s (cold start)
- 750 hours/month free

---

## ✈️ Fly.io

Fly.io offers global edge deployment with persistent volumes.

### Deploy Steps

1. **Install Fly CLI**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Launch App**
   ```bash
   fly launch
   ```
   
   When prompted:
   - App name: `gains-food-vision-api` (or custom)
   - Region: `lhr` (London) for UK-first
   - Database: No
   - Redis: No

4. **Set Secrets** (optional API key)
   ```bash
   fly secrets set API_KEY=$(openssl rand -hex 32)
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Create Persistent Volume** (optional, for DB persistence)
   ```bash
   fly volumes create gains_data --region lhr --size 1
   ```
   
   Then uncomment the `[[mounts]]` section in `fly.toml`.

### Access Logs
```bash
fly logs
```

---

## 🔧 Replit (Dev/Demo)

Replit is great for demos and quick testing.

### Deploy Steps

1. **Create Replit Account** at [replit.com](https://replit.com)

2. **Import from GitHub**
   - Click "Create Repl"
   - Select "Import from GitHub"
   - Paste: `https://github.com/your-username/gains-food-vision-api`

3. **Run Setup**
   ```bash
   # Replit will auto-detect .replit and run setup
   # If not, manually run:
   bash scripts/setup_and_validate.sh
   ```

4. **Start Server**
   - Click "Run" button
   - Server starts on auto-assigned port
   - Public URL appears in Webview

5. **Access API**
   - Replit provides a public URL like `https://gains-food-vision-api.your-username.repl.co`
   - Add `/docs` for interactive documentation

### Replit Notes
- Free tier has CPU/RAM limits (inference may be slow)
- Repl goes to sleep after inactivity
- Good for demos, not production

---

## 🔐 API Key Authentication (Optional)

To restrict access, set the `API_KEY` environment variable on any platform.

### Generate Secure Key
```bash
openssl rand -hex 32
```

### Set in Platform
- **Railway**: Variables tab → Add `API_KEY`
- **Render**: Environment → Add `API_KEY`
- **Fly.io**: `fly secrets set API_KEY=your-key`
- **Replit**: Secrets tab → Add `API_KEY`

### Client Usage
```typescript
// React Native / Expo
const response = await fetch('https://your-api.com/api/classify', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-key-here'
  },
  body: formData
});
```

**Protected Routes**: All endpoints except `/`, `/health`, `/docs`  
**Unprotected Routes**: Health check and docs always public

---

## 🌍 Custom Domain (Optional)

### Railway
1. Settings → Networking → Custom Domain
2. Add your domain (e.g., `api.gains.app`)
3. Update DNS CNAME to point to Railway URL

### Render
1. Settings → Custom Domain
2. Follow DNS setup instructions

### Fly.io
```bash
fly certs add api.gains.app
```

---

## 📊 Monitoring & Logs

### Railway
- Deployments tab → View logs
- Metrics tab → CPU/Memory usage

### Render
- Logs tab (real-time)
- Metrics tab (requests, latency)

### Fly.io
```bash
fly logs
fly status
fly vm status
```

---

## 🚀 Performance Tips

### Free Tier Optimization
1. **Use Railway or Render** - Most generous free tiers for Python apps
2. **Keep ENABLE_DETECTOR=false** - Saves memory (~200MB)
3. **Set TORCH_NUM_THREADS=2** - On free tier, limit CPU threads
4. **Use SQLite** - No external DB needed

### Production Recommendations
1. **Upgrade to paid tier** for consistent uptime
2. **Add Redis caching** for frequently-requested foods
3. **Enable ENABLE_DETECTOR=true** if you need bounding boxes
4. **Use PostgreSQL** if you need multi-instance setup
5. **Add CDN** (Cloudflare) for image upload optimization

---

## 🐛 Troubleshooting

### Build Failures

**Issue**: Model download times out  
**Fix**: Increase build timeout in platform settings

**Issue**: CoFID import fails  
**Fix**: Check CSV download URL is accessible

### Runtime Issues

**Issue**: 503 Service Unavailable  
**Fix**: Model not loaded - check logs for download errors

**Issue**: Slow inference (>2s)  
**Fix**: Free tier CPU throttling - upgrade or reduce TORCH_NUM_THREADS

**Issue**: Database locked errors  
**Fix**: SQLite doesn't support concurrent writes - use PostgreSQL for multi-worker

### API Key Issues

**Issue**: 401 Unauthorized  
**Fix**: Include `X-API-Key` header in all requests (except `/health`, `/docs`)

---

## 🔄 CI/CD with GitHub Actions

The `.github/workflows/ci.yaml` runs tests on every push.

### Enable Railway Auto-Deploy

1. Get Railway API key from [railway.app/account/tokens](https://railway.app/account/tokens)
2. Add to GitHub Secrets:
   - `RAILWAY_API_KEY`
   - `RAILWAY_SERVICE_ID` (from Railway dashboard URL)
3. Push to `main` branch → Auto-deploys on test success

---

## 📞 Support

- API Issues: Open a GitHub issue
- Deployment Help: Check platform docs or Discord
- GAINS Integration: See `GAINS_INTEGRATION.md`

---

**Next**: See `GAINS_INTEGRATION.md` for React Native code examples.
