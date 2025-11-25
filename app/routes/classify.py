"""Vision classification endpoints"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Request
from PIL import Image
import io
import logging

from app.data.schema import ClassifyResponse, ClassificationResult

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/classify", response_model=ClassifyResponse)
async def classify_food(
    request: Request,
    file: UploadFile = File(...),
    top_k: int = Query(5, ge=1, le=20)
):
    """
    Classify food from image
    
    Args:
        file: Image file (JPEG, PNG, WebP)
        top_k: Number of top predictions (1-20)
    
    Returns:
        ClassifyResponse with top-k predictions
    """
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Get classifier
        classifier = request.app.state.classifier
        if not classifier or not classifier.ready:
            raise HTTPException(status_code=503, detail="Classifier not ready")
        
        # Predict
        labels, scores, inference_ms = await classifier.predict(image, top_k)
        
        # Format response
        results = [
            ClassificationResult(label=label, score=score)
            for label, score in zip(labels, scores)
        ]
        
        return ClassifyResponse(
            model="food101-resnet50",
            top_k=results,
            inference_ms=inference_ms
        )
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
