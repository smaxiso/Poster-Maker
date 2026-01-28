
import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Tuple


class FileManager:
    """Manage file operations for poster creation."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the file manager.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

    def create_directory_structure(
        self,
        image_path: str,
        parts: int,
        output_dir: str = None,
        duplicate: bool = False,
        grid_spec: str = None,
    ) -> Tuple[str, str, str]:
        """
        Create the output directory structure for poster parts.

        Args:
            image_path: Path to the input image file
            parts: Number of parts (total pages)
            output_dir: Custom output directory (optional)
            duplicate: Whether to preserve previous output under old folder
            grid_spec: If set, e.g. "3x3" for grid layout (folder name posters_3x3)

        Returns:
            Tuple[str, str, str]: (posters_dir, filename, ext)
        """
        # Get base filename without extension
        basename = os.path.basename(image_path)
        filename, ext = os.path.splitext(basename)

        # Define the directory structure
        if output_dir is None:
            base_dir = os.getcwd()
            base_output_dir = os.path.join(base_dir, self.config["paths"]["base_output_dir"])
        else:
            base_output_dir = output_dir

        output_base_dir = os.path.join(base_output_dir, f"{filename}_poster")
        original_dir = os.path.join(output_base_dir, "original")
        layout_label = grid_spec if grid_spec else str(parts)
        posters_dir = os.path.join(output_base_dir, f"posters_{layout_label}")

        self.logger.debug(f"Creating directory structure in {output_base_dir}")

        # Handle duplicate case
        if duplicate and os.path.exists(posters_dir):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            old_posters_dir = os.path.join(output_base_dir, f"old_posters_{layout_label}_{timestamp}")
            try:
                os.makedirs(old_posters_dir, exist_ok=True)
                if os.path.exists(posters_dir):
                    self.logger.info(f"Moving existing posters to {old_posters_dir}")
                    shutil.move(posters_dir, os.path.join(old_posters_dir, "posters"))
            except (OSError, PermissionError) as e:
                self.logger.error(f"Failed to preserve previous output: {e}")
                raise

        # Create output directories
        try:
            os.makedirs(original_dir, exist_ok=True)
            os.makedirs(posters_dir, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create output directories: {e}")
            raise

        # Copy original image
        original_copy_path = os.path.join(original_dir, basename)
        if not os.path.exists(original_copy_path):
            self.logger.debug(f"Copying original image to {original_copy_path}")
            try:
                shutil.copy2(image_path, original_copy_path)
            except (OSError, PermissionError, shutil.SameFileError) as e:
                self.logger.error(f"Failed to copy original image: {e}")
                raise

        return posters_dir, filename, ext

    def get_output_path(self, posters_dir: str, filename: str, part: int = None,
                        ext: str = None, suffix: str = "", output_format: str = None) -> str:
        """
        Generate output file path for image parts.

        Args:
            posters_dir: Directory to save poster parts
            filename: Base filename
            part: Part number (None for full image)
            ext: File extension with dot (e.g., ".jpg")
            suffix: Additional suffix for filename
            output_format: If specified, override the original extension

        Returns:
            str: Full output file path
        """
        if output_format:
            ext = f".{output_format}"

        if part is not None:
            output_name = f"{filename}_part{part}{suffix}{ext}"
        else:
            output_name = f"{filename}{suffix}{ext}"

        output_path = os.path.join(posters_dir, output_name)
        return output_path