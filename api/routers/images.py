import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from PIL import Image

from api.schemas import ImageMetadata, ImageDimensions
from api.dependencies import get_logger

router = APIRouter(prefix="/images", tags=["images"])

# Define upload directory
UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ImageMetadata)
async def upload_image(
    file: UploadFile = File(...),
    logger = Depends(get_logger)
):
    """
    Upload an image file and return its metadata.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate unique filename to prevent collisions
    file_ext = os.path.splitext(file.filename)[1]
    if not file_ext:
        # Default fallback if extension missing
        file_ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
        
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Saved uploaded file to {file_path}")

        # Analyze image with Pillow
        with Image.open(file_path) as img:
            width, height = img.size
            format_name = img.format
            
            # Generate thumbnail for preview (max 800px)
            img.thumbnail((800, 800))
            thumb_filename = f"{uuid.uuid4()}_thumb{file_ext}"
            thumb_path = os.path.join(UPLOAD_DIR, thumb_filename)
            img.save(thumb_path)
            
        file_size = os.path.getsize(file_path)
        
        # Construct response
        url = f"/images/file/{unique_filename}"
        preview_url = f"/images/file/{thumb_filename}"
        
        return ImageMetadata(
            filename=unique_filename,
            original_filename=file.filename,
            format=format_name or "UNKNOWN",
            size_bytes=file_size,
            dimensions=ImageDimensions(
                width=width,
                height=height,
                aspect_ratio=round(width / height, 3) if height > 0 else 0
            ),
            url=url,
            preview_url=preview_url
        )

    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        # Clean up if file was partially saved
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{filename}")
async def get_image(filename: str):
    """
    Serve an uploaded image file.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
        
    return FileResponse(file_path)
