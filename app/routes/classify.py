"""Vision classification endpoints"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Request
from PIL import Image
import io
import logging

from app.data.schema import ClassifyResponse, ClassificationResult

router = APIRouter()
logger = logging.getLogger(__name__)

# Image constraints
MAX_IMAGE_SIZE_MB = 6
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]


@router.post("/classify", response_model=ClassifyResponse)
async def classify_food(
    request: Request,
    file: UploadFile = File(...),
    top_k: int = Query(5, ge=1, le=20)
):
    """
    Classify food from image
    
    Args:
        file: Image file (JPEG, PNG, WebP) - Max 6MB
        top_k: Number of top predictions (1-20)
    
    Returns:
        ClassifyResponse with top-k predictions
    
    Raises:
        422: Invalid image format or size
        503: Classifier not ready
        500: Processing error
    """
    try:
        # Validate content type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid image format. Allowed: JPEG, PNG, WebP. Got: {file.content_type}"
            )
        
        # Read image with size limit
        contents = await file.read()
        
        # Check file size
        if len(contents) > MAX_IMAGE_SIZE_BYTES:
            size_mb = len(contents) / (1024 * 1024)
            raise HTTPException(
                status_code=422,
                detail=f"Image too large: {size_mb:.1f}MB. Maximum allowed: {MAX_IMAGE_SIZE_MB}MB"
            )
        
        # Validate image can be opened
        try:
            image = Image.open(io.BytesIO(contents))
            # Verify it's actually an image
            image.verify()
            # Reopen for processing (verify() closes the file)
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid or corrupted image file: {str(e)}"
            )
        
        # Get classifier
        classifier = request.app.state.classifier
        if not classifier or not classifier.ready:
            raise HTTPException(
                status_code=503,
                detail="Classifier not ready. Please try again in a moment."
            )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")
