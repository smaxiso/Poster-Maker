
# poster_maker/utils/memory_service.py
import logging
from typing import Optional, Tuple


class MemoryService:
    """Service for memory-related operations and estimations."""

    def __init__(self, logger: logging.Logger):
        """Initialize the memory service."""
        self.logger = logger

    @staticmethod
    def estimate_memory_usage(width: int, height: int, parts: int, dpi: int, output_format: str, 
                              grid: Optional[Tuple[int, int]] = None) -> Tuple[float, Optional[float]]:
        """
        Estimate maximum RAM usage during processing.

        This estimates the peak RAM needed during image processing,
        not the final output file size (which will be smaller).

        Args:
            width: Source image width in pixels
            height: Source image height in pixels
            parts: Total number of parts
            dpi: Output DPI
            output_format: Output format (affects memory calculation)
            grid: Optional (rows, cols) tuple for grid layout

        Returns:
            Tuple[float, Optional[float]]: (estimated_memory_mb, memory_percentage_of_system)
        """
        # Calculate target dimensions
        a4_width_inches = 8.27
        a4_height_inches = 11.69
        
        if grid:
            rows, cols = grid
            target_width = int(a4_width_inches * dpi * cols)
            target_height = int(a4_height_inches * dpi * rows)
        else:
            # 1D strip mode (horizontal parts)
            target_width = int(a4_width_inches * dpi * parts)
            # Height will be scaled proportionally later
            target_height = 0  # Placeholder

        # Calculate scaling factor
        scale_factor = target_width / width
        if target_height == 0:
            target_height = int(height * scale_factor)

        # Calculate bytes per pixel (for in-memory representation)
        bytes_per_pixel = 4  # RGBA format is used internally

        # Calculate memory for different stages
        original_image_memory = width * height * bytes_per_pixel
        resized_image_memory = target_width * target_height * bytes_per_pixel

        # Working memory for processing (consider the largest part)
        largest_part_memory = (target_width // parts + 1) * target_height * bytes_per_pixel

        # More realistic peak memory estimate:
        # - During resize: original + resized + PIL buffers (~20%)
        # - During split/save: resized + 2 parts (current + being saved)
        # These stages don't overlap, so take the maximum
        resize_phase_memory = original_image_memory + resized_image_memory * 1.2
        split_phase_memory = resized_image_memory + largest_part_memory * 2

        peak_memory = max(resize_phase_memory, split_phase_memory)

        # Convert to MB with 30% safety margin (covers PIL internal buffers)
        total_memory_mb = (peak_memory / (1024 * 1024)) * 1.3

        # Factor in the system's available memory
        try:
            import psutil
            system_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
            memory_percentage = (total_memory_mb / system_memory) * 100
            return total_memory_mb, memory_percentage
        except ImportError:
            # If psutil isn't available, just return the estimated memory
            return total_memory_mb, None

    def display_memory_warning(self, memory_estimate: Tuple[float, Optional[float]]) -> bool:
        """
        Display warning for high memory usage and ask for confirmation if necessary.

        Args:
            memory_estimate: Tuple of (estimated_memory_mb, memory_percentage)

        Returns:
            bool: True if should continue, False if operation was cancelled
        """
        memory_mb, memory_percentage = memory_estimate

        # Define reasonable thresholds
        HIGH_MEMORY_MB = 2000  # 2GB
        VERY_HIGH_MEMORY_MB = 4000  # 4GB
        HIGH_PERCENTAGE = 50  # 50% of system RAM

        # Determine if this is a high memory operation
        is_high_memory = memory_mb > HIGH_MEMORY_MB
        is_very_high_memory = memory_mb > VERY_HIGH_MEMORY_MB
        is_high_percentage = memory_percentage and memory_percentage > HIGH_PERCENTAGE

        if is_high_memory or is_high_percentage:
            # Prepare warning message
            warning = [
                f"Warning: This operation may require significant RAM during processing:",
                f"• Estimated peak RAM usage: {memory_mb:.1f} MB ({memory_mb / 1024:.2f} GB)"
            ]

            if memory_percentage:
                warning.append(f"• This represents approximately {memory_percentage:.1f}% of your system's RAM")

            # warning.append("Note: The final output files will be much smaller than this RAM estimate.")
            warning.append("Consider reducing DPI or number of parts if you experience performance issues.")

            # Log and print the warning
            self.logger.warning(f"Estimated peak RAM usage is high: {memory_mb:.2f} MB" +
                                (f" ({memory_percentage:.1f}% of system RAM)" if memory_percentage else ""))

            for line in warning:
                print(line)

            # For very high memory usage, ask for confirmation
            if is_very_high_memory or (memory_percentage and memory_percentage > 70):
                while True:
                    response = input("\nContinue with this high-memory operation? (y/n): ").strip().lower()
                    if response == 'y':
                        return True
                    elif response == 'n':
                        print("Operation cancelled by user.")
                        return False
                    # If empty or invalid, loop again
                    print("Please enter 'y' to continue or 'n' to cancel.")

        return True