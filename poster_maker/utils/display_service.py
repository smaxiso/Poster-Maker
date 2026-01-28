
# poster_maker/utils/display_service.py
import json
import logging
import os
from typing import Any, Dict


class DisplayService:
    """Service for display and formatting operations."""

    def __init__(self, logger: logging.Logger):
        """Initialize the display service."""
        self.logger = logger

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Human-readable size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @staticmethod
    def display_dpi_guide() -> None:
        """Display DPI selection guidelines."""
        print("\nDPI SELECTION GUIDE:")
        print("=" * 80)
        print("\nRecommended DPI ranges based on use case:")
        print("------------------------------------------")
        print("72-150 DPI:   Screen display, draft prints, very large posters viewed from a distance")
        print("             • Smaller file sizes, faster processing")
        print("             • Good for: Temporary displays, event backdrops, very large format prints")
        print("\n150-300 DPI:  Standard printing, typical posters (RECOMMENDED)")
        print("             • Good balance between quality and file size")
        print("             • Good for: Most poster applications, normal viewing distance (2-3 feet)")
        print("             • 300 DPI is the industry standard for most print applications")
        print("\n300-600 DPI:  High-quality prints, professional photography")
        print("             • Excellent print quality, suitable for close inspection")
        print("             • Good for: Art prints, photography exhibitions, premium posters")
        print("\n600-1200 DPI: Premium art reproduction, fine art")
        print("             • Maximum print quality with no visible pixelation")
        print("             • Warning: Very large file sizes, significantly longer processing times")
        print("\nAbove 1200:   Not recommended - excessive for most purposes")
        print("             • Extremely large files, severe processing times, minimal quality improvement")

        print("\nDPI Selection Based on Print Size and Viewing Distance:")
        print("----------------------------------------------------")
        print("Viewing Distance | Small Poster (A3/A2) | Medium Poster (A1) | Large Poster (A0+)")
        print("----------------|---------------------|-------------------|------------------")
        print("Close (1-2 ft)  | 300-600 DPI         | 250-300 DPI       | 150-250 DPI")
        print("Normal (3-6 ft) | 200-300 DPI         | 150-250 DPI       | 100-150 DPI")
        print("Far (6+ ft)     | 150 DPI             | 100-150 DPI       | 72-100 DPI")

        print("\nNOTE: Higher DPI doesn't create detail that wasn't in the original image.")
        print("      Increasing DPI simply spreads the same pixels over a smaller print area.")
        print("=" * 80)

    def display_summary(self, result: Dict[str, Any], summary_level: str = 'basic',
                        save_summary: bool = False, pdf_info: Dict[str, Any] = None,
                        log_file: str = None) -> None:
        """
        Display processing summary using Rich for nicer formatting.

        Args:
            result: Processing result
            summary_level: Level of detail to display ('minimal', 'basic', 'detailed')
            save_summary: Whether to save the summary as a JSON file
            pdf_info: Information about generated PDF (if applicable)
            log_file: Path to the log file (optional)
        """
        # Try importing rich, fall back to basic print if not available
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            from rich.text import Text
            from rich import box
            console = Console()
            has_rich = True
        except ImportError:
            has_rich = False
            
        output_paths = result["output_paths"]
        summary = result["summary"]
        cleanup_info = result.get("cleanup", {})
        
        # Log internal completion info
        self.logger.info(f"Successfully created {len(output_paths['parts'])} poster parts")
        
        # Calculate sizes
        resized_size = summary['output']['resized_image']['size_bytes']
        parts_size = sum(part['size_bytes'] for part in summary['output']['parts'])
        pdf_size = pdf_info.get('size_bytes', 0) if pdf_info else 0
        total_time = summary['timing'].get('total_seconds', 0)

        if not has_rich:
            # Fallback for systems without rich
            print("\n" + "=" * 80)
            print(f"PROCESSING COMPLETE ({total_time:.2f}s)")
            print("=" * 80)
            if pdf_info:
                print(f"PDF Output: {pdf_info['path']} ({self.format_size(pdf_size)})")
            if log_file:
                print(f"Log File: {log_file}")
            return

        # Create Main Summary Table
        table = Table(box=box.ROUNDED, show_header=False, expand=True, border_style="blue")
        table.add_column("Key", style="cyan", width=20)
        table.add_column("Value", style="white")

        # 1. Processing Stats
        table.add_row("Source Image", f"{summary['source_image']['path']}")
        table.add_row("Resolution", f"{summary['source_image']['dimensions']['width']}x{summary['source_image']['dimensions']['height']} px")
        table.add_row("Output Layout", f"{len(summary['output']['parts'])} parts @ {summary['process_options']['dpi']} DPI")
        table.add_row("Processing Time", f"[bold green]{total_time:.2f} seconds[/bold green]")
        
        table.add_section()

        # 2. Output Files
        if pdf_info:
            pdf_path = pdf_info['path']
            # Highlight the PDF path as it's the main artifact
            table.add_row("PDF Output", f"[bold yellow]{pdf_path}[/bold yellow] ({self.format_size(pdf_size)})")
        
        if not cleanup_info.get("parts_deleted"):
             parts_dir = os.path.dirname(output_paths['parts'][0])
             table.add_row("Image Parts", f"{parts_dir}")

        # 3. Cleanup Info
        if cleanup_info.get("parts_deleted", 0) > 0:
             freed = cleanup_info.get("bytes_freed", 0)
             table.add_row("Cleanup", f"[dim]Deleted intermediate files ({self.format_size(freed)} freed)[/dim]")

        # 4. Log File
        if log_file:
             table.add_section()
             table.add_row("Log File", f"[dim]{log_file}[/dim]")

        # Print the panel
        console.print()
        console.print(Panel(
            table,
            title="[bold blue]🖼️  Poster Maker - Execution Summary[/bold blue]",
            border_style="blue",
            expand=False
        ))
        console.print()

        # Save summary file if requested
        if save_summary:
            summary_file = os.path.join(
                os.path.dirname(output_paths['parts'][0]),
                f"{os.path.basename(summary['source_image']['path']).split('.')[0]}_summary.json"
            )
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Summary saved to: {summary_file}")
            console.print(f"[dim]JSON summary saved to: {summary_file}[/dim]")
            console.print()