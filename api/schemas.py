from pydantic import BaseModel
from typing import Optional

class ImageDimensions(BaseModel):
    width: int
    height: int
    aspect_ratio: float

class ImageMetadata(BaseModel):
    filename: str
    original_filename: str
    format: str
    size_bytes: int
    dimensions: ImageDimensions
    url: str  # URL to access the original image
    preview_url: Optional[str] = None  # URL to a smaller preview thumbnail

from enum import Enum
from typing import List, Optional, Dict, Any

class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GridConfig(BaseModel):
    rows: int
    cols: int

class ProcessingConfig(BaseModel):
    filename: str  # The unique filename returned by upload
    dpi: int = 300
    grid: Optional[GridConfig] = None
    parts: int = 3  # Fallback if grid not specified
    output_format: Optional[str] = None
    resize_mode: str = "maintain"
    generate_pdf: bool = True
    pdf_options: Dict[str, Any] = {} # e.g. {"compress": True, "quality": 90}
    rotation: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

