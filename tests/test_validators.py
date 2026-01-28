
"""Unit tests for validators and parse_grid."""
import os
import tempfile

import pytest

from poster_maker.utils.validators import parse_grid, InputValidator


class TestParseGrid:
    """Tests for parse_grid()."""

    def test_valid_3x3(self):
        assert parse_grid("3x3") == (3, 3)

    def test_valid_2x4(self):
        assert parse_grid("2x4") == (2, 4)

    def test_valid_uppercase(self):
        assert parse_grid("4X4") == (4, 4)

    def test_valid_with_spaces(self):
        assert parse_grid(" 3 x 3 ") == (3, 3)

    def test_unicode_times(self):
        assert parse_grid("2×3") == (2, 3)

    def test_single_digit(self):
        assert parse_grid("1x10") == (1, 10)

    def test_empty_returns_none(self):
        assert parse_grid("") is None
        assert parse_grid("   ") is None

    def test_invalid_format_returns_none(self):
        assert parse_grid("x3") is None
        assert parse_grid("3x") is None
        assert parse_grid("3") is None
        assert parse_grid("3-3") is None
        assert parse_grid("abc") is None

    def test_none_input(self):
        assert parse_grid(None) is None

    def test_zero_dimension_returns_none(self):
        assert parse_grid("0x3") is None
        assert parse_grid("3x0") is None


class TestValidateParts:
    """Tests for InputValidator.validate_parts()."""

    def test_valid(self):
        valid, msg = InputValidator.validate_parts(1)
        assert valid is True
        assert msg is None
        valid, msg = InputValidator.validate_parts(100)
        assert valid is True

    def test_zero_invalid(self):
        valid, msg = InputValidator.validate_parts(0)
        assert valid is False
        assert "positive" in msg

    def test_negative_invalid(self):
        valid, msg = InputValidator.validate_parts(-1)
        assert valid is False

    def test_over_limit_invalid(self):
        valid, msg = InputValidator.validate_parts(101)
        assert valid is False
        assert "100" in msg or "large" in msg.lower()


class TestValidateGrid:
    """Tests for InputValidator.validate_grid()."""

    def test_valid_3x3(self):
        valid, msg = InputValidator.validate_grid(3, 3)
        assert valid is True
        assert msg is None

    def test_valid_10x10(self):
        valid, msg = InputValidator.validate_grid(10, 10)
        assert valid is True

    def test_valid_20x5(self):
        valid, msg = InputValidator.validate_grid(20, 5)
        assert valid is True

    def test_zero_invalid(self):
        valid, msg = InputValidator.validate_grid(0, 3)
        assert valid is False
        valid, msg = InputValidator.validate_grid(3, 0)
        assert valid is False

    def test_over_20_invalid(self):
        valid, msg = InputValidator.validate_grid(21, 1)
        assert valid is False
        assert "20" in msg

    def test_over_100_pages_invalid(self):
        valid, msg = InputValidator.validate_grid(20, 20)
        assert valid is False
        assert "100" in msg


class TestValidateDpi:
    """Tests for InputValidator.validate_dpi()."""

    def test_valid(self):
        valid, msg = InputValidator.validate_dpi(300)
        assert valid is True
        assert msg is None

    def test_zero_invalid(self):
        valid, msg = InputValidator.validate_dpi(0)
        assert valid is False

    def test_too_low_invalid(self):
        valid, msg = InputValidator.validate_dpi(71)
        assert valid is False
        assert "72" in msg or "low" in msg.lower()

    def test_too_high_invalid(self):
        valid, msg = InputValidator.validate_dpi(1201)
        assert valid is False
        assert "1200" in msg or "high" in msg.lower()


class TestValidateFilePath:
    """Tests for InputValidator.validate_file_path()."""

    def test_missing_file(self):
        valid, msg = InputValidator.validate_file_path("/nonexistent/path/image.png")
        assert valid is False
        assert "not found" in msg.lower() or "exist" in msg.lower()

    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            valid, msg = InputValidator.validate_file_path(path)
            assert valid is True
            assert msg is None
        finally:
            os.unlink(path)

    def test_directory_not_valid_as_file(self):
        with tempfile.TemporaryDirectory() as d:
            valid, msg = InputValidator.validate_file_path(d)
            assert valid is False
            assert "not a file" in msg.lower() or "directory" in msg.lower()


class TestValidateFormat:
    """Tests for InputValidator.validate_format()."""

    def test_empty_ok(self):
        valid, msg = InputValidator.validate_format("")
        assert valid is True

    def test_valid_formats(self):
        for fmt in ["png", "jpg", "jpeg", "PNG", "webp"]:
            valid, msg = InputValidator.validate_format(fmt)
            assert valid is True, f"Format {fmt} should be valid"

    def test_invalid_format(self):
        valid, msg = InputValidator.validate_format("xyz")
        assert valid is False
        assert "unsupported" in msg.lower() or "valid" in msg.lower()
```

================================================================================
SUMMARY
================================================================================

Total scan time: 0.02 seconds
Total files found: 134
Files processed: 25
Files skipped: 109
Total code lines: 5,211
Directories skipped: 8

Skipped directories:
  - .pytest_cache
  - logs
  - poster_maker/__pycache__
  - tests/__pycache__
  - poster_maker/cli/__pycache__
  - poster_maker/config/__pycache__
  - poster_maker/core/__pycache__
  - poster_maker/utils/__pycache__

Skip reasons:
  - Excluded file: .DS_Store: 7
  - Excluded extension: .jpg: 38
  - Excluded extension: .jpeg: 22
  - Size exceeds limit (21.8 MB): 1
  - Size exceeds limit (17.7 MB): 1
  - Size exceeds limit (405.4 MB): 1
  - Size exceeds limit (33.7 MB): 1
  - Size exceeds limit (40.1 MB): 1
  - Size exceeds limit (43.6 MB): 1
  - Size exceeds limit (21.1 MB): 1
  - Size exceeds limit (140.4 MB): 1
  - Size exceeds limit (103.6 MB): 1
  - Size exceeds limit (84.1 MB): 1
  - Excluded extension: .pdf: 3
  - Size exceeds limit (18.7 MB): 1
  - Size exceeds limit (18.5 MB): 2
  - Size exceeds limit (17.8 MB): 1
  - Size exceeds limit (55.0 MB): 1
  - Excluded extension: .png: 16
  - Size exceeds limit (10.3 MB): 1
  - Size exceeds limit (25.6 MB): 1
  - Size exceeds limit (10.9 MB): 1
  - Size exceeds limit (12.5 MB): 1
  - Size exceeds limit (57.5 MB): 1
  - Size exceeds limit (48.1 MB): 1
  - Excluded extension: .txt: 2

Processed files with line counts:
  - NextSteps.md (252 lines)
  - README.md (499 lines)
  - config/settings.yaml (74 lines)
  - main.py (533 lines)
  - poster_maker/__init__.py (5 lines)
  - poster_maker/cli/__init__.py (1 lines)
  - poster_maker/cli/arg_parser.py (138 lines)
  - poster_maker/cli/interactive.py (650 lines)
  - poster_maker/config/__init__.py (1 lines)
  - poster_maker/config/config_loader.py (101 lines)
  - poster_maker/core/__init__.py (1 lines)
  - poster_maker/core/file_manager.py (119 lines)
  - poster_maker/core/image_processor.py (505 lines)
  - poster_maker/utils/__init__.py (1 lines)
  - poster_maker/utils/display_service.py (192 lines)
  - poster_maker/utils/logger.py (193 lines)
  - poster_maker/utils/memory_service.py (121 lines)
  - poster_maker/utils/pdf_service.py (909 lines)
  - poster_maker/utils/validators.py (172 lines)
  - pyproject.toml (32 lines)
  - tests/__init__.py (1 lines)
  - tests/test_interactive.py (225 lines)
  - tests/test_memory_service.py (48 lines)
  - tests/test_pdf_logic.py (267 lines)
  - tests/test_validators.py (171 lines)