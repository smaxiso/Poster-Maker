
# poster_maker/utils/pdf_service.py
"""
Service for generating PDF outputs from poster parts.
"""
import logging
import os
import tempfile
import time
import webbrowser
from datetime import datetime
from typing import Any, Dict, List

from PIL import Image
from reportlab.lib.colors import black, gray, white, Color
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from tqdm import tqdm


class PDFService:
    """Service for generating PDF documents from poster parts."""

    def __init__(self, logger: logging.Logger, config: Dict[str, Any]):
        """
        Initialize the PDF service.

        Args:
            logger: Logger instance
            config: Configuration dictionary
        """
        self.logger = logger
        self.config = config
        self.pdf_config = config.get("pdf", {})

        # Set default A4 dimensions
        self.page_width_mm = self.config.get("image", {}).get("a4", {}).get("width_mm", 210)
        self.page_height_mm = self.config.get("image", {}).get("a4", {}).get("height_mm", 297)

        # Convert to points (the unit used by reportlab)
        self.page_width_pt = self.page_width_mm * mm
        self.page_height_pt = self.page_height_mm * mm
        self.page_size = (self.page_width_pt, self.page_height_pt)

    def generate_pdf_from_parts(
        self,
        parts_info: List[Dict[str, Any]],
        output_path: str = None,
        preview: bool = False,
        verbose: bool = False,
        grid_rows: int = None,
        grid_cols: int = None,
    ) -> Dict[str, Any]:
        """
        Generate a PDF document with each poster part on a separate page.

        Args:
            parts_info: List of dictionaries with part information (from summary)
            output_path: Path to save the PDF file (if None, uses a default location)
            preview: Whether to open the PDF after generation
            verbose: Whether to show detailed progress
            grid_rows: For 2D grid layout, number of rows (optional)
            grid_cols: For 2D grid layout, number of columns (optional)

        Returns:
            Dict[str, Any]: Information about the generated PDF
        """
        start_time = time.time()

        # If output path is not specified, create one based on the first part path
        if output_path is None:
            first_part = parts_info[0]
            part_dir = os.path.dirname(first_part["path"])
            filename = os.path.basename(first_part["path"]).split("_part")[0]

            # Get prefix and suffix from config
            prefix = self.pdf_config.get("file", {}).get("prefix", "")
            suffix = self.pdf_config.get("file", {}).get("suffix", "_complete")

            output_path = os.path.join(part_dir, f"{prefix}{filename}{suffix}.pdf")

        # Set up the PDF information dictionary
        pdf_info = {
            "path": output_path,
            "filename": os.path.basename(output_path),
            "directory": os.path.dirname(output_path),
            "pages": len(parts_info),
            "creation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "page_size": "A4",
            "dimensions_mm": f"{self.page_width_mm}mm x {self.page_height_mm}mm",
            "parts_included": [],
            "features": self._get_enabled_features()
        }

        # Check if we should include assembly instructions
        include_instructions = self.pdf_config.get("features", {}).get("assembly_instructions", False)
        include_duplex = self.pdf_config.get("features", {}).get("duplex_back_pages", False)
        
        if include_instructions:
            pdf_info["pages"] += 1  # Add one for instructions page
            if include_duplex:
                pdf_info["pages"] += 1  # Add blank back page for instructions
        
        if include_duplex:
            pdf_info["pages"] += len(parts_info)  # Add back pages for each part

        # Get compression settings
        optimization = self.pdf_config.get("optimization", {})
        compress_images = optimization.get("compress_images", True)
        compression_quality = optimization.get("compression_quality", 90)
        downsample_images = optimization.get("downsample_images", False)
        downsample_resolution = optimization.get("downsample_resolution_dpi", 300)
        use_jpeg = optimization.get("use_jpeg_compression", True)

        # Set up the PDF
        self.logger.info(f"Generating PDF from {len(parts_info)} parts{' with compression' if compress_images else ''}")
        c = canvas.Canvas(output_path, pagesize=self.page_size)

        # Add metadata to the PDF
        c.setTitle(f"Poster Parts - {pdf_info['filename']}")
        c.setAuthor("Poster Maker Tool")
        c.setSubject("Multi-part poster for printing")
        c.setKeywords("poster,print,multi-page")

        # Add assembly instructions if configured
        if include_instructions:
            self._add_assembly_instructions_page(
                c, parts_info, grid_rows=grid_rows, grid_cols=grid_cols
            )
            # After adding the page, move to the next one
            c.showPage()
            
            # If duplex mode, add a blank page after instructions
            # so first poster piece doesn't print on back of instructions
            if include_duplex:
                self._add_blank_page(c, "This page intentionally left blank for duplex printing")
                c.showPage()

        # Process each part with progress bar
        total_parts = len(parts_info)

        with tqdm(total=total_parts, desc="Generating PDF", unit="page", disable=not verbose) as pbar:
            for i, part in enumerate(parts_info, 1):
                self.logger.info(f"Adding part {i}/{total_parts} to PDF")
                pbar.set_description(f"Adding part {i}/{total_parts}")

                # Get the part image
                img_path = part["path"]
                temp_path = None

                try:
                    # If compression is enabled, create an optimized version
                    if compress_images:
                        # Create a temporary file for the compressed image
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                            temp_path = temp_file.name

                        # Open and optimize the image
                        img = Image.open(img_path)

                        # Downsample if required
                        if downsample_images and 'dpi' in part:
                            current_dpi = part.get('dpi', 600)  # Default to 600 if not specified
                            if current_dpi > downsample_resolution:
                                scale_factor = downsample_resolution / current_dpi
                                new_width = int(img.width * scale_factor)
                                new_height = int(img.height * scale_factor)
                                img = img.resize((new_width, new_height), Image.LANCZOS)

                        # Save with compression
                        format_to_use = 'JPEG' if use_jpeg else 'PNG'
                        if format_to_use == 'JPEG':
                            # Convert to RGB if needed (JPEG doesn't support alpha)
                            if img.mode == 'RGBA':
                                img = img.convert('RGB')
                            img.save(temp_path, format=format_to_use, quality=compression_quality, optimize=True)
                        else:
                            # For PNG, use optimize=True
                            img.save(temp_path, format=format_to_use, optimize=True)

                        # Use the temporary file for the PDF
                        img_to_use = temp_path
                        img_width, img_height = img.size
                    else:
                        # Use the original image
                        img = Image.open(img_path)
                        img_width, img_height = img.size
                        img_to_use = img_path

                    # Calculate scaling to fit A4 with margins
                    margin_mm = self.pdf_config.get("styling", {}).get("margin_mm", 5)
                    available_width = self.page_width_pt - (2 * margin_mm * mm)
                    available_height = self.page_height_pt - (2 * margin_mm * mm)

                    width_ratio = available_width / img_width
                    height_ratio = available_height / img_height
                    scale = min(width_ratio, height_ratio)

                    # Calculate position to center the image
                    x = (self.page_width_pt - (img_width * scale)) / 2
                    y = (self.page_height_pt - (img_height * scale)) / 2

                    # Calculate actual dimensions on page
                    actual_width = img_width * scale
                    actual_height = img_height * scale

                    # Draw the image
                    c.drawImage(
                        img_to_use,
                        x, y,
                        width=actual_width,
                        height=actual_height
                    )

                finally:
                    # Always clean up temp file, even if an exception occurred
                    if temp_path is not None:
                        try:
                            os.unlink(temp_path)
                        except OSError as e:
                            self.logger.warning(f"Failed to remove temporary file {temp_path}: {e}")

                # Add configured elements
                self._add_page_content(c, i, total_parts, img_width, img_height, part)

                # Store information about this page in our PDF info
                pdf_info["parts_included"].append({
                    "page": i + (1 if include_instructions else 0),  # Adjust for assembly instructions
                    "original_path": img_path,
                    "original_dimensions": f"{img_width}x{img_height}",
                    "scale_factor": f"{scale:.3f}",
                    "printed_dimensions_mm": f"{(actual_width / mm):.1f}mm x {(actual_height / mm):.1f}mm",
                    "position_on_page": f"({x / mm:.1f}mm, {y / mm:.1f}mm)"
                })

                # Add duplex back page with position info if enabled
                if include_duplex:
                    c.showPage()
                    self._add_duplex_back_page(
                        c, i, total_parts, grid_rows or 1, grid_cols or total_parts
                    )

                # Add a new page for the next part (except for the last page)
                if i < total_parts:
                    c.showPage()

                # Update progress bar
                pbar.update(1)

        # Save the PDF
        c.save()

        # Calculate file size
        pdf_size_bytes = os.path.getsize(output_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Add file info to the PDF information
        pdf_info["size_bytes"] = pdf_size_bytes
        pdf_info["size_mb"] = pdf_size_bytes / (1024 * 1024)
        pdf_info["processing_time_seconds"] = processing_time

        # Add optimization info
        pdf_info["optimization"] = {
            "compress_images": compress_images,
            "compression_quality": compression_quality if compress_images else None,
            "downsample_images": downsample_images,
            "downsample_resolution_dpi": downsample_resolution if downsample_images else None,
            "use_jpeg_compression": use_jpeg
        }

        # Add config info
        pdf_info["config"] = {
            "features": self._get_enabled_features()
        }

        # Log result
        self.logger.info(f"PDF generated successfully: {output_path} ({pdf_info['size_mb']:.2f} MB)")

        # Open the PDF if requested
        if preview:
            self._open_pdf(output_path)

        return pdf_info

    def _get_enabled_features(self) -> List[str]:
        """Get a list of enabled PDF features from config."""
        features = []
        features_config = self.pdf_config.get("features", {})

        if features_config.get("page_numbers", True):
            features.append("Page numbers")

        if features_config.get("assembly_aids", True):
            features.append("Assembly aids")

        if features_config.get("part_dimensions", True):
            features.append("Part dimensions")

        if features_config.get("grid_overlay", False):
            features.append("Grid overlay")

        if features_config.get("bleed_marks", False):
            features.append("Bleed marks")

        if features_config.get("assembly_instructions", False):
            features.append("Assembly instructions")

        if features_config.get("duplex_back_pages", False):
            features.append("Duplex back pages")

        return features

    def _add_page_content(self, canvas_obj, part_num: int, total_parts: int,
                          img_width: int, img_height: int, part_info: Dict[str, Any]) -> None:
        """
        Add content to the PDF page based on configuration.

        Args:
            canvas_obj: ReportLab canvas object
            part_num: Current part number
            total_parts: Total number of parts
            img_width: Width of the current part
            img_height: Height of the current part
            part_info: Information about the current part
        """
        features = self.pdf_config.get("features", {})
        styling = self.pdf_config.get("styling", {})
        content = self.pdf_config.get("content", {})

        # Get styling parameters
        font_name = styling.get("font_name", "Helvetica")
        title_size = styling.get("title_size", 12)
        subtitle_size = styling.get("subtitle_size", 8)
        margin_mm = styling.get("margin_mm", 5)
        corner_marks_mm = styling.get("corner_marks_mm", 10)

        # Add page numbers if enabled
        if features.get("page_numbers", True):
            canvas_obj.setFont(f"{font_name}-Bold", title_size)

            # Draw centered page number at bottom
            text = f"Page {part_num} of {total_parts}"
            text_width = canvas_obj.stringWidth(text, f"{font_name}-Bold", title_size)
            canvas_obj.drawString((self.page_width_pt - text_width) / 2, 10 * mm, text)

        # Add part dimensions if enabled
        if features.get("part_dimensions", True):
            canvas_obj.setFont(font_name, subtitle_size)
            canvas_obj.drawString(margin_mm * mm, margin_mm * mm,
                                  f"Part {part_num}/{total_parts} - Size: {img_width}x{img_height}")

        # Add top orientation text if enabled
        top_text = content.get("top_text", "↑ TOP ↑")
        if top_text:
            canvas_obj.setFont(font_name, subtitle_size)
            canvas_obj.drawString(self.page_width_pt - 30 * mm, self.page_height_pt - 10 * mm, top_text)

        # Add timestamp if enabled
        if content.get("add_timestamp", True):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            canvas_obj.setFont(font_name, subtitle_size)
            canvas_obj.drawString(self.page_width_pt - 45 * mm, 5 * mm, f"Created: {timestamp}")

        # Add source filename if enabled
        if content.get("add_source_filename", True):
            source_file = os.path.basename(part_info.get("path", ""))
            if source_file:
                canvas_obj.setFont(font_name, subtitle_size)
                text = f"Source: {source_file}"
                # Limit text length to avoid overflow
                if canvas_obj.stringWidth(text, font_name, subtitle_size) > 60 * mm:
                    text = f"Source: ...{source_file[-25:]}"
                canvas_obj.drawString(margin_mm * mm, 5 * mm, text)

        # Add assembly aids if enabled
        if features.get("assembly_aids", True):
            self._add_assembly_aids(canvas_obj, part_num, total_parts, corner_marks_mm)

        # Add grid overlay if enabled
        if features.get("grid_overlay", False):
            self._add_grid_overlay(canvas_obj)

        # Add bleed marks if enabled
        if features.get("bleed_marks", False):
            self._add_bleed_marks(canvas_obj)

    def _add_assembly_instructions_page(
        self,
        canvas_obj,
        parts_info: List[Dict[str, Any]],
        grid_rows: int = None,
        grid_cols: int = None,
    ) -> None:
        """
        Add a page with assembly instructions for the poster.

        Args:
            canvas_obj: ReportLab canvas object
            parts_info: Information about all parts
            grid_rows: For 2D grid, number of rows (optional)
            grid_cols: For 2D grid, number of columns (optional)
        """
        # Get styling parameters
        styling = self.pdf_config.get("styling", {})
        font_name = styling.get("font_name", "Helvetica")

        # Draw title
        canvas_obj.setFont(f"{font_name}-Bold", 24)
        title = "Poster Assembly Instructions"
        title_width = canvas_obj.stringWidth(title, f"{font_name}-Bold", 24)
        canvas_obj.drawString((self.page_width_pt - title_width) / 2, self.page_height_pt - 40, title)

        # Draw horizontal line
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40, self.page_height_pt - 50, self.page_width_pt - 40, self.page_height_pt - 50)

        # Add information
        canvas_obj.setFont(font_name, 12)
        y_position = self.page_height_pt - 80
        line_height = 20

        # Add poster information
        canvas_obj.drawString(40, y_position, f"Total Parts: {len(parts_info)}")
        y_position -= line_height

        # Use provided grid dimensions or infer from crop boxes (1D strip)
        if grid_rows is not None and grid_cols is not None:
            split_direction = "grid"
        elif len(parts_info) > 1 and "crop_box" in parts_info[0]:
            first_box = parts_info[0]["crop_box"]
            second_box = parts_info[1]["crop_box"]
            if first_box[2] == second_box[0]:
                split_direction = "horizontal"
                grid_cols = len(parts_info)
                grid_rows = 1
            elif first_box[3] == second_box[1]:
                split_direction = "vertical"
                grid_cols = 1
                grid_rows = len(parts_info)
            else:
                split_direction = self._determine_split_direction_from_dimensions(parts_info)
                grid_cols = len(parts_info) if split_direction == "horizontal" else 1
                grid_rows = 1 if split_direction == "horizontal" else len(parts_info)
        else:
            split_direction = self._determine_split_direction_from_dimensions(parts_info)
            grid_cols = len(parts_info) if split_direction == "horizontal" else 1
            grid_rows = 1 if split_direction == "horizontal" else len(parts_info)

        arrangement_text = f"Arrangement: {grid_rows} row(s) × {grid_cols} column(s)"
        if split_direction != "grid":
            arrangement_text += f" (Split: {split_direction})"
        canvas_obj.drawString(40, y_position, arrangement_text)
        y_position -= line_height * 2

        # Add assembly steps
        canvas_obj.setFont(f"{font_name}-Bold", 14)
        canvas_obj.drawString(40, y_position, "Assembly Steps:")
        y_position -= line_height * 1.5

        canvas_obj.setFont(font_name, 12)

        if split_direction == "grid":
            arrangement_step = "4. Arrange in a grid: top row left to right, then each row below."
        elif split_direction == "horizontal":
            arrangement_step = "4. Align the parts horizontally from left to right."
        else:
            arrangement_step = "4. Align the parts vertically from top to bottom."

        steps = [
            "1. Print all pages at 100% scale (no scaling/resizing).",
            "2. Cut along the edges of each part if needed.",
            "3. Arrange the parts in order according to the page numbers.",
            arrangement_step,
            "5. Use the corner marks and TOP indicators to ensure proper alignment.",
            "6. Tape or glue the parts together from the back side.",
            "7. For best results, use a straight edge when joining parts."
        ]

        for step in steps:
            canvas_obj.drawString(40, y_position, step)
            y_position -= line_height

        y_position -= line_height

        # Add diagram of the layout (simplified)
        canvas_obj.setFont(f"{font_name}-Bold", 14)
        canvas_obj.drawString(40, y_position, "Layout Diagram:")
        y_position -= line_height * 1.5

        # Calculate the size of the diagram
        diagram_width = 300
        diagram_height = 200

        # Adjust the aspect ratio to match the real layout
        if grid_rows > grid_cols:
            # Vertical layout - make diagram taller
            diagram_height = min(300, diagram_width * grid_rows / grid_cols)
        else:
            # Horizontal layout - make diagram wider
            diagram_width = min(400, diagram_height * grid_cols / grid_rows)

        cell_width = diagram_width / max(grid_cols, 1)
        cell_height = diagram_height / max(grid_rows, 1)

        # Draw the grid
        canvas_obj.setLineWidth(2)
        start_x = (self.page_width_pt - diagram_width) / 2
        start_y = y_position - diagram_height

        for i in range(grid_rows + 1):
            y = start_y + i * cell_height
            canvas_obj.line(start_x, y, start_x + diagram_width, y)

        for i in range(grid_cols + 1):
            x = start_x + i * cell_width
            canvas_obj.line(x, start_y, x, start_y + diagram_height)

        # Add part numbers to the grid (row-major: 1..cols, then next row)
        canvas_obj.setFont(f"{font_name}", 16)

        for i in range(len(parts_info)):
            part_num = i + 1
            if split_direction == "grid" and grid_cols and grid_rows:
                row = i // grid_cols
                col = i % grid_cols
            elif split_direction == "vertical":
                row = i
                col = 0
            else:
                row = 0
                col = i

            x = start_x + col * cell_width + cell_width / 2
            y = start_y + (grid_rows - row - 1) * cell_height + cell_height / 2

            text = str(part_num)
            text_width = canvas_obj.stringWidth(text, font_name, 16)
            canvas_obj.drawString(x - text_width / 2, y, text)

        y_position = start_y - 30

        # Add footer
        canvas_obj.setFont(font_name, 10)
        footer = "Created with Poster Maker Tool"
        footer_width = canvas_obj.stringWidth(footer, font_name, 10)
        canvas_obj.drawString((self.page_width_pt - footer_width) / 2, 20, footer)

    @staticmethod
    def _determine_split_direction_from_dimensions(parts_info: List[Dict[str, Any]]) -> str:
        """
        Determine the split direction based on part dimensions.

        Args:
            parts_info: List of part information dictionaries

        Returns:
            str: 'horizontal' or 'vertical'
        """
        # Extract dimensions from first part
        if "dimensions" in parts_info[0]:
            first_width = parts_info[0]["dimensions"].get("width", 0)
            first_height = parts_info[0]["dimensions"].get("height", 0)

            # Compare width vs height ratio
            if len(parts_info) > 1:
                # Multiple parts with same aspect ratio suggests a direction
                aspect_ratio = first_width / first_height if first_height else 1

                if aspect_ratio > 1:
                    # Landscape parts usually come from horizontal splits
                    return "horizontal"
                else:
                    # Portrait parts usually come from vertical splits
                    return "vertical"

        # Default to horizontal if we can't determine or need a fallback
        return "horizontal"

    def _add_assembly_aids(self, canvas_obj, part_num: int, total_parts: int, corner_marks_mm: float) -> None:
        """
        Add assembly aids like corner marks to the PDF.

        Args:
            canvas_obj: ReportLab canvas object
            part_num: Current part number
            total_parts: Total number of parts
            corner_marks_mm: Length of corner marks in mm
        """
        # Get margin from styling config
        margin_mm = self.pdf_config.get("styling", {}).get("margin_mm", 5)

        # Draw subtle corner marks for alignment
        canvas_obj.setLineWidth(0.2)
        corner_length = corner_marks_mm * mm  # Convert to points
        margin = margin_mm * mm  # Convert to points

        # Top-left corner
        canvas_obj.line(margin, self.page_height_pt - margin, margin + corner_length, self.page_height_pt - margin)
        canvas_obj.line(margin, self.page_height_pt - margin, margin, self.page_height_pt - margin - corner_length)

        # Top-right corner
        canvas_obj.line(self.page_width_pt - margin, self.page_height_pt - margin,
                        self.page_width_pt - margin - corner_length, self.page_height_pt - margin)
        canvas_obj.line(self.page_width_pt - margin, self.page_height_pt - margin,
                        self.page_width_pt - margin, self.page_height_pt - margin - corner_length)

        # Bottom-left corner
        canvas_obj.line(margin, margin, margin + corner_length, margin)
        canvas_obj.line(margin, margin, margin, margin + corner_length)

        # Bottom-right corner
        canvas_obj.line(self.page_width_pt - margin, margin, self.page_width_pt - margin - corner_length, margin)
        canvas_obj.line(self.page_width_pt - margin, margin, self.page_width_pt - margin, margin + corner_length)

    def _add_grid_overlay(self, canvas_obj) -> None:
        """
        Add a grid overlay to help with alignment.

        Args:
            canvas_obj: ReportLab canvas object
        """
        # Save current state
        canvas_obj.saveState()

        # Set up grid style
        canvas_obj.setStrokeColor(gray)
        canvas_obj.setLineWidth(0.1)

        # Draw vertical lines every 20mm
        for x in range(0, int(self.page_width_mm), 20):
            canvas_obj.line(x * mm, 0, x * mm, self.page_height_pt)

        # Draw horizontal lines every 20mm
        for y in range(0, int(self.page_height_mm), 20):
            canvas_obj.line(0, y * mm, self.page_width_pt, y * mm)

        # Restore state
        canvas_obj.restoreState()

    def _add_bleed_marks(self, canvas_obj) -> None:
        """
        Add bleed marks for professional printing.

        Args:
            canvas_obj: ReportLab canvas object
        """
        # Save current state
        canvas_obj.saveState()

        # Set up bleed mark style
        canvas_obj.setStrokeColor(black)
        canvas_obj.setLineWidth(0.5)

        # Standard bleed is 3mm
        bleed = 3 * mm

        # Draw bleed marks at corners
        # Top-left
        canvas_obj.line(bleed, self.page_height_pt, bleed, self.page_height_pt - 5 * mm)
        canvas_obj.line(0, self.page_height_pt - bleed, 5 * mm, self.page_height_pt - bleed)

        # Top-right
        canvas_obj.line(self.page_width_pt - bleed, self.page_height_pt,
                        self.page_width_pt - bleed, self.page_height_pt - 5 * mm)
        canvas_obj.line(self.page_width_pt, self.page_height_pt - bleed,
                        self.page_width_pt - 5 * mm, self.page_height_pt - bleed)

        # Bottom-left
        canvas_obj.line(bleed, 0, bleed, 5 * mm)
        canvas_obj.line(0, bleed, 5 * mm, bleed)

        # Bottom-right
        canvas_obj.line(self.page_width_pt - bleed, 0, self.page_width_pt - bleed, 5 * mm)
        canvas_obj.line(self.page_width_pt, bleed, self.page_width_pt - 5 * mm, bleed)

        # Restore state
        canvas_obj.restoreState()

    def _add_blank_page(self, canvas_obj, message: str = "") -> None:
        """
        Add a blank page with optional centered message.

        Args:
            canvas_obj: ReportLab canvas object
            message: Optional message to display
        """
        if message:
            styling = self.pdf_config.get("styling", {})
            font_name = styling.get("font_name", "Helvetica")
            
            canvas_obj.setFont(font_name, 10)
            canvas_obj.setFillColor(gray)
            text_width = canvas_obj.stringWidth(message, font_name, 10)
            canvas_obj.drawString(
                (self.page_width_pt - text_width) / 2,
                self.page_height_pt / 2,
                message
            )
            canvas_obj.setFillColor(black)

    def _add_duplex_back_page(
        self,
        canvas_obj,
        part_num: int,
        total_parts: int,
        grid_rows: int,
        grid_cols: int,
    ) -> None:
        """
        Add a back page with position information for duplex printing.
        Shows a mini grid with current position highlighted.

        Args:
            canvas_obj: ReportLab canvas object
            part_num: Current part number (1-indexed)
            total_parts: Total number of parts
            grid_rows: Number of rows in the grid
            grid_cols: Number of columns in the grid
        """
        styling = self.pdf_config.get("styling", {})
        font_name = styling.get("font_name", "Helvetica")
        
        # Calculate row and column for this part
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        
        # Title
        canvas_obj.setFont(f"{font_name}-Bold", 24)
        title = f"Page {part_num} of {total_parts}"
        title_width = canvas_obj.stringWidth(title, f"{font_name}-Bold", 24)
        canvas_obj.drawString(
            (self.page_width_pt - title_width) / 2,
            self.page_height_pt - 50,
            title
        )
        
        # Position info
        canvas_obj.setFont(f"{font_name}", 16)
        position_text = f"Row {row + 1}, Column {col + 1}"
        pos_width = canvas_obj.stringWidth(position_text, font_name, 16)
        canvas_obj.drawString(
            (self.page_width_pt - pos_width) / 2,
            self.page_height_pt - 80,
            position_text
        )
        
        # Draw the mini grid diagram
        # Calculate grid dimensions to fit nicely on page
        max_grid_width = 150 * mm
        max_grid_height = 180 * mm
        
        # Adjust aspect ratio
        cell_size = min(max_grid_width / grid_cols, max_grid_height / grid_rows)
        grid_width = cell_size * grid_cols
        grid_height = cell_size * grid_rows
        
        # Center the grid
        start_x = (self.page_width_pt - grid_width) / 2
        start_y = (self.page_height_pt - grid_height) / 2 - 20  # Slightly above center
        
        # Draw grid cells
        for r in range(grid_rows):
            for c in range(grid_cols):
                cell_x = start_x + c * cell_size
                cell_y = start_y + (grid_rows - r - 1) * cell_size  # Flip Y for top-to-bottom
                
                cell_part_num = r * grid_cols + c + 1
                is_current = cell_part_num == part_num
                
                # Draw cell border - thick border for current cell (ink-efficient highlight)
                if is_current:
                    # Draw thick border for current cell (no fill - saves ink!)
                    canvas_obj.setStrokeColor(black)
                    canvas_obj.setLineWidth(4)
                    canvas_obj.rect(cell_x, cell_y, cell_size, cell_size, fill=0, stroke=1)
                    # Draw inner border for double-line effect
                    canvas_obj.setLineWidth(1)
                    inset = 3
                    canvas_obj.rect(
                        cell_x + inset, cell_y + inset,
                        cell_size - 2 * inset, cell_size - 2 * inset,
                        fill=0, stroke=1
                    )
                else:
                    # Normal thin border for other cells
                    canvas_obj.setStrokeColor(gray)
                    canvas_obj.setLineWidth(0.5)
                    canvas_obj.rect(cell_x, cell_y, cell_size, cell_size, fill=0, stroke=1)
                
                # Draw part number in cell
                if cell_part_num <= total_parts:
                    canvas_obj.setFillColor(black)
                    canvas_obj.setFont(
                        f"{font_name}-Bold" if is_current else font_name,
                        16 if is_current else 10
                    )
                    num_text = str(cell_part_num)
                    num_width = canvas_obj.stringWidth(
                        num_text,
                        f"{font_name}-Bold" if is_current else font_name,
                        16 if is_current else 10
                    )
                    canvas_obj.drawString(
                        cell_x + (cell_size - num_width) / 2,
                        cell_y + cell_size / 2 - (6 if is_current else 4),
                        num_text
                    )
        
        # Reset line width
        canvas_obj.setLineWidth(1)
        
        # Add legend/instructions below grid
        y_legend = start_y - 30
        
        # Grid info with dynamic font sizing for large grids
        grid_info = f"Grid: {grid_rows} rows × {grid_cols} columns"
        info_font_size = 11
        max_text_width = self.page_width_pt - 40  # 20mm margins
        info_width = canvas_obj.stringWidth(grid_info, font_name, info_font_size)
        
        # Scale down font if text too wide
        while info_width > max_text_width and info_font_size > 7:
            info_font_size -= 1
            info_width = canvas_obj.stringWidth(grid_info, font_name, info_font_size)
        
        canvas_obj.setFont(font_name, info_font_size)
        canvas_obj.drawString((self.page_width_pt - info_width) / 2, y_legend, grid_info)
        
        # Assembly hint
        y_legend -= 20
        if grid_cols > 1:
            hint = "← Arrange left to right, top to bottom →"
        else:
            hint = "↓ Arrange top to bottom ↓"
        hint_width = canvas_obj.stringWidth(hint, font_name, 11)
        canvas_obj.drawString((self.page_width_pt - hint_width) / 2, y_legend, hint)
        
        # Neighbors info
        y_legend -= 30
        canvas_obj.setFont(font_name, 10)
        neighbors = []
        if row > 0:
            neighbors.append(f"↑ Above: Page {part_num - grid_cols}")
        if row < grid_rows - 1 and part_num + grid_cols <= total_parts:
            neighbors.append(f"↓ Below: Page {part_num + grid_cols}")
        if col > 0:
            neighbors.append(f"← Left: Page {part_num - 1}")
        if col < grid_cols - 1 and part_num + 1 <= total_parts:
            neighbors.append(f"→ Right: Page {part_num + 1}")
        
        if neighbors:
            neighbor_text = "Neighbors: " + " | ".join(neighbors)
            neighbor_width = canvas_obj.stringWidth(neighbor_text, font_name, 10)
            # If text is too wide, split into two lines
            if neighbor_width > self.page_width_pt - 40:
                mid = len(neighbors) // 2
                line1 = "Neighbors: " + " | ".join(neighbors[:mid])
                line2 = " | ".join(neighbors[mid:])
                w1 = canvas_obj.stringWidth(line1, font_name, 10)
                w2 = canvas_obj.stringWidth(line2, font_name, 10)
                canvas_obj.drawString((self.page_width_pt - w1) / 2, y_legend, line1)
                canvas_obj.drawString((self.page_width_pt - w2) / 2, y_legend - 15, line2)
            else:
                canvas_obj.drawString((self.page_width_pt - neighbor_width) / 2, y_legend, neighbor_text)
        
        # "View from Front" clarification (addresses mirroring cognitive load)
        y_legend -= 25
        canvas_obj.setFont(f"{font_name}-Oblique", 9)
        canvas_obj.setFillColor(gray)
        view_note = "📋 Grid shows poster layout as viewed from the FRONT"
        view_width = canvas_obj.stringWidth(view_note, f"{font_name}-Oblique", 9)
        canvas_obj.drawString((self.page_width_pt - view_width) / 2, y_legend, view_note)
        
        # Footer
        canvas_obj.setFont(font_name, 9)
        footer = "This is the back side for duplex printing - Position this page behind the poster piece"
        footer_width = canvas_obj.stringWidth(footer, font_name, 9)
        canvas_obj.drawString((self.page_width_pt - footer_width) / 2, 30, footer)
        canvas_obj.setFillColor(black)

    def _open_pdf(self, pdf_path: str) -> None:
        """
        Open the PDF file in the default viewer.

        Args:
            pdf_path: Path to the PDF file
        """
        import platform
        import subprocess

        try:
            if not os.path.exists(pdf_path):
                self.logger.warning(f"Cannot open PDF: File not found: {pdf_path}")
                return

            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", pdf_path], check=True)
            elif system == "Windows":
                os.startfile(pdf_path)  # type: ignore
            else:  # Linux and others
                subprocess.run(["xdg-open", pdf_path], check=True)

            self.logger.info(f"Opened PDF file: {pdf_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to open PDF: {e}")
        except Exception as e:
            self.logger.error(f"Failed to open PDF: {str(e)}")