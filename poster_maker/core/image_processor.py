
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
from tqdm import tqdm

from poster_maker.core.file_manager import FileManager


class ImageProcessor:
    """Process and split images for poster creation."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger, file_manager: FileManager):
        """
        Initialize the image processor.

        Args:
            config: Configuration dictionary
            logger: Logger instance
            file_manager: FileManager instance
        """
        self.config = config
        self.logger = logger
        self.file_manager = file_manager

        # Get resampling method from config
        resampling_str = self.config["image"].get("resampling_method", "LANCZOS")
        self.resampling_method = getattr(Image, resampling_str)

    def calculate_ideal_dimensions(self, img_width: int, img_height: int, parts: int, dpi: int) -> Tuple[int, int]:
        """
        Calculate ideal dimensions to optimize for A4 printing.

        Args:
            img_width: Original image width
            img_height: Original image height
            parts: Number of parts to split into
            dpi: DPI for output images

        Returns:
            Tuple[int, int]: (target_width, target_height)
        """
        # Calculate A4 dimensions at the specified DPI
        a4_config = self.config["image"]["a4"]
        a4_width = int(a4_config["width_inches"] * dpi)
        a4_height = int(a4_config["height_inches"] * dpi)

        aspect_ratio = img_width / img_height

        # Determine if we should split horizontally or vertically
        # For poster creation, we typically want to split along the longer dimension
        if img_width > img_height:  # Landscape orientation
            # Split horizontally
            target_width = a4_width * parts
            target_height = int(target_width / aspect_ratio)
        else:  # Portrait orientation
            # Split vertically
            target_height = a4_height * parts
            target_width = int(target_height * aspect_ratio)

        self.logger.debug(f"Calculated ideal dimensions: {target_width}x{target_height} pixels")
        return target_width, target_height

    def calculate_ideal_dimensions_grid(
        self, img_width: int, img_height: int, rows: int, cols: int, dpi: int
    ) -> Tuple[int, int]:
        """
        Calculate ideal dimensions for a rows×cols grid (each cell = 1 A4 page).

        Returns:
            Tuple[int, int]: (target_width, target_height) so that dividing into
            cols×rows gives A4-sized cells.
        """
        a4_config = self.config["image"]["a4"]
        a4_width = int(a4_config["width_inches"] * dpi)
        a4_height = int(a4_config["height_inches"] * dpi)
        target_width = a4_width * cols
        target_height = a4_height * rows
        self.logger.debug(f"Grid ideal dimensions: {target_width}x{target_height} ({rows}×{cols} A4 cells)")
        return target_width, target_height

    def resize_image(self, img: Image.Image, target_width: int, target_height: int,
                     resize_mode: str = "maintain", verbose: bool = False) -> Image.Image:
        """
        Resize an image to target dimensions based on specified mode with interactive progress bar.
        """
        start_time = time.time()
        self.logger.info(
            f"Resizing image from {img.width}x{img.height} to {target_width}x{target_height} (mode: {resize_mode})")

        orig_width, orig_height = img.size

        # Guard against zero dimensions
        if orig_height == 0 or orig_width == 0:
            raise ValueError(f"Invalid image dimensions: {orig_width}x{orig_height}")
        if target_height == 0 or target_width == 0:
            raise ValueError(f"Invalid target dimensions: {target_width}x{target_height}")

        # Only show progress bar if verbose is True
        if verbose:
            # Show elapsed time instead of fake percentages (PIL resize can't report real progress)
            with tqdm(total=100, desc="Resizing image", unit="%", bar_format='{desc}: {elapsed}') as pbar:
                img_resized = self._do_resize(img, target_width, target_height, resize_mode)
                pbar.update(100)
        else:
            img_resized = self._do_resize(img, target_width, target_height, resize_mode)

        elapsed_time = time.time() - start_time
        self.logger.debug(f"Resizing completed in {elapsed_time:.2f} seconds")

        return img_resized

    def _do_resize(
        self, img: Image.Image, target_width: int, target_height: int, resize_mode: str
    ) -> Image.Image:
        """
        Perform the actual resize operation (extracted to avoid duplication).
        """
        orig_width, orig_height = img.size
        aspect_ratio = orig_width / orig_height
        target_ratio = target_width / target_height

        if resize_mode in ["maintain", "stretch"]:
            return img.resize((target_width, target_height), self.resampling_method, reducing_gap=3.0)

        elif resize_mode == "crop":
            if aspect_ratio > target_ratio:
                new_width = int(target_height * aspect_ratio)
                temp_img = img.resize((new_width, target_height), self.resampling_method)
                left = (new_width - target_width) // 2
                return temp_img.crop((left, 0, left + target_width, target_height))
            else:
                new_height = int(target_width / aspect_ratio)
                temp_img = img.resize((target_width, new_height), self.resampling_method)
                top = (new_height - target_height) // 2
                return temp_img.crop((0, top, target_width, top + target_height))

        elif resize_mode in ["pad_white", "pad_black"]:
            pad_color = (255, 255, 255) if resize_mode == "pad_white" else (0, 0, 0)
            img_resized = Image.new("RGB", (target_width, target_height), pad_color)

            if aspect_ratio > target_ratio:
                new_height = int(target_width / aspect_ratio)
                temp_img = img.resize((target_width, new_height), self.resampling_method)
                y_offset = (target_height - new_height) // 2
                img_resized.paste(temp_img, (0, y_offset))
            else:
                new_width = int(target_height * aspect_ratio)
                temp_img = img.resize((new_width, target_height), self.resampling_method)
                x_offset = (target_width - new_width) // 2
                img_resized.paste(temp_img, (x_offset, 0))
            return img_resized

        else:
            return img.resize((target_width, target_height), self.resampling_method)

    def _save_image_optimized(self, img: Image.Image, path: str) -> None:
        """
        Save image with optimized compression settings.

        For PNG: Uses compress_level=6 (faster than default 9, good compression).
        For JPEG: Uses quality=95 and optimize=True.

        Args:
            img: PIL Image to save
            path: Output file path
        """
        ext = os.path.splitext(path)[1].lower()

        if ext == ".png":
            # compress_level 6 is ~3x faster than 9 with ~5% larger files
            img.save(path, compress_level=6)
        elif ext in (".jpg", ".jpeg"):
            # Convert to RGB if necessary (JPEG doesn't support alpha)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(path, quality=95, optimize=True)
        else:
            # Default: let Pillow decide
            img.save(path)

    def split_and_save_parts(
        self,
        img_resized: Image.Image,
        split_parts: List[Tuple[Image.Image, Tuple[int, int, int, int]]],
        filename: str,
        posters_dir: str,
        ext: str,
        output_format: Optional[str] = None,
        verbose: bool = False,
    ) -> List[str]:
        """
        Split image and save parts with optional progress bar based on verbose flag.

        Returns:
            List of output file paths for the saved part images.
        """
        output_paths: List[str] = []
        total_parts = len(split_parts)

        if verbose:
            # Progress bar: count parts (avoids misleading GB from uncompressed pixel bytes)
            with tqdm(total=total_parts, desc="Creating poster parts", unit="part") as pbar:
                for i, (part, box) in enumerate(split_parts, 1):
                    pbar.set_description(f"Creating part {i}/{total_parts}")

                    output_path = self.file_manager.get_output_path(
                        posters_dir, filename, part=i, ext=ext, output_format=output_format
                    )

                    self._save_image_optimized(part, output_path)
                    pbar.update(1)
                    output_paths.append(output_path)

                    # Log info but don't display on console during progress
                    self.logger.info(f"Saved part {i}/{total_parts}: {output_path} ({part.width}x{part.height} pixels)")
        else:
            # No progress bar when not in verbose mode
            for i, (part, box) in enumerate(split_parts, 1):
                output_path = self.file_manager.get_output_path(
                    posters_dir, filename, part=i, ext=ext, output_format=output_format
                )

                # Save the part with optimized settings
                self._save_image_optimized(part, output_path)
                output_paths.append(output_path)

                # Log with print since not in verbose mode
                self.logger.info(f"Saved part {i}/{total_parts}: {output_path} ({part.width}x{part.height} pixels)")
                print(f"Saved part {i}/{total_parts}: {output_path}")

        return output_paths

    def process_image(
        self,
        image_path: str,
        parts: int,
        dpi: int,
        output_dir: str = None,
        duplicate: bool = False,
        output_format: str = None,
        resize_mode: str = "maintain",
        verbose: bool = False,
        grid: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Process an image: resize, split, and save parts.

        Args:
            image_path: Path to the input image file
            parts: Number of parts (total; for grid mode this is rows×cols)
            dpi: DPI for output images
            output_dir: Custom output directory (optional)
            duplicate: Whether to preserve previous output
            output_format: Output image format (e.g., "png", "jpg")
            resize_mode: How to handle aspect ratio
            verbose: Whether to enable verbose logging
            grid: If set, (rows, cols) for 2D grid split; else 1D strip

        Returns:
            Dict[str, Any]: Dictionary with output paths and process summary
        """
        start_time = time.time()
        grid_spec = f"{grid[0]}x{grid[1]}" if grid else None
        summary = {
            "source_image": {
                "path": image_path,
                "format": os.path.splitext(image_path)[1][1:],
            },
            "process_options": {
                "parts": parts,
                "grid": grid_spec,
                "dpi": dpi,
                "output_format": output_format,
                "resize_mode": resize_mode,
                "preserve_previous": duplicate,
            },
            "output": {},
            "timing": {},
        }

        # Create directories and get paths
        posters_dir, filename, ext = self.file_manager.create_directory_structure(
            image_path, parts, output_dir, duplicate, grid_spec=grid_spec
        )

        # Initialize output_paths dictionary
        output_paths = {
            "resized": None,
            "parts": []
        }

        # If output format is specified, override the extension
        if output_format:
            self.logger.info(f"Overriding output format to .{output_format}")
            ext = f".{output_format}"

        # Open the original image
        self.logger.info(f"Opening image: {image_path}")
        try:
            img = Image.open(image_path)
            img.load()  # Force load to catch truncated/corrupt images
        except OSError as e:
            self.logger.error(f"Cannot open or read image: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Invalid or corrupted image: {e}")
            raise

        width, height = img.size
        self.logger.info(f"Image dimensions: {width}x{height} pixels")

        # Update summary with source image details
        summary["source_image"]["dimensions"] = {
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 3)
        }
        try:
            summary["source_image"]["size_bytes"] = os.path.getsize(image_path)
        except OSError as e:
            self.logger.warning(f"Could not get file size: {e}")
            summary["source_image"]["size_bytes"] = 0

        # Calculate ideal dimensions for proper A4 printing
        if grid:
            target_width, target_height = self.calculate_ideal_dimensions_grid(
                width, height, grid[0], grid[1], dpi
            )
        else:
            target_width, target_height = self.calculate_ideal_dimensions(width, height, parts, dpi)

        # Record resize start time
        resize_start = time.time()

        # Resize image to the ideal dimensions with high quality
        img_resized = self.resize_image(img, target_width, target_height, resize_mode, verbose)
        width, height = img_resized.size

        # Update timing information
        summary["timing"]["resize_seconds"] = round(time.time() - resize_start, 2)

        # Save the resized full image as a reference
        resized_path = self.file_manager.get_output_path(
            posters_dir, filename, ext=ext, suffix="_resized", output_format=output_format
        )

        # Save with progress indication (large images can take 20-30s)
        if verbose:
            print("Saving resized image (this may take a moment for large images)...")
        self._save_image_optimized(img_resized, resized_path)
        self.logger.info(f"Saved resized image: {resized_path}")

        # Store resized path in output_paths
        output_paths["resized"] = resized_path

        # Update summary with resized image info
        summary["output"]["resized_image"] = {
            "path": resized_path,
            "dimensions": {
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 3)
            },
            "size_bytes": os.path.getsize(resized_path)
        }

        # Split the image and save each part with progress bar
        split_start = time.time()
        if grid:
            self.logger.info(f"Splitting image into {grid[0]}×{grid[1]} grid ({parts} parts)")
            split_parts = self.split_image_to_grid(img_resized, grid[0], grid[1])
        else:
            self.logger.info(f"Splitting image into {parts} parts")
            split_parts = self.split_image_to_parts(img_resized, parts)
        summary["timing"]["split_calculation_seconds"] = round(time.time() - split_start, 2)

        # Use the improved split and save function
        save_start = time.time()
        output_paths["parts"] = self.split_and_save_parts(
            img_resized, split_parts, filename, posters_dir, ext, output_format, verbose
        )
        summary["timing"]["save_parts_seconds"] = round(time.time() - save_start, 2)

        # Update the parts information in the summary
        summary["output"]["parts"] = []
        part_sizes_bytes = 0

        for i, path in enumerate(output_paths["parts"], 1):
            part = split_parts[i - 1][0]  # Get the image part
            box = split_parts[i - 1][1]  # Get the crop box
            file_size = os.path.getsize(path)
            part_sizes_bytes += file_size

            # Add part info to summary
            summary["output"]["parts"].append({
                "part_number": i,
                "path": path,
                "dimensions": {
                    "width": part.width,
                    "height": part.height
                },
                "size_bytes": file_size,
                "crop_box": box
            })

        if grid:
            summary["output"]["grid_rows"] = grid[0]
            summary["output"]["grid_cols"] = grid[1]

        # Calculate total processing time
        total_time = time.time() - start_time
        summary["timing"]["total_seconds"] = round(total_time, 2)

        # Add final summary stats
        summary["output"]["total_size_bytes"] = part_sizes_bytes + summary["output"]["resized_image"]["size_bytes"]
        summary["output"]["total_size_mb"] = round(summary["output"]["total_size_bytes"] / (1024 * 1024), 2)

        return {
            "output_paths": output_paths,
            "summary": summary
        }

    def split_image_to_parts(self, img: Image.Image, parts: int) -> List[Tuple[Image.Image, Tuple[int, int, int, int]]]:
        """
        Split an image into parts.

        Args:
            img: PIL Image object to split
            parts: Number of parts to split into

        Returns:
            List[Tuple[Image.Image, Tuple[int, int, int, int]]]: List of (image_part, (left, upper, right, lower))
        """
        width, height = img.size
        horizontal_split = width > height

        # Calculate dimensions for each part
        result_parts = []

        if horizontal_split:
            self.logger.info(f"Splitting horizontally into {parts} parts")
            part_width = width // parts
            part_height = height

            for i in range(parts):
                left = i * part_width
                # Make sure the last part includes any remainder pixels
                right = (i + 1) * part_width if i < parts - 1 else width
                box = (left, 0, right, part_height)

                part = img.crop(box)
                if abs(part.width - part_width) > 1:
                    self.logger.warning(f"Part {i + 1} has different width: {part.width}px vs expected {part_width}px")

                result_parts.append((part, box))
        else:
            self.logger.info(f"Splitting vertically into {parts} parts")
            part_width = width
            part_height = height // parts

            for i in range(parts):
                top = i * part_height
                # Make sure the last part includes any remainder pixels
                bottom = (i + 1) * part_height if i < parts - 1 else height
                box = (0, top, part_width, bottom)

                part = img.crop(box)
                if abs(part.height - part_height) > 1:
                    self.logger.warning(
                        f"Part {i + 1} has different height: {part.height}px vs expected {part_height}px")

                result_parts.append((part, box))

        return result_parts

    def split_image_to_grid(
        self, img: Image.Image, rows: int, cols: int
    ) -> List[Tuple[Image.Image, Tuple[int, int, int, int]]]:
        """
        Split an image into a rows×cols grid. Parts are returned in row-major order
        (top row left-to-right, then next row, etc.), numbered 1..rows*cols.

        Returns:
            List of (image_part, (left, upper, right, lower)) in reading order.
        """
        width, height = img.size
        cell_w = width // cols
        cell_h = height // rows
        result_parts = []
        self.logger.info(f"Splitting into {rows}×{cols} grid ({rows * cols} parts)")

        for row in range(rows):
            for col in range(cols):
                left = col * cell_w
                right = width if col == cols - 1 else (col + 1) * cell_w
                top = row * cell_h
                bottom = height if row == rows - 1 else (row + 1) * cell_h
                box = (left, top, right, bottom)
                part = img.crop(box)
                result_parts.append((part, box))

        return result_parts