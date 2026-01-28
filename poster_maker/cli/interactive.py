
"""
Interactive CLI mode for Poster Maker.

Provides a guided, step-by-step experience for creating posters
with smart recommendations based on image properties.
"""

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import questionary
from PIL import Image
from questionary import Style

from ..utils.validators import (
    InputValidator,
    MAX_DPI,
    MAX_GRID_DIM,
    MAX_GRID_PAGES,
    MAX_PARTS,
    MIN_DPI,
    parse_grid,
)

# Custom style for questionary prompts
CUSTOM_STYLE = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
    ("separator", "fg:gray"),
    ("instruction", "fg:gray italic"),
    ("text", "fg:white"),
])


@dataclass
class InteractiveConfig:
    """Configuration gathered from interactive prompts."""

    file_path: str
    mode: str  # "grid" or "strip"
    grid: Optional[Tuple[int, int]] = None  # (rows, cols) for grid mode
    parts: int = 3  # for strip mode
    dpi: int = 300
    resize_mode: str = "maintain"
    generate_pdf: bool = True
    pdf_instructions: bool = True
    pdf_page_numbers: bool = False
    pdf_grid_overlay: bool = False
    pdf_assembly_aids: bool = True
    pdf_compress: bool = False
    pdf_quality: int = 90
    pdf_duplex: bool = True  # Add back-pages with position info for duplex printing
    preview_pdf: bool = True
    cleanup_parts: bool = True  # Delete image parts after PDF generation
    cleanup_resized: bool = False  # Delete resized image after PDF generation
    verbose: bool = False
    output_dir: Optional[str] = None
    output_format: Optional[str] = None
    duplicate: bool = False


class InteractiveCLI:
    """Interactive command-line interface for Poster Maker."""

    # A4 dimensions in mm
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297

    # Common grid presets with descriptions
    GRID_PRESETS = [
        ("2x2", 2, 2, "Small poster ~42×59cm (4 pages)"),
        ("2x3", 2, 3, "Medium vertical ~42×88cm (6 pages)"),
        ("3x2", 3, 2, "Medium horizontal ~63×59cm (6 pages)"),
        ("3x3", 3, 3, "Large poster ~63×88cm (9 pages)"),
        ("3x4", 3, 4, "Wide panorama ~63×118cm (12 pages)"),
        ("4x3", 4, 3, "Tall panorama ~84×88cm (12 pages)"),
        ("4x4", 4, 4, "Wall mural ~84×118cm (16 pages)"),
    ]

    DPI_OPTIONS = [
        (150, "Draft quality - fast printing, visible pixels up close"),
        (200, "Good quality - balanced for most posters"),
        (300, "High quality - sharp details, larger file size"),
        (600, "Professional - maximum detail, very large files"),
    ]

    RESIZE_MODES = [
        ("maintain", "Maintain aspect ratio (may have white borders)"),
        ("stretch", "Stretch to fill (may distort image)"),
        ("crop", "Crop to fill (may lose edges)"),
        ("pad_white", "Pad with white to fill"),
        ("pad_black", "Pad with black to fill"),
    ]

    def __init__(self) -> None:
        """Initialize the interactive CLI."""
        self._check_tty()

    def _check_tty(self) -> None:
        """Check if running in an interactive terminal."""
        if not sys.stdin.isatty():
            print("❌ Interactive mode requires a terminal (TTY).")
            print("💡 Tip: Use standard CLI arguments instead: python main.py -f image.png --grid 3x3")
            sys.exit(1)

    def run(self) -> InteractiveConfig:
        """
        Run the interactive CLI flow.

        Returns:
            InteractiveConfig with all user selections.
        """
        self._print_welcome()

        # Step 1: Get file path
        file_path = self._prompt_file_path()

        # Step 2: Analyze image and show info
        img_info = self._analyze_image(file_path)
        self._print_image_info(img_info)

        # Step 3: Choose mode (grid or strip)
        mode = self._prompt_mode()

        # Step 4: Mode-specific options
        if mode == "grid":
            grid = self._prompt_grid_size(img_info)
            parts = grid[0] * grid[1]
        else:
            grid = None
            parts = self._prompt_strip_parts(img_info)

        # Step 5: DPI selection with recommendation
        dpi = self._prompt_dpi(img_info, grid, parts)

        # Step 6: Resize mode
        resize_mode = self._prompt_resize_mode()

        # Step 7: PDF options
        pdf_opts = self._prompt_pdf_options()

        # Step 8: Additional options
        verbose, output_dir = self._prompt_additional_options()

        # Build and return config
        config = InteractiveConfig(
            file_path=file_path,
            mode=mode,
            grid=grid,
            parts=parts,
            dpi=dpi,
            resize_mode=resize_mode,
            generate_pdf=pdf_opts["generate_pdf"],
            pdf_instructions=pdf_opts["pdf_instructions"],
            pdf_page_numbers=pdf_opts["pdf_page_numbers"],
            pdf_grid_overlay=pdf_opts["pdf_grid_overlay"],
            pdf_assembly_aids=pdf_opts["pdf_assembly_aids"],
            pdf_duplex=pdf_opts.get("pdf_duplex", False),
            pdf_compress=pdf_opts["pdf_compress"],
            pdf_quality=pdf_opts["pdf_quality"],
            preview_pdf=pdf_opts["preview_pdf"],
            cleanup_parts=pdf_opts.get("cleanup_parts", True),
            cleanup_resized=pdf_opts.get("cleanup_resized", False),
            verbose=verbose,
            output_dir=output_dir,
        )

        self._print_summary(config, img_info)

        if not questionary.confirm("Proceed with these settings?", default=True, style=CUSTOM_STYLE).ask():
            print("\n👋 Cancelled. Run again when ready!")
            sys.exit(0)

        return config

    def _print_welcome(self) -> None:
        """Print welcome banner."""
        print()
        print("╭─────────────────────────────────────────────────╮")
        print("│        🖼️  Poster Maker - Interactive Mode       │")
        print("│     Split images into printable A4 posters      │")
        print("╰─────────────────────────────────────────────────╯")
        print()

    def _prompt_file_path(self) -> str:
        """Prompt for and validate image file path."""
        while True:
            file_path = questionary.path(
                "Enter image path:",
                only_directories=False,
                style=CUSTOM_STYLE,
            ).ask()

            if file_path is None:
                print("\n👋 Cancelled.")
                sys.exit(0)

            file_path = os.path.expanduser(file_path.strip())

            # Validate
            valid, error = InputValidator.validate_file_path(file_path)
            if valid:
                return file_path

            print(f"  ❌ {error}")
            print("  💡 Please enter a valid image file path.\n")

    def _analyze_image(self, file_path: str) -> Dict[str, Any]:
        """Analyze image and return properties."""
        try:
            img = Image.open(file_path)
            width, height = img.size
            file_size = os.path.getsize(file_path)
            aspect_ratio = width / height if height > 0 else 1.0

            return {
                "path": file_path,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "file_size": file_size,
                "format": img.format,
                "mode": img.mode,
                "orientation": "landscape" if width > height else "portrait" if height > width else "square",
            }
        except Exception as e:
            print(f"  ❌ Error reading image: {e}")
            sys.exit(1)

    def _print_image_info(self, info: Dict[str, Any]) -> None:
        """Display image information."""
        size_mb = info["file_size"] / (1024 * 1024)
        print(f"\n  ✓ Image loaded: {os.path.basename(info['path'])}")
        print(f"    📐 Dimensions: {info['width']}×{info['height']}px ({info['orientation']})")
        print(f"    📦 File size: {size_mb:.2f} MB | Format: {info['format']}")
        print()

    def _prompt_mode(self) -> str:
        """Prompt for splitting mode."""
        choices = [
            questionary.Choice("📊 2D Grid (PosteRazor-style) - Split into rows × columns", value="grid"),
            questionary.Choice("📏 1D Strip - Split horizontally or vertically only", value="strip"),
        ]

        mode = questionary.select(
            "What type of poster would you like to create?",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if mode is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        return mode

    def _prompt_grid_size(self, img_info: Dict[str, Any]) -> Tuple[int, int]:
        """Prompt for grid size with smart recommendations."""
        recommended = self._recommend_grid(img_info)

        choices = []
        for label, rows, cols, desc in self.GRID_PRESETS:
            is_recommended = (rows, cols) == recommended
            marker = " ⭐ recommended" if is_recommended else ""
            choice_label = f"{label} - {desc}{marker}"
            choices.append(questionary.Choice(choice_label, value=(rows, cols)))

        choices.append(questionary.Choice("✏️  Custom grid size...", value="custom"))

        # Find default index
        default_idx = 0
        for i, (label, rows, cols, desc) in enumerate(self.GRID_PRESETS):
            if (rows, cols) == recommended:
                default_idx = i
                break

        selection = questionary.select(
            "Select grid size:",
            choices=choices,
            default=choices[default_idx],
            style=CUSTOM_STYLE,
        ).ask()

        if selection is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        if selection == "custom":
            return self._prompt_custom_grid()

        return selection

    def _prompt_custom_grid(self) -> Tuple[int, int]:
        """Prompt for custom grid dimensions."""
        while True:
            grid_str = questionary.text(
                f"Enter custom grid (e.g., 5x3 for 5 rows × 3 columns, max {MAX_GRID_DIM}×{MAX_GRID_DIM}, max {MAX_GRID_PAGES} pages):",
                style=CUSTOM_STYLE,
            ).ask()

            if grid_str is None:
                print("\n👋 Cancelled.")
                sys.exit(0)

            parsed = parse_grid(grid_str)
            if parsed is None:
                print("  ❌ Invalid format. Use RxC format (e.g., 3x4, 5x2)")
                continue

            rows, cols = parsed
            valid, error = InputValidator.validate_grid(rows, cols)
            if valid:
                return (rows, cols)

            print(f"  ❌ {error}")

    def _prompt_strip_parts(self, img_info: Dict[str, Any]) -> int:
        """Prompt for number of strip parts."""
        recommended = self._recommend_parts(img_info)

        choices = []
        for n in [2, 3, 4, 5, 6, 8, 10]:
            is_recommended = n == recommended
            marker = " ⭐ recommended" if is_recommended else ""
            choices.append(questionary.Choice(f"{n} parts{marker}", value=n))

        choices.append(questionary.Choice("✏️  Custom number...", value="custom"))

        selection = questionary.select(
            "How many parts to split into?",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if selection is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        if selection == "custom":
            return self._prompt_custom_parts()

        return selection

    def _prompt_custom_parts(self) -> int:
        """Prompt for custom number of parts."""
        while True:
            parts_str = questionary.text(
                f"Enter number of parts (1-{MAX_PARTS}):",
                style=CUSTOM_STYLE,
            ).ask()

            if parts_str is None:
                print("\n👋 Cancelled.")
                sys.exit(0)

            try:
                parts = int(parts_str)
                valid, error = InputValidator.validate_parts(parts)
                if valid:
                    return parts
                print(f"  ❌ {error}")
            except ValueError:
                print("  ❌ Please enter a valid number.")

    def _prompt_dpi(
        self, img_info: Dict[str, Any], grid: Optional[Tuple[int, int]], parts: int
    ) -> int:
        """Prompt for DPI with smart recommendation."""
        recommended = self._recommend_dpi(img_info, grid, parts)

        choices = []
        for dpi, desc in self.DPI_OPTIONS:
            is_recommended = dpi == recommended
            marker = " ⭐ recommended" if is_recommended else ""
            choices.append(questionary.Choice(f"{dpi} DPI - {desc}{marker}", value=dpi))

        choices.append(questionary.Choice("✏️  Custom DPI...", value="custom"))

        selection = questionary.select(
            "Select print quality (DPI):",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if selection is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        if selection == "custom":
            return self._prompt_custom_dpi()

        return selection

    def _prompt_custom_dpi(self) -> int:
        """Prompt for custom DPI."""
        while True:
            dpi_str = questionary.text(
                f"Enter DPI ({MIN_DPI}-{MAX_DPI}):",
                style=CUSTOM_STYLE,
            ).ask()

            if dpi_str is None:
                print("\n👋 Cancelled.")
                sys.exit(0)

            try:
                dpi = int(dpi_str)
                valid, error = InputValidator.validate_dpi(dpi)
                if valid:
                    return dpi
                print(f"  ❌ {error}")
            except ValueError:
                print("  ❌ Please enter a valid number.")

    def _prompt_resize_mode(self) -> str:
        """Prompt for resize mode."""
        choices = [
            questionary.Choice(f"{mode} - {desc}", value=mode)
            for mode, desc in self.RESIZE_MODES
        ]

        selection = questionary.select(
            "How should the image be resized?",
            choices=choices,
            default=choices[0],
            style=CUSTOM_STYLE,
        ).ask()

        if selection is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        return selection

    def _prompt_pdf_options(self) -> Dict[str, Any]:
        """Prompt for PDF generation options."""
        generate_pdf = questionary.confirm(
            "Generate PDF with all parts?",
            default=True,
            style=CUSTOM_STYLE,
        ).ask()

        if generate_pdf is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        if not generate_pdf:
            return {
                "generate_pdf": False,
                "pdf_instructions": False,
                "pdf_page_numbers": False,
                "pdf_grid_overlay": False,
                "pdf_assembly_aids": False,
                "pdf_duplex": False,
                "pdf_compress": False,
                "pdf_quality": 90,
                "preview_pdf": False,
                "cleanup_parts": False,  # Don't cleanup if no PDF
                "cleanup_resized": False,
            }

        # PDF sub-options
        pdf_features = questionary.checkbox(
            "Select PDF features:",
            choices=[
                questionary.Choice("📋 Assembly instructions page", value="instructions", checked=True),
                questionary.Choice("🔢 Page numbers on each page", value="page_numbers", checked=False),
                questionary.Choice("📊 Grid overlay on all pages (20mm lines)", value="grid_overlay", checked=False),
                questionary.Choice("📐 Assembly aids (corner marks)", value="assembly_aids", checked=True),
                questionary.Choice("🖨️ Duplex back-pages (position info for double-sided printing)", value="duplex", checked=True),
                questionary.Choice("🗜️ Compress images in PDF", value="compress", checked=False),
                questionary.Choice("👁️ Preview PDF after creation", value="preview", checked=True),
            ],
            style=CUSTOM_STYLE,
        ).ask()

        if pdf_features is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        # Cleanup options
        cleanup_features = questionary.checkbox(
            "Cleanup after PDF generation:",
            choices=[
                questionary.Choice(
                    "🗑️ Delete individual image parts (only keep PDF)",
                    value="cleanup_parts",
                    checked=True,
                ),
                questionary.Choice(
                    "🗑️ Also delete resized source image",
                    value="cleanup_resized",
                    checked=False,
                ),
            ],
            style=CUSTOM_STYLE,
        ).ask()

        if cleanup_features is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        return {
            "generate_pdf": True,
            "pdf_instructions": "instructions" in pdf_features,
            "pdf_page_numbers": "page_numbers" in pdf_features,
            "pdf_grid_overlay": "grid_overlay" in pdf_features,
            "pdf_assembly_aids": "assembly_aids" in pdf_features,
            "pdf_duplex": "duplex" in pdf_features,
            "pdf_compress": "compress" in pdf_features,
            "pdf_quality": 90,
            "preview_pdf": "preview" in pdf_features,
            "cleanup_parts": "cleanup_parts" in cleanup_features,
            "cleanup_resized": "cleanup_resized" in cleanup_features,
        }

    def _prompt_additional_options(self) -> Tuple[bool, Optional[str]]:
        """Prompt for additional options."""
        verbose = questionary.confirm(
            "Show detailed progress?",
            default=False,
            style=CUSTOM_STYLE,
        ).ask()

        if verbose is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        custom_output = questionary.confirm(
            "Use custom output directory?",
            default=False,
            style=CUSTOM_STYLE,
        ).ask()

        if custom_output is None:
            print("\n👋 Cancelled.")
            sys.exit(0)

        output_dir = None
        if custom_output:
            output_dir = questionary.path(
                "Enter output directory:",
                only_directories=True,
                style=CUSTOM_STYLE,
            ).ask()

            if output_dir is None:
                print("\n👋 Cancelled.")
                sys.exit(0)

        return verbose, output_dir

    def _recommend_grid(self, img_info: Dict[str, Any]) -> Tuple[int, int]:
        """Recommend grid size based on image properties."""
        aspect = img_info["aspect_ratio"]

        # Match grid aspect ratio to image aspect ratio
        if aspect > 1.5:  # Wide panorama
            return (3, 4)  # 12 pages, wide
        elif aspect > 1.2:  # Landscape
            return (3, 3)  # 9 pages
        elif aspect > 0.8:  # Near square
            return (3, 3)  # 9 pages
        elif aspect > 0.6:  # Portrait
            return (3, 2)  # 6 pages
        else:  # Tall
            return (4, 3)  # 12 pages, tall

    def _recommend_parts(self, img_info: Dict[str, Any]) -> int:
        """Recommend number of parts for strip mode."""
        aspect = img_info["aspect_ratio"]

        if aspect > 2.0:  # Very wide
            return 6
        elif aspect > 1.5:  # Wide
            return 4
        elif aspect < 0.5:  # Very tall
            return 6
        elif aspect < 0.7:  # Tall
            return 4
        else:
            return 3

    def _recommend_dpi(
        self, img_info: Dict[str, Any], grid: Optional[Tuple[int, int]], parts: int
    ) -> int:
        """Recommend DPI based on image resolution and output size."""
        width, height = img_info["width"], img_info["height"]

        if grid:
            rows, cols = grid
            # Calculate output size in mm
            output_width_mm = cols * self.A4_WIDTH_MM
            output_height_mm = rows * self.A4_HEIGHT_MM
        else:
            # For strips, estimate based on parts
            output_width_mm = self.A4_WIDTH_MM
            output_height_mm = parts * self.A4_HEIGHT_MM

        # Convert output size to inches
        output_width_in = output_width_mm / 25.4
        output_height_in = output_height_mm / 25.4

        # Calculate effective DPI if we used the full image
        effective_dpi_x = width / output_width_in
        effective_dpi_y = height / output_height_in
        effective_dpi = min(effective_dpi_x, effective_dpi_y)

        # Recommend based on available resolution
        if effective_dpi >= 300:
            return 300  # Can do high quality
        elif effective_dpi >= 200:
            return 200  # Good quality
        elif effective_dpi >= 150:
            return 150  # Draft quality
        else:
            return 150  # Best we can do

    def _print_summary(self, config: InteractiveConfig, img_info: Dict[str, Any]) -> None:
        """Print configuration summary before processing."""
        print("\n" + "─" * 50)
        print("📋 Configuration Summary")
        print("─" * 50)
        print(f"  📁 Input:  {os.path.basename(config.file_path)}")
        print(f"  📐 Source: {img_info['width']}×{img_info['height']}px")

        if config.mode == "grid":
            rows, cols = config.grid
            print(f"  🔲 Layout: {rows}×{cols} grid ({config.parts} pages)")
            output_w = cols * self.A4_WIDTH_MM / 10
            output_h = rows * self.A4_HEIGHT_MM / 10
            print(f"  📏 Output: ~{output_w:.0f}×{output_h:.0f}cm")
        else:
            print(f"  📏 Layout: {config.parts} strip parts")

        print(f"  🖨️  DPI:    {config.dpi}")
        print(f"  📄 PDF:    {'Yes' if config.generate_pdf else 'No'}")
        print("─" * 50 + "\n")


def run_interactive() -> InteractiveConfig:
    """Entry point for interactive mode."""
    cli = InteractiveCLI()
    return cli.run()