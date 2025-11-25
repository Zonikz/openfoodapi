# 🚀 GAINS Food Vision API - Quick Start

Get running in 5 minutes!

## Option 1: Local Development

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download Model

```bash
python tools/download_model.py
```

### Step 3: Seed Database

```bash
python seeds/import_cofid.py
python seeds/import_off.py
```

### Step 4: Run Server

```bash
uvicorn main:app --reload
```

🎉 API running at http://localhost:8000

📖 Docs at http://localhost:8000/docs

---

## Option 2: Docker

```bash
docker-compose up --build
```

🎉 API running at http://localhost:8000

---

## Option 3: Replit

1. Create new Repl
2. Upload project files
3. Run:

```bash
pip install -r requirements.txt
python tools/download_model.py
python seeds/import_cofid.py
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Test the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Search Foods

```bash
curl "http://localhost:8000/api/foods/search?q=chicken&limit=5"
```

### 3. GAINS Score

```bash
curl -X POST "http://localhost:8000/api/score/gains" \
  -H "Content-Type: application/json" \
  -d '{"canonical_id": "COFID:1001", "grams": 250}'
```

---

## Connect GAINS App

In your GAINS mobile app, set API URL to:

```
http://YOUR-SERVER-URL:8000
```

Then use the API endpoints as documented in README.md

---

## Next Steps

- Read full [README.md](README.md)
- Import real CoFID/OFF data
- Train better classifier
- Deploy to production

🎊 You're all set!
