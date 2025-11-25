#!/bin/bash
# Example API requests for GAINS Food Vision API

BASE_URL="http://localhost:8000"

echo "🧪 Testing GAINS Food Vision API"
echo ""

# 1. Health check
echo "1️⃣  Health check..."
curl -s "$BASE_URL/health" | jq
echo ""

# 2. Classify image (requires test image)
echo "2️⃣  Classify food..."
# curl -X POST "$BASE_URL/api/classify?top_k=5" \
#   -F "file=@examples/chicken_curry.jpg" | jq
echo "  (Skipped - requires test image)"
echo ""

# 3. Map to food
echo "3️⃣  Map to canonical food..."
curl -s -X POST "$BASE_URL/api/map-to-food" \
  -H "Content-Type: application/json" \
  -d '{"query": "chicken_curry", "country": "UK"}' | jq
echo ""

# 4. Search foods
echo "4️⃣  Search foods..."
curl -s "$BASE_URL/api/foods/search?q=chicken&limit=5" | jq
echo ""

# 5. Barcode lookup
echo "5️⃣  Barcode lookup..."
curl -s "$BASE_URL/api/barcode/5000159407236" | jq
echo ""

# 6. GAINS scoring
echo "6️⃣  GAINS scoring..."
curl -s -X POST "$BASE_URL/api/score/gains" \
  -H "Content-Type: application/json" \
  -d '{"canonical_id": "COFID:1001", "grams": 250}' | jq
echo ""

echo "✅ Tests complete!"
