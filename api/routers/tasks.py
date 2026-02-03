from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from api.schemas import ProcessingConfig, TaskResponse
from api.dependencies import (
    get_task_manager, get_image_processor, 
    get_file_manager, get_pdf_service, get_logger
)
from api.services.worker import process_poster_background

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/process", response_model=TaskResponse)
async def process_image(
    config: ProcessingConfig,
    background_tasks: BackgroundTasks,
    task_manager = Depends(get_task_manager),
    image_processor = Depends(get_image_processor),
    file_manager = Depends(get_file_manager),
    pdf_service = Depends(get_pdf_service),
    logger = Depends(get_logger)
):
    """
    Start a background task to process an uploaded image.
    """
    # Create task entry
    task_id = task_manager.create_task()
    
    # helper wrapper to pass ALL dependencies to the worker
    background_tasks.add_task(
        process_poster_background,
        task_id=task_id,
        config=config,
        image_processor=image_processor,
        file_manager=file_manager,
        pdf_service=pdf_service,
        task_manager=task_manager,
        logger=logger
    )
    
    # Return initial status
    return task_manager.get_task(task_id)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    task_manager = Depends(get_task_manager)
):
    """
    Get the status of a background task.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return task

from fastapi.responses import FileResponse
import os

@router.get("/{task_id}/download/pdf")
async def download_pdf(
    task_id: str,
    task_manager = Depends(get_task_manager)
):
    """
    Download the generated PDF for a completed task.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task is not complete")
        
    if not task.result or "output_paths" not in task.result or "pdf" not in task.result["output_paths"]:
        raise HTTPException(status_code=404, detail="PDF outcome not found")
        
    pdf_path = task.result["output_paths"]["pdf"]
    if not os.path.exists(pdf_path):
         raise HTTPException(status_code=404, detail="PDF file missing on server")
         
    return FileResponse(
        pdf_path, 
        media_type="application/pdf", 
        filename=os.path.basename(pdf_path)
    )
