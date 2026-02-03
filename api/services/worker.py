import os
import logging
from api.schemas import ProcessingConfig, TaskStatus
from api.services.task_manager import TaskManager
from api.services.progress_adapter import APIProgressCallback
from poster_maker.core.image_processor import ImageProcessor
from poster_maker.core.file_manager import FileManager
from poster_maker.utils.pdf_service import PDFService

async def process_poster_background(
    task_id: str,
    config: ProcessingConfig,
    image_processor: ImageProcessor,
    file_manager: FileManager,
    pdf_service: PDFService,
    task_manager: TaskManager,
    logger: logging.Logger
):
    """
    Background worker function to process the poster.
    """
    try:
        # Construct full input path
        upload_dir = os.path.join(os.getcwd(), "data", "uploads")
        input_path = os.path.join(upload_dir, config.filename)

        if not os.path.exists(input_path):
            task_manager.update_task(
                task_id, 
                status=TaskStatus.FAILED, 
                error=f"Input file not found: {config.filename}"
            )
            return

        # Initialize progress callback
        progress = APIProgressCallback(task_id, task_manager)
        
        logger.info(f"Starting background task {task_id} for {config.filename}")
        
        grid = (config.grid.rows, config.grid.cols) if config.grid else None

        # Execute processing
        result = image_processor.process_image(
            image_path=input_path,
            parts=config.parts,
            dpi=config.dpi,
            output_dir=None,
            duplicate=False,
            output_format=config.output_format,
            resize_mode=config.resize_mode,
            verbose=False,
            grid=grid,
            progress_callback=progress,
            rotation=config.rotation,
            flip_horizontal=config.flip_horizontal,
            flip_vertical=config.flip_vertical
        )

        # Generating PDF if requested
        if config.generate_pdf:
             # Use values from summary which contains rich info (dimensions, crop_box) 
             # expected by pdf_service, not just paths
             parts_info = result["summary"]["output"]["parts"]
             
             if parts_info:
                 # Get directory from the first part path
                 first_part_path = parts_info[0]["path"]
                 posters_dir = os.path.dirname(first_part_path)
                 
                 # Determine basename for PDF
                 # image_processor uses basename of input file usually
                 base_name = os.path.splitext(config.filename)[0]
                 pdf_filename = f"{base_name}_complete.pdf"
                 full_output_path = os.path.join(posters_dir, pdf_filename)
                 
                 progress.on_update(0, "Generating PDF...")
                 
                 pdf_info = pdf_service.generate_pdf_from_parts(
                     parts_info, 
                     output_path=full_output_path,
                     grid_rows=config.grid.rows if config.grid else None,
                     grid_cols=config.grid.cols if config.grid else None
                 )
                 
                 pdf_path = pdf_info["path"]
                 result["output_paths"]["pdf"] = pdf_path
                 # Add to summary
                 result["summary"]["output"]["pdf"] = pdf_path

        # Update task with result
        task_manager.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="Processing complete",
            result=result
        )

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        task_manager.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            message="Processing failed"
        )
