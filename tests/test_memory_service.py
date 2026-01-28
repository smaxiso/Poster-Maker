
"""Unit tests for MemoryService."""
import logging

import pytest

from poster_maker.utils.memory_service import MemoryService


@pytest.fixture
def logger():
    return logging.getLogger("test")


class TestMemoryService:
    """Tests for MemoryService.estimate_memory_usage()."""

    def test_returns_positive_memory(self, logger):
        service = MemoryService(logger)
        memory_mb, pct = service.estimate_memory_usage(1920, 1080, 3, 300, "png")
        assert memory_mb > 0
        assert isinstance(memory_mb, (int, float))

    def test_more_parts_increases_estimate(self, logger):
        service = MemoryService(logger)
        m1, _ = service.estimate_memory_usage(1920, 1080, 2, 300, "png")
        m2, _ = service.estimate_memory_usage(1920, 1080, 6, 300, "png")
        assert m2 > m1

    def test_higher_dpi_increases_estimate(self, logger):
        service = MemoryService(logger)
        m1, _ = service.estimate_memory_usage(1920, 1080, 3, 150, "png")
        m2, _ = service.estimate_memory_usage(1920, 1080, 3, 300, "png")
        assert m2 > m1

    def test_different_image_sizes_return_positive_estimates(self, logger):
        """Both small and large source images get positive memory estimates."""
        service = MemoryService(logger)
        m1, _ = service.estimate_memory_usage(800, 600, 3, 300, "png")
        m2, _ = service.estimate_memory_usage(3840, 2160, 3, 300, "png")
        assert m1 > 0 and m2 > 0

    def test_returns_tuple_of_length_two(self, logger):
        service = MemoryService(logger)
        result = service.estimate_memory_usage(100, 100, 2, 72, "jpg")
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Second element may be None if psutil not available
        assert result[1] is None or (isinstance(result[1], (int, float)) and result[1] >= 0)