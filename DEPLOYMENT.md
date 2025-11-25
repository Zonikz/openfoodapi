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

### Full UK Import (Optional - 150k+ Products)

For production with complete OpenFoodFacts data:

```bash
# Note: Railway has persistent storage, so data survives redeploys

# 1. SSH into Railway container (via Railway CLI)
railway shell

# 2. Download OFF dump (10+ GB, takes 10-30 min)
mkdir -p seeds/data
curl -L -o seeds/data/off.jsonl.gz \
  https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz

# 3. Import ALL UK products (streaming, ~30-60 min)
python -m seeds.import_off --file seeds/data/off.jsonl.gz --country UK --limit 0

# 4. Build label map
python -m tools.build_label_map

# 5. Verify
curl http://localhost:8000/api/health | jq '.data_counts.off_products'
# Expected: 150000+
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

## 🔄 Automatic Daily Updates (VPS Production)

For production VPS deployments, keep your OpenFoodFacts data fresh with automated daily updates.

### Setup Systemd Timer

**Step 1: Make scripts executable**
```bash
chmod +x scripts/update_off.sh scripts/update_cofid.sh scripts/update_all.sh
```

**Step 2: Create systemd service**
```bash
sudo tee /etc/systemd/system/gains-data-update.service > /dev/null <<'EOF'
[Unit]
Description=GAINS Food Data Update
Wants=docker.service
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/root/openfoodapi
ExecStart=/bin/bash -lc 'git pull --rebase || true && docker compose up -d && bash scripts/update_all.sh'
TimeoutStartSec=7200
EOF
```

**Step 3: Create systemd timer**
```bash
sudo tee /etc/systemd/system/gains-data-update.timer > /dev/null <<'EOF'
[Unit]
Description=Run GAINS data update daily at 03:30

[Timer]
OnCalendar=*-*-* 03:30:00
RandomizedDelaySec=900
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

**Step 4: Enable and start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gains-data-update.timer
```

**Step 5: Verify**
```bash
systemctl list-timers | grep gains-data-update
```

### What It Does

The automated update:
1. **Downloads** latest OFF dump (~10 GB)
2. **Streams import** (150k+ UK products, zero RAM spike)
3. **Rebuilds label map** for 101 Food-101 classes
4. **Vacuums database** to reclaim space
5. **Runs health check** to verify success

### Manual Triggers

**Test the update**:
```bash
sudo systemctl start gains-data-update.service
journalctl -u gains-data-update -f
```

**View logs**:
```bash
# Last run
journalctl -u gains-data-update --since today

# Follow live
journalctl -u gains-data-update -f

# Last 100 lines
journalctl -u gains-data-update -n 100
```

**Disable timer** (if needed):
```bash
sudo systemctl stop gains-data-update.timer
sudo systemctl disable gains-data-update.timer
```

### Update Scripts

The repo includes three automation scripts:

**`scripts/update_off.sh`** - OpenFoodFacts update
- Downloads latest OFF dump
- Streams import (all UK products)
- Rebuilds label map
- Vacuums database

**`scripts/update_cofid.sh`** - CoFID update
- Re-imports CoFID data
- Rebuilds label map

**`scripts/update_all.sh`** - Complete update
- Runs OFF update
- Optionally runs CoFID update
- Health check

### Customization

**Change schedule**:
Edit `/etc/systemd/system/gains-data-update.timer`:
```ini
# Every Sunday at 2 AM
OnCalendar=Sun *-*-* 02:00:00

# Twice daily (3:30 AM and 3:30 PM)
OnCalendar=*-*-* 03:30:00
OnCalendar=*-*-* 15:30:00
```

**Change working directory**:
Edit `/etc/systemd/system/gains-data-update.service`:
```ini
WorkingDirectory=/your/custom/path/gains-food-vision-api
```

**Update specific country**:
Edit `scripts/update_off.sh`, change:
```bash
--country UK
```
to:
```bash
--country US
```

### VPS Resource Notes

- **Disk**: ~15 GB required (dump + database + temp)
- **RAM**: 4 GB minimum (streaming import uses <500 MB)
- **Duration**: 30-90 minutes (network + processing)
- **Bandwidth**: ~10 GB download per run

**Tip**: Schedule during low-traffic hours (3-5 AM).

---

## 🐛 Troubleshooting

### Build Failures

**Issue**: Model download times out  
**Fix**: Increase build timeout in platform settings

**Issue**: CoFID import fails  
**Fix**: Check CSV download URL is accessible

**Issue**: Disk full during build  
**Fix**: Ensure `.dockerignore` excludes `seeds/data/`, `data/`, `models/`, `.git/`

### Runtime Issues

**Issue**: 503 Service Unavailable  
**Fix**: Model not loaded - check logs for download errors

**Issue**: Slow inference (>2s)  
**Fix**: Free tier CPU throttling - upgrade or reduce TORCH_NUM_THREADS

**Issue**: Database locked errors  
**Fix**: SQLite doesn't support concurrent writes - use PostgreSQL for multi-worker

**Issue**: MemoryError on OFF import  
**Fix**: Use streaming import with `--file` flag (no full file load into RAM)

**Issue**: OFF import UNIQUE errors  
**Fix**: Already handled automatically - duplicates are skipped on IntegrityError

**Issue**: OFF download blocked  
**Fix**: Use alternate URL or download on host, then use `--file` flag

### API Key Issues

**Issue**: 401 Unauthorized  
**Fix**: Include `X-API-Key` header in all requests (except `/health`, `/docs`)

### Docker-Specific Issues

**Issue**: Container can't see seeds/data  
**Fix**: Check volume mount in `docker-compose.yml`: `./seeds/data:/app/seeds/data:ro`

**Issue**: TTY error with heredocs  
**Fix**: Use `docker compose exec -T` (not `exec`) when piping input

**Issue**: Build context too large  
**Fix**: Ensure `.dockerignore` excludes large directories

### Systemd Timer Issues

**Issue**: Timer not running  
**Fix**: Check status with `systemctl status gains-data-update.timer`

**Issue**: Service fails  
**Fix**: Check logs with `journalctl -u gains-data-update -n 50`

**Issue**: Wrong working directory  
**Fix**: Update `WorkingDirectory` in service file, then `systemctl daemon-reload`

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
