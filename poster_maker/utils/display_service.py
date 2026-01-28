
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
                        save_summary: bool = False, pdf_info: Dict[str, Any] = None) -> None:
        """
        Display processing summary.

        Args:
            result: Processing result
            summary_level: Level of detail to display ('minimal', 'basic', 'detailed')
            save_summary: Whether to save the summary as a JSON file
            pdf_info: Information about generated PDF (if applicable)
        """
        output_paths = result["output_paths"]
        summary = result["summary"]

        # Check if cleanup was performed
        cleanup_info = result.get("cleanup", {})
        parts_cleaned = cleanup_info.get("parts_deleted", 0) > 0
        resized_cleaned = cleanup_info.get("resized_deleted", False)

        # Log completion info with cleanup status
        self.logger.info(f"Successfully created {len(output_paths['parts'])} poster parts")
        if resized_cleaned:
            self.logger.info(f"Resized image was cleaned up (originally: {output_paths['resized']})")
        else:
            self.logger.info(f"Resized image saved to: {output_paths['resized']}")
        if parts_cleaned:
            self.logger.info(f"Poster parts were cleaned up (originally in: {os.path.dirname(output_paths['parts'][0])})")
        else:
            self.logger.info(f"Poster parts saved to: {os.path.dirname(output_paths['parts'][0])}")

        # Calculate total sizes including PDF if available
        resized_size_bytes = summary['output']['resized_image']['size_bytes']
        parts_size_bytes = sum(part['size_bytes'] for part in summary['output']['parts'])
        pdf_size_bytes = pdf_info.get('size_bytes', 0) if pdf_info else 0

        # Calculate total combined output size (only what remains after cleanup)
        if parts_cleaned:
            remaining_parts_size = 0
        else:
            remaining_parts_size = parts_size_bytes

        if resized_cleaned:
            remaining_resized_size = 0
        else:
            remaining_resized_size = resized_size_bytes

        total_output_size_bytes = remaining_resized_size + remaining_parts_size + pdf_size_bytes

        # Human-readable summary always shown
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Source image: {summary['source_image']['dimensions']['width']}x"
              f"{summary['source_image']['dimensions']['height']} pixels "
              f"({self.format_size(summary['source_image']['size_bytes'])})")
        print(f"Output: {len(summary['output']['parts'])} poster parts at {summary['process_options']['dpi']} DPI")

        # Print detailed size breakdown
        print("\nOutput Size Breakdown:")
        if resized_cleaned:
            print(f"  • Resized image: {self.format_size(resized_size_bytes)} (deleted)")
        else:
            print(f"  • Resized image: {self.format_size(resized_size_bytes)}")

        if parts_cleaned:
            print(f"  • Image parts: {self.format_size(parts_size_bytes)} (deleted - {len(summary['output']['parts'])} files)")
        else:
            print(f"  • Image parts: {self.format_size(parts_size_bytes)} (across {len(summary['output']['parts'])} files)")

        if pdf_info:
            print(f"  • PDF document: {self.format_size(pdf_size_bytes)} ({pdf_info['pages']} pages)")

        # Show total remaining output
        if parts_cleaned or resized_cleaned:
            print(f"  • Total remaining: {self.format_size(total_output_size_bytes)}")
        else:
            print(f"  • Total output: {self.format_size(total_output_size_bytes)}")
        print(f"\nProcessing time: {summary['timing']['total_seconds']:.2f} seconds")

        # Add PDF information to summary if provided
        if pdf_info:
            # Include PDF info in the summary
            summary["pdf_output"] = pdf_info

        # Show detailed summary based on level
        if summary_level in ['basic', 'detailed']:
            print("\nSUMMARY:")

            if summary_level == 'basic':
                # Show simplified summary of image parts
                print("Image Parts:")
                for i, part in enumerate(summary['output']['parts']):
                    print(f"  Part {i + 1}: {part['dimensions']['width']}x{part['dimensions']['height']} "
                          f"pixels ({self.format_size(part['size_bytes'])})")

                # If PDF was generated, show basic PDF info
                if pdf_info:
                    print("\nPDF Output:")
                    print(f"  File: {pdf_info['path']}")
                    print(f"  Size: {self.format_size(pdf_info['size_bytes'])}")
                    print(f"  Pages: {pdf_info['pages']}")
                    if 'features' in pdf_info and pdf_info['features']:
                        print(f"  Features: {', '.join(pdf_info['features'])}")

                    # Show compression info if available
                    if 'optimization' in pdf_info and pdf_info['optimization'].get('compress_images'):
                        print(f"  Compression: Quality {pdf_info['optimization']['compression_quality']}%")
                        if pdf_info['optimization'].get('downsample_images'):
                            print(f"  Downsampling: To {pdf_info['optimization']['downsample_resolution_dpi']} DPI")

            elif summary_level == 'detailed':
                # Show detailed JSON summary
                print(json.dumps(summary, indent=2))

        # Save summary file if requested
        if save_summary:
            summary_file = os.path.join(
                os.path.dirname(output_paths['parts'][0]),
                f"{os.path.basename(summary['source_image']['path']).split('.')[0]}_summary.json"
            )
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Summary saved to: {summary_file}")