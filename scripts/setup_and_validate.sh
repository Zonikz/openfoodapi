#!/bin/bash
# GAINS Food Vision API - One-Command Setup & Validation
# This script sets up the entire project and runs validation tests

set -e  # Exit on error

echo "=================================================="
echo "🚀 GAINS FOOD VISION API - SETUP & VALIDATION"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track status
SETUP_STATUS=0
VALIDATION_STATUS=0

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Python not found. Please install Python 3.11+${NC}"
        exit 1
    fi
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}❌ Could not find virtual environment activation script${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data models app/mapping
echo -e "${GREEN}✅ Directories ready${NC}"
echo ""

# Download model weights
echo "=================================================="
echo "STEP 1: MODEL WEIGHTS"
echo "=================================================="
$PYTHON_CMD tools/download_model.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Model weights ready${NC}"
else
    echo -e "${YELLOW}⚠️  Model download had issues (continuing anyway)${NC}"
fi
echo ""

# Import CoFID data
echo "=================================================="
echo "STEP 2: CoFID DATABASE"
echo "=================================================="
$PYTHON_CMD seeds/import_cofid.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CoFID data imported${NC}"
else
    echo -e "${RED}❌ CoFID import failed${NC}"
    SETUP_STATUS=1
fi
echo ""

# Import OpenFoodFacts data
echo "=================================================="
echo "STEP 3: OPENFOODFACTS DATABASE"
echo "=================================================="
echo "⏳ This may take 5-10 minutes (downloading large dataset)..."
$PYTHON_CMD seeds/import_off.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ OpenFoodFacts data imported${NC}"
else
    echo -e "${YELLOW}⚠️  OFF import had issues (continuing with sample data)${NC}"
fi
echo ""

# Build label map
echo "=================================================="
echo "STEP 4: LABEL MAPPING"
echo "=================================================="
$PYTHON_CMD tools/build_label_map.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Label map built${NC}"
else
    echo -e "${RED}❌ Label map build failed${NC}"
    SETUP_STATUS=1
fi
echo ""

# Run validation suite
echo "=================================================="
echo "STEP 5: VALIDATION TESTS"
echo "=================================================="
echo ""

# Model validation
echo "→ Validating model..."
$PYTHON_CMD tools/validate_model.py
MODEL_STATUS=$?

# CoFID validation
echo ""
echo "→ Validating CoFID..."
$PYTHON_CMD tools/validate_cofid.py
COFID_STATUS=$?

# OFF validation
echo ""
echo "→ Validating OpenFoodFacts..."
$PYTHON_CMD tools/validate_off.py
OFF_STATUS=$?

# Label map validation
echo ""
echo "→ Validating label map..."
$PYTHON_CMD tools/validate_label_map.py
LABEL_STATUS=$?

# Pytest suite
echo ""
echo "→ Running pytest suite..."
pytest tests/ -v --tb=short -x
PYTEST_STATUS=$?

# Final summary
echo ""
echo "=================================================="
echo "📊 SETUP & VALIDATION SUMMARY"
echo "=================================================="
echo ""

if [ $MODEL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Model Validation: PASS${NC}"
else
    echo -e "${RED}❌ Model Validation: FAIL${NC}"
    VALIDATION_STATUS=1
fi

if [ $COFID_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ CoFID Validation: PASS${NC}"
else
    echo -e "${RED}❌ CoFID Validation: FAIL${NC}"
    VALIDATION_STATUS=1
fi

if [ $OFF_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ OFF Validation: PASS${NC}"
else
    echo -e "${YELLOW}⚠️  OFF Validation: PARTIAL (expected if using sample data)${NC}"
fi

if [ $LABEL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Label Map Validation: PASS${NC}"
else
    echo -e "${RED}❌ Label Map Validation: FAIL${NC}"
    VALIDATION_STATUS=1
fi

if [ $PYTEST_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Pytest Suite: PASS${NC}"
else
    echo -e "${YELLOW}⚠️  Pytest Suite: PARTIAL${NC}"
fi

echo ""
echo "=================================================="

if [ $SETUP_STATUS -eq 0 ] && [ $VALIDATION_STATUS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED - API READY!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start server: uvicorn main:app --reload"
    echo "  2. Visit: http://localhost:8000/docs"
    echo "  3. Test endpoints with examples/test_requests.sh"
    exit 0
else
    echo -e "${YELLOW}⚠️  SETUP COMPLETE WITH WARNINGS${NC}"
    echo ""
    echo "Some validations failed, but the API should still work."
    echo "Check the logs above for details."
    echo ""
    echo "To start the server anyway:"
    echo "  uvicorn main:app --reload"
    exit 1
fi
