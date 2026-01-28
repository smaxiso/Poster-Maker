
#!/usr/bin/env python3
"""
Poster Maker - Main script to split images into multiple parts for poster creation.
"""
import os
import sys
import logging
from PIL import Image
from typing import Dict, Any, Optional, Tuple

from poster_maker.utils.logger import LoggerSetup
from poster_maker.cli.arg_parser import ArgParser
from poster_maker.utils.pdf_service import PDFService
from poster_maker.core.file_manager import FileManager
from poster_maker.utils.validators import InputValidator, parse_grid
from poster_maker.config.config_loader import ConfigLoader
from poster_maker.utils.memory_service import MemoryService
from poster_maker.core.image_processor import ImageProcessor
from poster_maker.utils.display_service import DisplayService


class PosterMakerApp:
    """Main application class for Poster Maker."""

    def __init__(self, interactive_config: Optional[Any] = None):
        """
        Initialize the Poster Maker application.

        Args:
            interactive_config: Optional config from interactive CLI mode.
        """
        # Core components
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_config()
        self.arg_parser = ArgParser(self.config)
        self.args = self.arg_parser.parse_args()

        # Apply interactive config if provided
        if interactive_config is not None:
            self._apply_interactive_config(interactive_config)

        # Validate that we have required args (file path)
        if not getattr(self.args, 'interactive', False) and not self.args.file:
            print("❌ Error: -f/--file is required (or use -i/--interactive mode)")
            sys.exit(1)

        # Set up environment with verbose setting
        self.env = self._setup_environment(verbose=self.args.verbose)
        self.logger = self.env["logger"]
        self.validator = self.env["validator"]
        self.image_processor = self.env["image_processor"]

        # Additional services
        self.memory_service = MemoryService(self.logger)
        self.display_service = DisplayService(self.logger)
        # Initialize PDF service if needed
        self.pdf_service = None
        if getattr(self.args, 'generate_pdf', False):
            self.pdf_service = PDFService(self.logger, self.config)

    def _apply_interactive_config(self, config: Any) -> None:
        """Apply interactive config to args."""
        # Core options
        self.args.file = config.file_path
        self.args.dpi = config.dpi
        self.args.verbose = config.verbose
        self.args.resize_mode = config.resize_mode

        # Output options
        if config.output_dir:
            self.args.output_dir = config.output_dir
        self.args.format = getattr(config, "output_format", None)
        self.args.duplicate = getattr(config, "duplicate", False)

        # Grid/parts mode
        if config.mode == "grid" and config.grid:
            self.args.grid = f"{config.grid[0]}x{config.grid[1]}"
            self.args.parts = config.parts
        else:
            self.args.grid = None
            self.args.parts = config.parts

        # PDF options
        self.args.generate_pdf = config.generate_pdf
        self.args.pdf_instructions = config.pdf_instructions
        self.args.pdf_page_numbers = config.pdf_page_numbers
        self.args.pdf_grid_overlay = getattr(config, "pdf_grid_overlay", False)
        self.args.pdf_assembly_aids = getattr(config, "pdf_assembly_aids", True)
        self.args.pdf_duplex = getattr(config, "pdf_duplex", False)
        self.args.pdf_compress = getattr(config, "pdf_compress", False)
        self.args.pdf_quality = getattr(config, "pdf_quality", 90)
        self.args.preview_pdf = getattr(config, "preview_pdf", True)

        # Cleanup options
        self.args.cleanup_parts = getattr(config, "cleanup_parts", True)
        self.args.cleanup_resized = getattr(config, "cleanup_resized", False)

    def _setup_environment(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Set up the environment (config, logging, etc.).

        Args:
            verbose: Whether to use verbose logging

        Returns:
            Dict[str, Any]: Dictionary with environment objects
        """
        # Set up logger
        # Parse all args into a dictionary for the logger
        arg_dict = {
            "file": self.args.file,
            "parts": self.args.parts,
            "grid": getattr(self.args, "grid", None),
            "dpi": self.args.dpi,
            "resize_mode": getattr(self.args, 'resize_mode', None),
            "verbose": verbose
        }

        # Set up logger with args
        logger_setup = LoggerSetup(self.config, arg_dict)
        logger = logger_setup.get_logger()

        # Set log level based on verbose flag
        if verbose:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)

        # Initialize components
        file_manager = FileManager(self.config, logger)
        image_processor = ImageProcessor(self.config, logger, file_manager)
        validator = InputValidator()

        return {
            "config": self.config,
            "logger": logger,
            "logger_setup": logger_setup,
            "file_manager": file_manager,
            "image_processor": image_processor,
            "validator": validator
        }

    def _validate_inputs(self) -> Tuple[bool, Optional[str]]:
        """
        Validate all input parameters.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Validate file path
        valid, error_msg = self.validator.validate_file_path(self.args.file)
        if not valid:
            return False, error_msg

        # Validate grid or parts
        grid_spec = getattr(self.args, "grid", None)
        if grid_spec:
            parsed = parse_grid(grid_spec)
            if not parsed:
                return False, f"Invalid --grid format: '{grid_spec}'. Use e.g. 2x2, 3x3, 2x3"
            valid, error_msg = self.validator.validate_grid(parsed[0], parsed[1])
            if not valid:
                return False, error_msg
        else:
            valid, error_msg = self.validator.validate_parts(self.args.parts)
            if not valid:
                return False, error_msg

        # Validate DPI
        valid, error_msg = self.validator.validate_dpi(self.args.dpi)
        if not valid:
            # show dpi usage
            self.display_service.display_dpi_guide()
            return False, error_msg

        # Validate format if specified
        if self.args.format:
            valid, error_msg = self.validator.validate_format(self.args.format)
            if not valid:
                return False, error_msg

        # Validate output directory if specified
        if self.args.output_dir:
            valid, error_msg = self.validator.validate_output_dir(self.args.output_dir)
            if not valid:
                return False, error_msg

        return True, None

    def _check_memory_requirements(self) -> bool:
        """
        Check if memory requirements are acceptable.

        Returns:
            bool: True if memory check passes or user confirms, False otherwise
        """
        try:
            # Open the image just to get dimensions for estimation
            img = Image.open(self.args.file)
            width, height = img.size

            # Calculate estimated memory usage
            output_format = self.args.format or os.path.splitext(self.args.file)[1][1:]
            parts = self._get_parts_count()
            grid = self._get_grid_tuple()
            memory_estimate = self.memory_service.estimate_memory_usage(
                width, height,
                parts,
                self.args.dpi,
                output_format,
                grid
            )

            # Display warning and get user confirmation if needed
            return self.memory_service.display_memory_warning(memory_estimate)

        except Exception as e:
            # Log but continue if memory estimation fails
            self.logger.warning(f"Couldn't estimate memory usage: {str(e)}")
            return True

    def _get_parts_count(self) -> int:
        """Return total number of parts (from --grid rows×cols or --parts)."""
        grid_spec = getattr(self.args, "grid", None)
        if grid_spec:
            parsed = parse_grid(grid_spec)
            return (parsed[0] * parsed[1]) if parsed else self.args.parts
        return self.args.parts

    def _get_grid_tuple(self) -> Optional[Tuple[int, int]]:
        """Return (rows, cols) if --grid is set, else None."""
        grid_spec = getattr(self.args, "grid", None)
        return parse_grid(grid_spec) if grid_spec else None

    def _process_image(self) -> Dict[str, Any]:
        """
        Process the image with current settings.

        Returns:
            Dict[str, Any]: Processing result
        """
        grid = self._get_grid_tuple()
        parts = self._get_parts_count()
        if grid:
            self.logger.info(f"Processing image {self.args.file} into {grid[0]}×{grid[1]} grid ({parts} parts) at {self.args.dpi} DPI")
        else:
            self.logger.info(f"Processing image {self.args.file} into {parts} parts at {self.args.dpi} DPI")

        resize_mode = getattr(self.args, 'resize_mode', "maintain")

        result = self.image_processor.process_image(
            self.args.file,
            parts,
            self.args.dpi,
            getattr(self.args, 'output_dir', None),
            getattr(self.args, 'duplicate', False),
            getattr(self.args, 'format', None),
            resize_mode,
            self.args.verbose,
            grid=grid,
        )

        return result

    def _generate_pdf(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a PDF with all poster parts.

        Args:
            result: Result from image processing

        Returns:
            PDF generation result information, or None if generation failed.
        """
        try:
            # Get custom PDF filename if provided
            pdf_filename = getattr(self.args, 'pdf_filename', None)

            if pdf_filename:
                # Make sure it has the right extension
                if not pdf_filename.lower().endswith('.pdf'):
                    pdf_filename += '.pdf'

                # Create full path using the output directory
                first_part = result["summary"]["output"]["parts"][0]
                output_dir = os.path.dirname(first_part["path"])
                pdf_path = os.path.join(output_dir, pdf_filename)
            else:
                pdf_path = None  # Let the service decide the default name

                # Apply any CLI overrides to the PDF config
            self._apply_pdf_config_overrides()

            # Check if the PDF should be previewed
            preview_pdf = getattr(self.args, 'preview_pdf', False)

            # Generate the PDF and get detailed info
            self.logger.info("Generating PDF with all poster parts...")
            out = result["summary"]["output"]
            pdf_info = self.pdf_service.generate_pdf_from_parts(
                out["parts"],
                pdf_path,
                preview=preview_pdf,
                verbose=self.args.verbose,
                grid_rows=out.get("grid_rows"),
                grid_cols=out.get("grid_cols"),
            )
            # Format sizes for display
            pdf_info["formatted_size"] = self.display_service.format_size(pdf_info["size_bytes"])
            return pdf_info

        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
            print(f"\nError generating PDF: {str(e)}")
            return None

    def _apply_pdf_config_overrides(self):
        """Apply CLI arguments to PDF configuration."""
        # Features
        if hasattr(self.args, 'pdf_page_numbers') and self.args.pdf_page_numbers is not None:
            self.config["pdf"]["features"]["page_numbers"] = self.args.pdf_page_numbers

        if hasattr(self.args, 'pdf_assembly_aids') and self.args.pdf_assembly_aids is not None:
            self.config["pdf"]["features"]["assembly_aids"] = self.args.pdf_assembly_aids

        if hasattr(self.args, 'pdf_grid_overlay') and self.args.pdf_grid_overlay:
            self.config["pdf"]["features"]["grid_overlay"] = self.args.pdf_grid_overlay

        if hasattr(self.args, 'pdf_instructions') and self.args.pdf_instructions:
            self.config["pdf"]["features"]["assembly_instructions"] = self.args.pdf_instructions

        if hasattr(self.args, 'pdf_duplex') and self.args.pdf_duplex:
            self.config["pdf"]["features"]["duplex_back_pages"] = self.args.pdf_duplex

        # Compression settings
        if hasattr(self.args, 'pdf_compress') and self.args.pdf_compress is not None:
            self.config["pdf"]["optimization"]["compress_images"] = self.args.pdf_compress

        if hasattr(self.args, 'pdf_quality') and self.args.pdf_quality is not None:
            self.config["pdf"]["optimization"]["compression_quality"] = self.args.pdf_quality

        if hasattr(self.args, 'pdf_downsample') and self.args.pdf_downsample:
            self.config["pdf"]["optimization"]["downsample_images"] = True

        if hasattr(self.args, 'pdf_dpi') and self.args.pdf_dpi is not None:
            self.config["pdf"]["optimization"]["downsample_resolution_dpi"] = self.args.pdf_dpi

    def _cleanup_temp_files(
        self, result: Dict[str, Any], pdf_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Clean up temporary image files after PDF generation.

        Args:
            result: Result from image processing
            pdf_result: Result from PDF generation

        Returns:
            Cleanup info dict, or None if no cleanup performed.
        """
        cleanup_parts = getattr(self.args, "cleanup_parts", True)
        cleanup_resized = getattr(self.args, "cleanup_resized", False)

        # Only cleanup if PDF was successfully generated
        if not pdf_result or not pdf_result.get("path"):
            return None

        # Don't cleanup if neither option is enabled
        if not cleanup_parts and not cleanup_resized:
            return None

        cleanup_info = {
            "parts_deleted": 0,
            "resized_deleted": False,
            "bytes_freed": 0,
            "files_deleted": [],
        }

        try:
            output = result.get("summary", {}).get("output", {})
            parts = output.get("parts", [])

            # Delete individual parts
            if cleanup_parts and parts:
                for part in parts:
                    part_path = part.get("path")
                    if part_path and os.path.exists(part_path):
                        try:
                            file_size = os.path.getsize(part_path)
                            os.remove(part_path)
                            cleanup_info["parts_deleted"] += 1
                            cleanup_info["bytes_freed"] += file_size
                            cleanup_info["files_deleted"].append(os.path.basename(part_path))
                            self.logger.debug(f"Deleted part: {part_path}")
                        except OSError as e:
                            self.logger.warning(f"Could not delete part {part_path}: {e}")

            # Delete resized image
            if cleanup_resized:
                resized_path = output.get("resized_image", {}).get("path")
                if resized_path and os.path.exists(resized_path):
                    try:
                        file_size = os.path.getsize(resized_path)
                        os.remove(resized_path)
                        cleanup_info["resized_deleted"] = True
                        cleanup_info["bytes_freed"] += file_size
                        cleanup_info["files_deleted"].append(os.path.basename(resized_path))
                        self.logger.debug(f"Deleted resized image: {resized_path}")
                    except OSError as e:
                        self.logger.warning(f"Could not delete resized image {resized_path}: {e}")

            # Log cleanup summary
            if cleanup_info["parts_deleted"] > 0 or cleanup_info["resized_deleted"]:
                freed_mb = cleanup_info["bytes_freed"] / (1024 * 1024)
                self.logger.info(
                    f"Cleanup: deleted {cleanup_info['parts_deleted']} parts"
                    + (", resized image" if cleanup_info["resized_deleted"] else "")
                    + f" (freed {freed_mb:.2f} MB)"
                )
                print(
                    f"\n🗑️ Cleanup: deleted {cleanup_info['parts_deleted']} image parts"
                    + (", resized image" if cleanup_info["resized_deleted"] else "")
                    + f" ({freed_mb:.2f} MB freed)"
                )

            return cleanup_info

        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
            return cleanup_info

    def run(self) -> int:
        """
        Run the Poster Maker application.

        Returns:
            int: Exit code (0 for success, non-zero for error)
        """
        try:
            self.logger.info("Starting Poster Maker - Image Splitting Tool")

            # Check for DPI guide flag
            if getattr(self.args, 'dpi_guide', False):
                self.display_service.display_dpi_guide()
                return 0

            # Validate inputs
            valid, error_msg = self._validate_inputs()
            if not valid:
                self.logger.error(error_msg)
                self._print_error_with_tips(error_msg)
                return 1

            # Check memory requirements
            if not self._check_memory_requirements():
                return 0  # User cancelled due to high memory usage

            # Process the image
            result = self._process_image()

            # Generate PDF if requested
            pdf_result = None
            if self.pdf_service:
                pdf_result = self._generate_pdf(result=result)
                if pdf_result is None:
                    self.logger.warning("PDF generation failed; continuing with image parts only.")
                else:
                    # Cleanup parts after successful PDF generation
                    cleanup_info = self._cleanup_temp_files(result, pdf_result)
                    if cleanup_info:
                        result["cleanup"] = cleanup_info

            # Get log file path if available
            log_file_path = None
            log_setup = self.env.get("logger_setup")
            if log_setup and hasattr(log_setup, "get_log_file_path"):
                log_file_path = log_setup.get_log_file_path()

            # Display summary
            summary_level = getattr(self.args, 'summary_level', 'basic')
            save_summary = getattr(self.args, 'save_summary', False)
            self.display_service.display_summary(
                result, 
                summary_level, 
                save_summary, 
                pdf_result, 
                log_file=log_file_path
            )

            self.logger.info("Processing complete")
            return 0

        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}", exc_info=True)
            self._print_error_with_tips(str(e))
            return 1

    @staticmethod
    def _print_error_with_tips(error_msg: str) -> None:
        """Print error message with contextual tips."""
        print(f"\n❌ ERROR: {error_msg}")

        msg_lower = error_msg.lower()
        if "dpi" in msg_lower:
            print("💡 Tip: Use --dpi-guide to see recommended DPI values")
        elif "file not found" in msg_lower or "not a file" in msg_lower:
            print("💡 Tip: Verify the file path is correct and the file exists")
        elif "grid" in msg_lower:
            print("💡 Tip: Use format like --grid 3x3 (rows x columns). Max 100 pages.")
        elif "parts" in msg_lower:
            print("💡 Tip: Use -n to specify number of parts (1-100)")
        elif "memory" in msg_lower:
            print("💡 Tip: Try reducing DPI (--dpi 150) or number of parts")
        elif "permission" in msg_lower:
            print("💡 Tip: Check file/folder permissions for the output directory")
        elif "corrupt" in msg_lower or "cannot open" in msg_lower:
            print("💡 Tip: The image file may be corrupted. Try re-downloading or converting it.")


def main():
    """Main entry point for the poster maker."""
    # Quick check for interactive mode before full init
    if "-i" in sys.argv or "--interactive" in sys.argv:
        from poster_maker.cli.interactive import run_interactive

        interactive_config = run_interactive()
        app = PosterMakerApp(interactive_config=interactive_config)
    else:
        app = PosterMakerApp()

    sys.exit(app.run())


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
        main()