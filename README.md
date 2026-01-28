
# Poster Maker

A Python tool for splitting images into equal parts for creating multi-page posters.

## Overview

Poster Maker takes an input image and splits it into a configurable number of equally-sized parts optimized for printing on A4 paper. This allows you to create large posters by printing each part on separate sheets and assembling them together.

![Poster Maker Example](https://i.imgur.com/example.png)

## Features

- Split images into parts: **1D strip** (single row or column) or **2D grid** (rows×cols, PosteRazor-style)
- Multiple resize modes (maintain, stretch, crop, pad_white, pad_black)
- Automatically optimize dimensions for A4 printing
- Maintain high image quality throughout the process
- Generate complete PDF with all poster parts for easy printing
- Assembly instructions with orientation-aware layout diagram
- Preserve previous outputs when generating new splits
- Support for various output formats (PNG, JPG, etc.)
- Comprehensive DPI selection guidelines

- **Optimized Memory Usage**: Streaming generator processes large images part-by-part to prevent RAM spikes
- Memory usage estimation and warnings
- Progress tracking for long operations
- Detailed processing summaries with size breakdowns
- Intelligent logging with context-aware filenames

## Project Structure

```
poster_maker/
├── config/
│   └── settings.yaml          # Configuration settings
├── poster_maker/              # Main package
│   ├── __init__.py
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── image_processor.py # Image processing logic
│   │   └── file_manager.py    # File operations
│   ├── utils/                 # Utility modules
│   │   ├── __init__.py
│   │   ├── logger.py          # Logging setup 
│   │   ├── validators.py      # Input validation
│   │   ├── memory_service.py  # Memory estimation
│   │   ├── pdf_service.py     # PDF generation
│   │   └── display_service.py # Display formatting
│   ├── cli/                   # Command line interface
│   │   ├── __init__.py
│   │   └── arg_parser.py      # Command argument parsing
│   └── config/                # Configuration management
│       ├── __init__.py
│       └── config_loader.py   # Load and parse config
├── data/                      # Data directory
│   └── image/
│       ├── input/             # Input images
│       └── output/            # Output directory for poster parts
├── logs/                      # Log files directory
├── main.py                    # Main entry point
├── pyproject.toml             # Python package configuration
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setting up the environment

1. Clone this repository:
   ```bash
   git clone https://github.com/smaxiso/poster_maker.git
   cd poster_maker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

To split an image into 3 parts (default):

```bash
python main.py -f data/image/input/my_image.jpg
```

### Interactive Mode (Guided Experience) 🎯

For a step-by-step guided experience with **smart recommendations**:

```bash
python main.py --interactive
# or
python main.py -i
```

The interactive mode will:

1. 🖼️ **Analyze your image** - Shows dimensions, aspect ratio, and file size
2. 💡 **Recommend optimal settings** - Grid size and DPI based on image properties
3. 🎯 **Guide you through choices** - Clear explanations for each option
4. ✅ **Validate inputs** - Prevents errors at each step
5. 📋 **Show summary** - Review everything before processing

**Example session:**

```
╭─────────────────────────────────────────────────╮
│        🖼️  Poster Maker - Interactive Mode       │
╰─────────────────────────────────────────────────╯

? Enter image path: /path/to/photo.jpg
  ✓ Image loaded: photo.jpg
    📐 Dimensions: 3840×2160px (landscape)
    📦 File size: 2.45 MB | Format: JPEG

? What type of poster would you like to create?
❯ 📊 2D Grid (PosteRazor-style)
  📏 1D Strip

? Select grid size:
  2x2 - Small poster ~42×59cm (4 pages)
❯ 3x3 - Large poster ~63×88cm (9 pages) ⭐ recommended
  3x4 - Wide panorama ~63×118cm (12 pages)
  ✏️  Custom grid size...

? Select print quality (DPI):
❯ 200 DPI - Good quality ⭐ recommended
  300 DPI - High quality
  ...
```

**Perfect for:**
- First-time users who are unsure about settings
- When you want intelligent recommendations
- Quick poster creation without memorizing CLI flags

**Cleanup options:** In interactive mode, you can choose to delete individual image parts after PDF generation (default: yes), keeping only the final PDF. This is ideal when you only need the PDF for printing.

### Advanced Options

```bash
python main.py -f data/image/input/my_image.jpg -n 4 --dpi 600 --format png --resize-mode pad_black -d -v
```

This will:
- Split `my_image.jpg` into 4 parts (`-n 4`)
- Use 600 DPI for high-quality printing (`--dpi 600`)
- Save output as PNG files (`--format png`)
- Use black padding resize mode (`--resize-mode pad_black`)
- Preserve previous outputs in an archive folder (`-d`)
- Show detailed logging and progress bars (`-v`)

### PDF Generation

Generate a complete PDF with all parts for easy printing:

```bash
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf
```

Options for PDF generation:

```bash
# Include assembly instructions page
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf --pdf-instructions

# Add grid overlay for better alignment
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf --pdf-grid-overlay

# Control compression for smaller file size
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf --pdf-quality 75

# Open PDF after generation
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf --preview-pdf
```

> **WSL Users:** To automatically open PDFs in Windows from WSL, install `wslu`:
> `sudo apt install wslu`
> This enables `wslview` which Poster Maker will use to launch your default Windows PDF viewer.

### Command Line Options

#### Basic Options

| Option | Description |
|--------|-------------|
| `-f`, `--file` | Path to input image file (required) |
| `-n`, `--parts` | Number of parts for 1D strip (default: 3). Ignored if `--grid` is set. |
| `-g`, `--grid` | 2D grid layout, e.g. `2x2`, `3x3`, `2x3`, `4x4`. Overrides `--parts`. Each cell = 1 A4 page. |
| `-d`, `--duplicate` | Preserve previous output in an archive folder |
| `-r`, `--dpi` | DPI for output images (default: 300) |
| `-o`, `--output-dir` | Custom output directory |
| `--format` | Output format (png, jpg, etc.) |
| `--resize-mode` | How to handle aspect ratio (maintain, stretch, crop, pad_white, pad_black) |
| `--summary-level` | Level of detail in summary output (minimal, basic, detailed) |
| `--save-summary` | Save processing summary as JSON file |
| `--dpi-guide` | Display DPI selection guidelines and exit |
| `-v`, `--verbose` | Enable verbose logging and progress bars |

#### PDF Options

| Option | Description |
|--------|-------------|
| `--generate-pdf` | Generate a PDF with all poster parts for easy printing |
| `--pdf-filename` | Specify a custom filename for the PDF |
| `--preview-pdf` | Open the generated PDF after creation |
| `--pdf-instructions` | Include assembly instructions page in the PDF |
| `--pdf-grid-overlay` | Add a grid overlay to PDF pages for alignment |
| `--pdf-compress` / `--no-pdf-compress` | Enable/disable image compression in PDF |
| `--pdf-quality` | JPEG quality for PDF compression (1-100, default: 90) |
| `--pdf-downsample` | Downsample high-resolution images in PDF |
| `--pdf-dpi` | Target DPI for downsampling (default: 300) |
| `--pdf-page-numbers` / `--no-pdf-page-numbers` | Enable/disable page numbers in PDF |
| `--pdf-assembly-aids` / `--no-pdf-assembly-aids` | Enable/disable corner marks in PDF |

#### Cleanup Options

| Option | Description |
|--------|-------------|
| `--cleanup-parts` / `--no-cleanup-parts` | Delete individual image parts after PDF generation (default: yes). Use `--no-cleanup-parts` to keep them. |
| `--cleanup-resized` | Also delete the resized source image after PDF generation (default: no) |

**Note:** Cleanup only happens when PDF is successfully generated. If you only need the PDF for printing, the default `--cleanup-parts` saves disk space by removing the 24 individual image files while keeping only the PDF.

### Resize Modes

The tool offers several resize modes for different needs:

- **maintain** (default): Maintains aspect ratio, may result in letterboxing when printed
- **stretch**: Stretches or shrinks to exactly fit A4 dimensions (may distort image)
- **crop**: Crops image edges to maintain aspect ratio and fill the entire print area
- **pad_white**: Adds white padding to maintain aspect ratio without distortion
- **pad_black**: Adds black padding for a gallery-style presentation

### DPI Guidelines

Use the `--dpi-guide` flag to see recommendations, or choose from these common settings:

- **72-150 DPI**: Screen display, draft prints, very large posters viewed from a distance
- **150-300 DPI**: Standard printing, typical posters (recommended)
- **300-600 DPI**: High-quality prints, professional photography
- **600-1200 DPI**: Premium art reproduction, fine art (large file sizes)

### Output Directory Structure

After running the script, the output will be organized as follows:

```
data/image/output/
└── my_image_poster/          # Directory named after your image
    ├── original/             # Contains a copy of the original image
    │   └── my_image.jpg
    └── posters_3/            # Contains the split parts, with "3" being the number of parts
        ├── my_image_resized.png  # Full resized image
        ├── my_image_part1.png    # First part (deleted if --cleanup-parts)
        ├── my_image_part2.png    # Second part (deleted if --cleanup-parts)
        ├── my_image_part3.png    # Third part (deleted if --cleanup-parts)
        └── my_image_complete.pdf # PDF with all parts (if generated)
```

**Note:** With `--cleanup-parts` (default when generating PDF), only the PDF and resized image remain. Use `--no-cleanup-parts` to keep individual parts.

If you run the script again with the `-d` flag, previous outputs will be preserved:

```
data/image/output/
└── my_image_poster/
    ├── old_posters_3_20230615_120000/  # Archive of previous run
    │   └── posters/
    │       ├── my_image_part1.png
    │       ├── my_image_part2.png
    │       └── my_image_part3.png
    ├── original/
    │   └── my_image.jpg
    └── posters_3/                      # New output
        ├── my_image_resized.png
        ├── my_image_part1.png
        ├── my_image_part2.png
        ├── my_image_part3.png
        └── my_image_complete.pdf
```

## 2D Grid (PosteRazor-style)

Use `--grid RxC` to split the image into a **rows×columns** grid. Each cell is one A4 page; parts are numbered in reading order (top row left→right, then next row).

**Example: 3×3 grid (9 A4 pages)**

```
┌────┬────┬────┐
│ 1  │ 2  │ 3  │   Each box = 1 A4 page
├────┼────┼────┤   Final size: ~63cm × 88cm
│ 4  │ 5  │ 6  │
├────┼────┼────┤
│ 7  │ 8  │ 9  │
└────┴────┴────┘
```

**Popular grid sizes:**

| Grid | A4 Pages | Approx. final size | Best for        |
|------|----------|--------------------|-----------------|
| 2×2  | 4        | 42×59 cm           | Medium poster   |
| 2×3  | 6        | 42×88 cm           | Vertical poster |
| 3×3  | 9        | 63×88 cm           | Large poster    |
| 3×4  | 12       | 63×118 cm          | Wide panorama   |
| 4×4  | 16       | 84×118 cm          | Wall mural      |

**Examples:**

```bash
# 3×3 grid, 9 pages
python main.py -f poster.jpg --grid 3x3 --dpi 300

# 2×3 vertical poster with PDF and assembly instructions
python main.py -f poster.jpg --grid 2x3 --generate-pdf --pdf-instructions

# 4×4 wall mural
python main.py -f mural.jpg --grid 4x4 --dpi 300 --resize-mode crop
```

Output for a grid is saved under `posters_3x3/` (or `posters_2x2/`, etc.) so it stays separate from 1D runs.

## Advanced Use Cases

### Creating a 2x2 Grid Poster

To create a poster on 4 A4 sheets in a 2×2 grid (use `--grid` for true 2D layout):

```bash
python main.py -f data/image/input/poster_image.jpg --grid 2x2 --dpi 300
```

### High-Quality Art Print with Black Border

For a 3-part art print with gallery-style black borders:

```bash
python main.py -f data/image/input/artwork.jpg -n 3 --dpi 600 --format png --resize-mode pad_black
```

### Making a Banner with Memory Check

To create a horizontal banner split into 5 parts with memory usage estimation:

```bash
python main.py -f data/image/input/banner.jpg -n 5 --dpi 300
```

### Creating a Detailed Summary Report

For a complete analysis of the processing:

```bash
python main.py -f data/image/input/my_image.jpg --summary-level detailed --save-summary
```

### Creating a Print-Ready PDF with Assembly Instructions

Generate a complete PDF with instructions for assembly:

```bash
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf --pdf-instructions --preview-pdf
```

### Optimizing PDF File Size

Create a more compressed PDF for easier sharing:

```bash
python main.py -f data/image/input/my_image.jpg -n 3 --generate-pdf --pdf-quality 75 --pdf-downsample --pdf-dpi 150
```

## Configuration

You can customize the default settings by editing the `config/settings.yaml` file:

```yaml
paths:
  base_output_dir: "data/image/output"
  input_dir: "data/image/input"

image:
  default_dpi: 300
  default_parts: 3
  default_format: ""
  resampling_method: "LANCZOS"
  resize_mode: "maintain"
  pad_white: [255, 255, 255]  # White padding for pad mode (RGB)
  pad_black: [0, 0, 0]        # Black padding for pad mode (RGB)
  a4:
    width_inches: 8.27
    height_inches: 11.69
    width_mm: 210
    height_mm: 297

pdf:
  features:
    page_numbers: true       # Add page numbers
    assembly_aids: true      # Add corner marks and orientation indicators
    part_dimensions: true    # Show part dimensions on page
    grid_overlay: false      # Add a grid overlay on each part
    bleed_marks: false       # Add bleed marks for printing
    assembly_instructions: false  # Include assembly instructions
  styling:
    font_name: "Helvetica"
    title_size: 12
    subtitle_size: 8
    margin_mm: 5
    corner_marks_mm: 10
  content:
    top_text: "↑ TOP ↑"
    add_timestamp: true
    add_source_filename: true
  file:
    prefix: ""
    suffix: "_complete"
  optimization:
    compress_images: true
    compression_quality: 90
    downsample_images: false
    downsample_resolution_dpi: 300
    use_jpeg_compression: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d -- %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  file_enabled: true
  file: "poster_maker_{{timestamp}}.log"
  log_folder: "logs"
```

## Output Size Breakdown

When processing is complete, the tool provides a detailed breakdown of output sizes:

```
================================================================================
PROCESSING COMPLETE
================================================================================
Source image: 3840x2160 pixels (1.06 MB)
Output: 3 poster parts at 100 DPI

Output Size Breakdown:
  • Resized image: 4.63 MB
  • Image parts: 4.60 MB (across 3 files)
  • PDF document: 10.32 MB (3 pages)
  • Total output: 19.54 MB

Processing time: 3.23 seconds

SUMMARY:
Image Parts:
  Part 1: 827x1395 pixels (1.46 MB)
  Part 2: 827x1395 pixels (1.61 MB)
  Part 3: 827x1395 pixels (1.52 MB)

PDF Output:
  File: sample_image_2_complete.pdf
  Size: 10.32 MB
  Pages: 3
```

## Requirements

Main dependencies:

- Pillow: Image processing library
- PyYAML: Configuration file parsing
- tqdm: Progress bar visualization
- psutil: System memory monitoring
- reportlab: PDF generation
- rich: Beautiful terminal formatting

See [requirements.txt](requirements.txt) for the complete list.

## Planned Features

- **Graphical User Interface**: Visual interface for easier interaction
- **Multi-page Formats**: Support for booklet printing formats

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The PIL/Pillow development team for the excellent image processing library
- ReportLab team for PDF generation capabilities
- All contributors and users of this tool

---