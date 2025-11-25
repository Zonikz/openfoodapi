"""
GAINS Food Vision API
Free, self-hosted food recognition + nutrition + GAINS scoring
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from pathlib import Path

from app.config import settings
from app.data.db import init_db, get_db
from app.models.vision_classifier import FoodClassifier
from app.models.vision_detector import FoodDetector
from app.routes import classify, mapping, barcode, search, scoring

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instances
classifier: FoodClassifier = None
detector: FoodDetector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management: load models on startup"""
    global classifier, detector
    
    logger.info("🚀 Starting GAINS Food Vision API")
    
    # Initialize database
    logger.info("📦 Initializing database...")
    init_db()
    
    # Load classifier
    logger.info("🧠 Loading Food-101 classifier...")
    classifier = FoodClassifier()
    await classifier.load()
    app.state.classifier = classifier
    
    # Load detector if enabled
    if settings.ENABLE_DETECTOR:
        logger.info("🔍 Loading YOLOv8 detector...")
        detector = FoodDetector()
        await detector.load()
        app.state.detector = detector
    else:
        logger.info("⏭️  Detector disabled (ENABLE_DETECTOR=false)")
    
    logger.info("✅ API ready!")
    
    yield
    
    logger.info("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="GAINS Food Vision API",
    description="Free, self-hosted food recognition + nutrition + GAINS scoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow all for Expo RN + local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(classify.router, prefix="/api", tags=["Vision"])
app.include_router(mapping.router, prefix="/api", tags=["Mapping"])
app.include_router(barcode.router, prefix="/api", tags=["Barcode"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(scoring.router, prefix="/api", tags=["Scoring"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GAINS Food Vision API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    
    Returns:
        - status: overall health status
        - classifier: model load status
        - detector: detector status (if enabled)
        - database: connection status
        - data_counts: row counts for each data source
        - label_map_coverage: percentage of Food-101 classes mapped
        - last_import: timestamps of data imports
    """
    try:
        from app.data.schema import FoodGeneric, FoodOFF, LabelMapping
        from sqlmodel import select, func
        from app.models.vision_classifier import FOOD101_CLASSES
        import json
        
        # Check classifier
        classifier_status = "loaded" if app.state.classifier and app.state.classifier.ready else "not_loaded"
        
        # Check detector
        detector_status = "disabled"
        if settings.ENABLE_DETECTOR:
            detector_status = "loaded" if hasattr(app.state, 'detector') and app.state.detector.ready else "not_loaded"
        
        # Check database and get counts
        db = next(get_db())
        
        cofid_count = db.exec(
            select(func.count(FoodGeneric.id))
            .where(FoodGeneric.source == "cofid")
        ).one()
        
        off_count = db.exec(
            select(func.count(FoodOFF.id))
        ).one()
        
        # Check label map coverage
        label_map_path = settings.label_map_path
        label_map_coverage = 0
        mapped_count = 0
        
        if label_map_path.exists():
            with open(label_map_path) as f:
                label_map = json.load(f)
                # Exclude _note field
                mapped_count = len([k for k in label_map.keys() if not k.startswith('_')])
                label_map_coverage = (mapped_count / len(FOOD101_CLASSES)) * 100
        
        # Get database file info for last modified
        db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
        last_import = None
        if db_path.exists():
            import datetime
            last_import = datetime.datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
        
        return {
            "status": "healthy" if classifier_status == "loaded" else "degraded",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "classifier": classifier_status,
            "detector": detector_status,
            "database": "connected",
            "data_counts": {
                "cofid_foods": cofid_count,
                "off_products": off_count,
                "total": cofid_count + off_count
            },
            "label_map": {
                "mapped": mapped_count,
                "total": len(FOOD101_CLASSES),
                "coverage_percent": round(label_map_coverage, 1)
            },
            "last_import": last_import,
            "models": {
                "food101": settings.MODEL_NAME,
                "detector_enabled": settings.ENABLE_DETECTOR
            },
            "api_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }
        )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
