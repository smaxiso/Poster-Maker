
# Poster Maker: Feature Status & Roadmap

## Overview

This document tracks implemented features and planned enhancements for Poster Maker.

### ✅ Completed Features

1. **Grid-based Splitting** — Split images into n×m grids (e.g., `--grid 3x3`)
2. **Interactive CLI Mode** — Guided experience with smart recommendations (`-i`)
3. **PDF Generation** — Complete PDF with assembly instructions
4. **Cleanup Options** — Auto-delete image parts after PDF generation
5. **Memory Optimization** — Generator-based processing for low RAM usage

### ⏳ Planned Features

1. **Graphical User Interface** — Visual interface for easier interaction

---

## ✅ COMPLETED: Grid-Based Splitting

**Status:** Fully implemented and tested.

### Usage

```bash
# 3×3 grid (9 A4 pages)
python main.py -f image.jpg --grid 3x3 --generate-pdf

# 2×4 grid for panoramas
python main.py -f panorama.jpg --grid 2x4 --dpi 300
```

### Implementation Details

- CLI argument: `--grid RxC` (e.g., `3x3`, `2x4`)
- Validation: Max 20×20 grid, max 100 total pages
- Output: Parts numbered in reading order (row by row)
- PDF: Assembly instructions with grid diagram

---

## ✅ COMPLETED: Interactive CLI Mode

**Status:** Fully implemented with smart recommendations.

### Usage

```bash
python main.py -i
# or
python main.py --interactive
```

### Features

- 🖼️ Image analysis with dimensions and aspect ratio
- 💡 Smart grid/DPI recommendations based on image properties
- ✅ Input validation at each step
- 📋 Configuration summary before processing
- 🗑️ Cleanup options (delete parts after PDF generation)

### Implementation

- Location: `poster_maker/cli/interactive.py`
- Library: `questionary` for styled prompts
- Config: `InteractiveConfig` dataclass

---

## ✅ COMPLETED: Cleanup Options

**Status:** Implemented with defaults optimized for print workflow.

### Usage

```bash
# Default: delete parts after PDF (only keep PDF)
python main.py -f image.jpg --grid 3x3 --generate-pdf

# Keep parts
python main.py -f image.jpg --grid 3x3 --generate-pdf --no-cleanup-parts

# Also delete resized image
python main.py -f image.jpg --grid 3x3 --generate-pdf --cleanup-resized
```

### Rationale

Most users only need the PDF for printing. Deleting 24 individual image parts saves significant disk space while keeping the complete, printable PDF.

---

## ⏳ PLANNED: Graphical User Interface

### 1. Technology Selection

- **Framework**: PyQt5 (cross-platform, feature-rich)
- **Structure**: Model-View-Controller pattern
- **Dependencies**: PyQt5, Pillow, other existing dependencies

### 2. Main Window Design

![Main Window Design](https://placeholder-for-gui-mockup.com/main_window.png)

#### A. Layout Components

1. **Image Preview Area**
   - Shows the current image with grid overlay
   - Drag & drop support
   - Zoom controls

2. **Split Configuration Panel**
   - Split mode: Horizontal / Vertical / Grid
   - Rows and columns inputs (for grid mode)
   - DPI settings
   - Output format selector

3. **Resize Options**
   - Maintain / Stretch / Crop / Pad White / Pad Black
   - Visual preview of each option

4. **PDF Options**
   - Assembly instructions toggle
   - Page numbers toggle
   - Grid overlay toggle
   - Compression quality slider

5. **Output Settings**
   - Output directory
   - Preview PDF checkbox
   - Named configurations (save/load settings)

### 3. Implementation Plan

#### A. Base Classes

```python
# poster_maker/gui/main_window.py
class PosterMakerWindow(QMainWindow):
    """Main window for the Poster Maker GUI application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poster Maker")
        self.setup_ui()
        
    def setup_ui(self):
        # Create widgets, layouts, and connections
        pass
    
    # ... other methods for handling UI events ...
```

#### B. Key Components

1. **Image Preview Widget**
   ```python
   # poster_maker/gui/widgets/image_preview.py
   class ImagePreviewWidget(QWidget):
       """Widget for displaying and interacting with the image."""
   ```

2. **Split Settings Widget**
   ```python
   # poster_maker/gui/widgets/split_settings.py
   class SplitSettingsWidget(QGroupBox):
       """Widget for configuring image splitting options."""
   ```

3. **PDF Options Widget**
   ```python
   # poster_maker/gui/widgets/pdf_options.py
   class PDFOptionsWidget(QGroupBox):
       """Widget for configuring PDF output options."""
   ```

4. **Processing Thread**
   ```python
   # poster_maker/gui/workers/processor_thread.py
   class ImageProcessorThread(QThread):
       """Background thread for image processing operations."""
   ```

### 4. User Interaction Flow

1. **Loading an Image**
   - User selects an image via file dialog or drag & drop
   - Image is displayed in preview area
   - Default grid overlay is shown based on settings

2. **Adjusting Settings**
   - User adjusts rows/columns or switches between modes
   - Preview updates in real-time to show split lines
   - Resize mode can be changed with visual feedback

3. **Processing**
   - User clicks "Generate" button
   - Progress dialog shows each step
   - On completion, summary is displayed

4. **Output Review**
   - Thumbnails of generated parts are displayed
   - PDF preview is shown if selected
   - Options to open output folder

## GUI Development Roadmap

### Phase 1: Core GUI (5-7 days)
- Days 1-2: Set up main window and basic widgets
- Day 3: Implement image preview with grid overlay
- Day 4: Add settings panels and controls
- Day 5: Create processing workflow and progress indicators
- Days 6-7: Testing, refinements, and bug fixes

### Phase 2: Integration and Polish (2-3 days)
- Day 1: Ensure CLI and GUI share the same core functionality
- Day 2: Add save/load settings functionality
- Day 3: Final testing across different platforms

---

## Technical Considerations

### 1. Memory Management ✅
- ~~Memory usage estimation before processing~~ — **Implemented**
- For GUI: implement preview downsampling for large images

### 2. User Experience ✅
- ~~Add templates for common poster sizes~~ — **Implemented** (grid presets in interactive mode)
- ~~Smart recommendations~~ — **Implemented** (aspect-ratio based suggestions)
- For GUI: tooltips, remember recent settings

### 3. Testing ✅
- ~~Unit tests for grid splitting~~ — **Implemented** (56 tests)
- For GUI: integration tests for GUI-CLI consistency

---

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Grid Splitting | ✅ Complete | `--grid RxC` |
| Interactive CLI | ✅ Complete | `-i` flag |
| PDF Generation | ✅ Complete | Assembly instructions, grid overlay |
| Cleanup Options | ✅ Complete | `--cleanup-parts` (default) |
| Memory Estimation | ✅ Complete | Warns for high RAM usage |
| Unit Tests | ✅ Complete | 56 tests passing |
| GUI | ⏳ Planned | PyQt5-based interface |

The CLI and interactive mode now provide a complete workflow. The GUI remains as the main enhancement opportunity for users who prefer visual interaction.