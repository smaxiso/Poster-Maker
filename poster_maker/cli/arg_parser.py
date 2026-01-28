
import argparse
from typing import Dict, Any


class ArgParser:
    """Parse command line arguments for the poster maker."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the argument parser.

        Args:
            config: Configuration dictionary
        """
        self.config = config

    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create and configure the argument parser.

        Returns:
            argparse.ArgumentParser: Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description='Split an image into multiple equal parts for poster creation',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        default_parts = self.config["image"]["default_parts"]
        default_dpi = self.config["image"]["default_dpi"]

        # Interactive mode flag (makes -f optional)
        parser.add_argument('-i', '--interactive', action='store_true',
                            help='Run in interactive mode with guided prompts')

        parser.add_argument('-f', '--file', required=False,
                            help='Path to input image file (required unless --interactive)')

        parser.add_argument('-n', '--parts', type=int, default=default_parts,
                            help=f'Number of parts for 1D strip (default: {default_parts}). Ignored if --grid is set.')
        parser.add_argument('-g', '--grid', metavar='RxC', dest='grid',
                            help='2D grid layout (e.g. 2x2, 3x3, 2x3, 4x4). Overrides --parts. Each cell = 1 A4 page.')

        parser.add_argument('-d', '--duplicate', action='store_true',
                            help='Preserve previous output under old folder')

        parser.add_argument('-r', '--dpi', type=int, default=default_dpi,
                            help=f'DPI for output images (default: {default_dpi})')

        parser.add_argument('-o', '--output-dir',
                            help='Custom output directory (overrides default)')

        parser.add_argument('--format',
                            help='Output image format (e.g., png, jpg). Leave empty to keep original format')

        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Enable verbose logging')

        parser.add_argument('--resize-mode', choices=['maintain', 'stretch', 'crop', 'pad_white', 'pad_black'],
                            default='maintain',
                            help='How to handle aspect ratio during resizing')

        parser.add_argument('--save-summary', action='store_true',
                            help='Save processing summary as JSON file')

        parser.add_argument('--summary-level',
                            choices=['minimal', 'basic', 'detailed'],
                            default='basic',
                            help='Level of detail in the processing summary (default: basic)')

        parser.add_argument('--dpi-guide', action='store_true',
                            help='Display DPI selection guidelines and exit')

        # Basic PDF arguments
        pdf_group = parser.add_argument_group('PDF Generation')
        pdf_group.add_argument('--generate-pdf', action='store_true',
                               help='Generate a PDF with all poster parts for easy printing')
        pdf_group.add_argument('--pdf-filename',
                               help='Specify the filename for the generated PDF (with or without .pdf extension)')
        pdf_group.add_argument('--preview-pdf', action='store_true',
                               help='Open the generated PDF after creation')

        # PDF compression options
        pdf_compression = parser.add_argument_group('PDF Compression')
        pdf_compression.add_argument('--pdf-compress', action='store_true', dest='pdf_compress',
                                     help='Enable image compression in PDF (default)')
        pdf_compression.add_argument('--no-pdf-compress', action='store_false', dest='pdf_compress',
                                     help='Disable image compression in PDF')
        pdf_compression.add_argument('--pdf-quality', type=int, choices=range(1, 101), metavar="[1-100]",
                                     help='JPEG quality for PDF compression (1-100, default 90)')
        pdf_compression.add_argument('--pdf-downsample', action='store_true',
                                     help='Downsample high-resolution images in PDF')
        pdf_compression.add_argument('--pdf-dpi', type=int,
                                     help='Target DPI for downsampling (default 300)')

        # PDF feature toggles
        pdf_features = parser.add_argument_group('PDF Features')
        pdf_features.add_argument('--pdf-page-numbers', action='store_true', dest='pdf_page_numbers',
                                  help='Include page numbers in PDF')
        pdf_features.add_argument('--no-pdf-page-numbers', action='store_false', dest='pdf_page_numbers',
                                  help='Exclude page numbers from PDF')
        pdf_features.add_argument('--pdf-assembly-aids', action='store_true', dest='pdf_assembly_aids',
                                  help='Include assembly aids (corner marks) in PDF')
        pdf_features.add_argument('--no-pdf-assembly-aids', action='store_false', dest='pdf_assembly_aids',
                                  help='Exclude assembly aids from PDF')
        pdf_features.add_argument('--pdf-grid-overlay', action='store_true', dest='pdf_grid_overlay',
                                  help='Add grid overlay to PDF pages')
        pdf_features.add_argument('--pdf-instructions', action='store_true', dest='pdf_instructions',
                                  help='Include assembly instructions page in PDF')
        pdf_features.add_argument('--pdf-duplex', action='store_true', dest='pdf_duplex',
                                  default=True,
                                  help='Add position info back-pages for duplex printing (default: on)')
        pdf_features.add_argument('--no-pdf-duplex', action='store_false', dest='pdf_duplex',
                                  help='Disable duplex back-pages')

        # Cleanup options
        cleanup_group = parser.add_argument_group('Cleanup Options')
        cleanup_group.add_argument('--cleanup-parts', action='store_true', dest='cleanup_parts',
                                   default=True,
                                   help='Delete individual image parts after PDF generation (default: yes)')
        cleanup_group.add_argument('--no-cleanup-parts', action='store_false', dest='cleanup_parts',
                                   help='Keep individual image parts after PDF generation')
        cleanup_group.add_argument('--cleanup-resized', action='store_true', dest='cleanup_resized',
                                   default=False,
                                   help='Also delete the resized source image after PDF generation')

        return parser

    def parse_args(self) -> argparse.Namespace:
        """
        Parse command line arguments.

        Returns:
            argparse.Namespace: Parsed arguments
        """
        parser = self.create_parser()
        args = parser.parse_args()
        return args