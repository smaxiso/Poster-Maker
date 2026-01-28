
"""
Input validation for poster maker (file paths, parts, grid, DPI, format).

Validation Limits:
    MAX_PARTS (100): Maximum number of poster parts for 1D strip mode.
    MAX_GRID_DIM (20): Maximum rows or columns in grid mode.
    MAX_GRID_PAGES (100): Maximum total pages (rows×cols) in grid mode.
    MIN_DPI (72): Minimum DPI for acceptable print quality.
    MAX_DPI (1200): Maximum DPI; higher values cause performance issues.
"""
import os
import re
from typing import Optional, Tuple

# Validation limits (single source of truth)
MAX_PARTS = 100
MAX_GRID_DIM = 20
MAX_GRID_PAGES = 100
MIN_DPI = 72
MAX_DPI = 1200


def parse_grid(s: str) -> Optional[Tuple[int, int]]:
    """
    Parse a grid spec string like '3x3' or '2x4' into (rows, cols).

    Returns:
        (rows, cols) or None if invalid.
    """
    if not s or not isinstance(s, str):
        return None
    m = re.match(r"^(\d+)\s*[xX×]\s*(\d+)$", s.strip())
    if not m:
        return None
    try:
        r, c = int(m.group(1)), int(m.group(2))
        return (r, c) if (r > 0 and c > 0) else None
    except (ValueError, IndexError):
        return None


class InputValidator:
    """Validate input parameters for the poster maker."""

    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if the provided file path exists and is a file.

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        if not os.path.isfile(file_path):
            return False, f"Not a file: {file_path}"

        return True, None

    @staticmethod
    def validate_parts(parts: int) -> Tuple[bool, Optional[str]]:
        """
        Validate the number of parts to split the image into.

        Args:
            parts: Number of parts to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if parts <= 0:
            return False, f"Number of parts must be positive, got: {parts}"

        if parts > MAX_PARTS:
            return False, f"Number of parts too large: {parts} (max {MAX_PARTS})"

        return True, None

    @staticmethod
    def validate_grid(rows: int, cols: int) -> Tuple[bool, Optional[str]]:
        """
        Validate grid dimensions (rows × cols).
        Limits: each dimension ≤ 20, and rows×cols ≤ 100 (so e.g. 10×10 or 20×5 ok; 20×20 invalid).

        Args:
            rows: Number of rows
            cols: Number of columns

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if rows <= 0 or cols <= 0:
            return False, f"Grid rows and cols must be positive, got: {rows}x{cols}"
        if rows > MAX_GRID_DIM or cols > MAX_GRID_DIM:
            return False, f"Each dimension must be ≤ {MAX_GRID_DIM}, got: {rows}×{cols}"
        if rows * cols > MAX_GRID_PAGES:
            return False, f"Total pages (rows×cols) must be ≤ {MAX_GRID_PAGES}, got: {rows * cols}"
        return True, None

    @staticmethod
    def validate_dpi(dpi: int) -> Tuple[bool, Optional[str]]:
        """
        Validate the DPI value.

        Args:
            dpi: DPI value to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if dpi <= 0:
            return False, f"DPI must be positive, got: {dpi}"

        if dpi < MIN_DPI:
            return False, f"DPI too low for quality printing: {dpi}. Minimum recommended is {MIN_DPI}."

        if dpi > MAX_DPI:
            return False, f"DPI extremely high, may cause performance issues: {dpi}"

        if dpi > 600:
            # Warning but not an error
            print(f"Warning: High DPI ({dpi}) will create large files and increase processing time significantly.")

        return True, None

    @staticmethod
    def validate_output_dir(output_dir: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the output directory exists or can be created.

        Args:
            output_dir: Directory path to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check if the directory exists
        if os.path.exists(output_dir):
            if not os.path.isdir(output_dir):
                return False, f"Output path exists but is not a directory: {output_dir}"
            return True, None

        # Try to create the directory
        try:
            os.makedirs(output_dir, exist_ok=True)
            return True, None
        except Exception as e:
            return False, f"Failed to create output directory: {str(e)}"

    @staticmethod
    def validate_format(format_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the output format.

        Args:
            format_str: Format string to validate (e.g., "png", "jpg")

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not format_str:  # Empty format means use original
            return True, None

        valid_formats = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]
        if format_str.lower() not in valid_formats:
            return False, f"Unsupported format: {format_str}. Use one of {', '.join(valid_formats)}"

        return True, None