from functools import lru_cache
from typing import Dict, Any

from poster_maker.config.config_loader import ConfigLoader
from poster_maker.utils.logger import LoggerSetup
from poster_maker.core.file_manager import FileManager
from poster_maker.core.image_processor import ImageProcessor
from poster_maker.utils.memory_service import MemoryService

@lru_cache()
def get_config():
    loader = ConfigLoader()
    return loader.get_config()

@lru_cache()
def get_logger():
    # Setup logger with default/minimal args for API mode
    arg_dict = {
        "verbose": False  # API should be less verbose mainly
    }
    config = get_config()
    logger_setup = LoggerSetup(config, arg_dict)
    return logger_setup.get_logger()

@lru_cache()
def get_file_manager():
    config = get_config()
    logger = get_logger()
    return FileManager(config, logger)

@lru_cache()
def get_image_processor():
    config = get_config()
    logger = get_logger()
    file_manager = get_file_manager()
    return ImageProcessor(config, logger, file_manager)

@lru_cache()
def get_memory_service():
    logger = get_logger()
    return MemoryService(logger)

from api.services.task_manager import TaskManager

@lru_cache()
def get_task_manager():
    return TaskManager()

from poster_maker.utils.pdf_service import PDFService

@lru_cache()
def get_pdf_service():
    config = get_config()
    logger = get_logger()
    return PDFService(logger, config)
