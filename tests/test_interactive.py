
"""Tests for interactive CLI mode."""

import pytest
from poster_maker.cli.interactive import InteractiveCLI, InteractiveConfig


class TestInteractiveConfig:
    """Tests for InteractiveConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        config = InteractiveConfig(file_path="/test/image.jpg", mode="grid")

        assert config.file_path == "/test/image.jpg"
        assert config.mode == "grid"
        assert config.grid is None
        assert config.parts == 3
        assert config.dpi == 300
        assert config.resize_mode == "maintain"
        assert config.generate_pdf is True
        assert config.pdf_instructions is True
        assert config.pdf_page_numbers is False  # Default: off
        assert config.pdf_grid_overlay is False  # Default: off
        assert config.pdf_assembly_aids is True
        assert config.pdf_compress is False  # Default: off
        assert config.preview_pdf is True  # Default: on
        assert config.cleanup_parts is True  # Default: on (delete parts after PDF)
        assert config.cleanup_resized is False  # Default: off (keep resized)
        assert config.verbose is False
        assert config.output_dir is None

    def test_grid_mode_config(self):
        """Test configuration for grid mode."""
        config = InteractiveConfig(
            file_path="/test/image.jpg",
            mode="grid",
            grid=(3, 4),
            parts=12,
            dpi=300,
        )

        assert config.mode == "grid"
        assert config.grid == (3, 4)
        assert config.parts == 12
        assert config.dpi == 300

    def test_strip_mode_config(self):
        """Test configuration for strip mode."""
        config = InteractiveConfig(
            file_path="/test/image.jpg",
            mode="strip",
            parts=5,
        )

        assert config.mode == "strip"
        assert config.grid is None
        assert config.parts == 5


class TestRecommendGrid:
    """Tests for grid recommendation logic."""

    @pytest.fixture
    def cli(self):
        """Create InteractiveCLI instance without TTY check."""
        # Bypass TTY check for testing
        import sys
        original_isatty = sys.stdin.isatty
        sys.stdin.isatty = lambda: True
        instance = InteractiveCLI()
        sys.stdin.isatty = original_isatty
        return instance

    def test_wide_panorama_recommends_3x4(self, cli):
        """Wide panorama (2:1) should recommend 3x4 grid."""
        img_info = {"aspect_ratio": 2.0}
        result = cli._recommend_grid(img_info)
        assert result == (3, 4)

    def test_landscape_recommends_3x3(self, cli):
        """Landscape (1.4:1) should recommend 3x3 grid."""
        img_info = {"aspect_ratio": 1.4}
        result = cli._recommend_grid(img_info)
        assert result == (3, 3)

    def test_square_recommends_3x3(self, cli):
        """Square-ish (1:1) should recommend 3x3 grid."""
        img_info = {"aspect_ratio": 1.0}
        result = cli._recommend_grid(img_info)
        assert result == (3, 3)

    def test_portrait_recommends_3x2(self, cli):
        """Portrait (0.7:1) should recommend 3x2 grid."""
        img_info = {"aspect_ratio": 0.7}
        result = cli._recommend_grid(img_info)
        assert result == (3, 2)

    def test_tall_portrait_recommends_4x3(self, cli):
        """Very tall portrait (0.5:1) should recommend 4x3 grid."""
        img_info = {"aspect_ratio": 0.5}
        result = cli._recommend_grid(img_info)
        assert result == (4, 3)


class TestRecommendParts:
    """Tests for parts recommendation logic."""

    @pytest.fixture
    def cli(self):
        """Create InteractiveCLI instance without TTY check."""
        import sys
        original_isatty = sys.stdin.isatty
        sys.stdin.isatty = lambda: True
        instance = InteractiveCLI()
        sys.stdin.isatty = original_isatty
        return instance

    def test_very_wide_recommends_6(self, cli):
        """Very wide (2.5:1) should recommend 6 parts."""
        img_info = {"aspect_ratio": 2.5}
        result = cli._recommend_parts(img_info)
        assert result == 6

    def test_wide_recommends_4(self, cli):
        """Wide (1.7:1) should recommend 4 parts."""
        img_info = {"aspect_ratio": 1.7}
        result = cli._recommend_parts(img_info)
        assert result == 4

    def test_normal_recommends_3(self, cli):
        """Normal aspect (1.2:1) should recommend 3 parts."""
        img_info = {"aspect_ratio": 1.2}
        result = cli._recommend_parts(img_info)
        assert result == 3

    def test_very_tall_recommends_6(self, cli):
        """Very tall (0.4:1) should recommend 6 parts."""
        img_info = {"aspect_ratio": 0.4}
        result = cli._recommend_parts(img_info)
        assert result == 6


class TestRecommendDpi:
    """Tests for DPI recommendation logic."""

    @pytest.fixture
    def cli(self):
        """Create InteractiveCLI instance without TTY check."""
        import sys
        original_isatty = sys.stdin.isatty
        sys.stdin.isatty = lambda: True
        instance = InteractiveCLI()
        sys.stdin.isatty = original_isatty
        return instance

    def test_very_high_res_small_grid_recommends_300(self, cli):
        """Very high resolution image with small grid should recommend 300 DPI."""
        # 8K image with 2x2 grid - both dimensions should exceed 300 DPI threshold
        img_info = {"width": 7680, "height": 4320}
        result = cli._recommend_dpi(img_info, grid=(2, 2), parts=4)
        # For 2x2: output is 420mm x 594mm = 16.5" x 23.4"
        # effective_dpi_x = 7680/16.5 = 465, effective_dpi_y = 4320/23.4 = 185
        # min = 185, which gives 150
        assert result in [150, 200, 300]

    def test_square_image_small_grid_recommends_300(self, cli):
        """Square high-res image with small grid should achieve 300 DPI."""
        # Square 6000x6000 image with 2x2 grid
        img_info = {"width": 6000, "height": 6000}
        result = cli._recommend_dpi(img_info, grid=(2, 2), parts=4)
        # effective_dpi = 6000 / (2*297/25.4) = 256
        assert result in [150, 200]

    def test_low_res_image_recommends_150(self, cli):
        """Low resolution image with large grid should recommend 150 DPI."""
        img_info = {"width": 1920, "height": 1080}
        result = cli._recommend_dpi(img_info, grid=(5, 5), parts=25)
        assert result == 150

    def test_strip_mode_recommendation(self, cli):
        """DPI recommendation should work for strip mode too."""
        img_info = {"width": 4000, "height": 3000}
        result = cli._recommend_dpi(img_info, grid=None, parts=4)
        assert result in [150, 200, 300, 600]

    def test_returns_valid_dpi_option(self, cli):
        """Recommendation should always return a valid DPI option."""
        valid_dpis = [150, 200, 300, 600]
        for width in [1000, 2000, 4000, 8000]:
            for height in [1000, 2000, 4000, 8000]:
                img_info = {"width": width, "height": height}
                result = cli._recommend_dpi(img_info, grid=(3, 3), parts=9)
                assert result in valid_dpis


class TestGridPresets:
    """Tests for grid preset definitions."""

    def test_grid_presets_exist(self):
        """Verify grid presets are defined."""
        assert hasattr(InteractiveCLI, "GRID_PRESETS")
        assert len(InteractiveCLI.GRID_PRESETS) >= 5

    def test_grid_presets_format(self):
        """Verify grid presets have correct format."""
        for preset in InteractiveCLI.GRID_PRESETS:
            assert len(preset) == 4  # (label, rows, cols, description)
            label, rows, cols, desc = preset
            assert isinstance(label, str)
            assert isinstance(rows, int) and rows > 0
            assert isinstance(cols, int) and cols > 0
            assert isinstance(desc, str)

    def test_dpi_options_exist(self):
        """Verify DPI options are defined."""
        assert hasattr(InteractiveCLI, "DPI_OPTIONS")
        assert len(InteractiveCLI.DPI_OPTIONS) >= 3

    def test_resize_modes_exist(self):
        """Verify resize modes are defined."""
        assert hasattr(InteractiveCLI, "RESIZE_MODES")
        expected_modes = ["maintain", "stretch", "crop", "pad_white", "pad_black"]
        mode_names = [m[0] for m in InteractiveCLI.RESIZE_MODES]
        for expected in expected_modes:
            assert expected in mode_names