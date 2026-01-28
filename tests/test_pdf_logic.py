
# tests/test_pdf_logic.py
"""
Tests for PDF generation logic, particularly duplex back page calculations.
These are pure logic tests that don't require actual PDF generation.
"""
import pytest


class TestGridPositionCalculation:
    """Test grid position calculations for duplex back pages."""

    def test_position_calculation_3x3_grid(self):
        """Test row/col calculation for a 3x3 grid."""
        grid_rows, grid_cols = 3, 3
        
        # Part 1 should be Row 0, Col 0 (top-left)
        part_num = 1
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 0 and col == 0, "Part 1 should be at Row 0, Col 0"
        
        # Part 5 should be Row 1, Col 1 (center)
        part_num = 5
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 1 and col == 1, "Part 5 should be at Row 1, Col 1"
        
        # Part 9 should be Row 2, Col 2 (bottom-right)
        part_num = 9
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 2 and col == 2, "Part 9 should be at Row 2, Col 2"

    def test_position_calculation_2x4_grid(self):
        """Test row/col calculation for a 2x4 grid (2 rows, 4 columns)."""
        grid_rows, grid_cols = 2, 4
        
        # Part 1 should be Row 0, Col 0
        part_num = 1
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 0 and col == 0
        
        # Part 4 should be Row 0, Col 3 (end of first row)
        part_num = 4
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 0 and col == 3
        
        # Part 5 should be Row 1, Col 0 (start of second row)
        part_num = 5
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 1 and col == 0
        
        # Part 8 should be Row 1, Col 3 (bottom-right)
        part_num = 8
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        assert row == 1 and col == 3


class TestNeighborCalculation:
    """Test neighbor calculation logic for duplex back pages."""

    @staticmethod
    def calculate_neighbors(part_num: int, total_parts: int, grid_rows: int, grid_cols: int) -> dict:
        """
        Calculate neighbors for a given part.
        This mirrors the logic in _add_duplex_back_page.
        """
        row = (part_num - 1) // grid_cols
        col = (part_num - 1) % grid_cols
        
        neighbors = {}
        
        # Above
        if row > 0:
            neighbors["above"] = part_num - grid_cols
        
        # Below
        if row < grid_rows - 1 and part_num + grid_cols <= total_parts:
            neighbors["below"] = part_num + grid_cols
        
        # Left
        if col > 0:
            neighbors["left"] = part_num - 1
        
        # Right
        if col < grid_cols - 1 and part_num + 1 <= total_parts:
            neighbors["right"] = part_num + 1
        
        return neighbors

    def test_corner_top_left_3x3(self):
        """Test neighbors for top-left corner (Page 1) in 3x3 grid."""
        neighbors = self.calculate_neighbors(1, 9, 3, 3)
        
        assert "above" not in neighbors, "Top-left has no neighbor above"
        assert "left" not in neighbors, "Top-left has no neighbor left"
        assert neighbors.get("right") == 2, "Top-left should have Page 2 on right"
        assert neighbors.get("below") == 4, "Top-left should have Page 4 below"

    def test_corner_top_right_3x3(self):
        """Test neighbors for top-right corner (Page 3) in 3x3 grid."""
        neighbors = self.calculate_neighbors(3, 9, 3, 3)
        
        assert "above" not in neighbors, "Top-right has no neighbor above"
        assert "right" not in neighbors, "Top-right has no neighbor right"
        assert neighbors.get("left") == 2, "Top-right should have Page 2 on left"
        assert neighbors.get("below") == 6, "Top-right should have Page 6 below"

    def test_corner_bottom_left_3x3(self):
        """Test neighbors for bottom-left corner (Page 7) in 3x3 grid."""
        neighbors = self.calculate_neighbors(7, 9, 3, 3)
        
        assert "below" not in neighbors, "Bottom-left has no neighbor below"
        assert "left" not in neighbors, "Bottom-left has no neighbor left"
        assert neighbors.get("above") == 4, "Bottom-left should have Page 4 above"
        assert neighbors.get("right") == 8, "Bottom-left should have Page 8 on right"

    def test_corner_bottom_right_3x3(self):
        """Test neighbors for bottom-right corner (Page 9) in 3x3 grid."""
        neighbors = self.calculate_neighbors(9, 9, 3, 3)
        
        assert "below" not in neighbors, "Bottom-right has no neighbor below"
        assert "right" not in neighbors, "Bottom-right has no neighbor right"
        assert neighbors.get("above") == 6, "Bottom-right should have Page 6 above"
        assert neighbors.get("left") == 8, "Bottom-right should have Page 8 on left"

    def test_center_3x3(self):
        """Test neighbors for center piece (Page 5) in 3x3 grid - should have all 4."""
        neighbors = self.calculate_neighbors(5, 9, 3, 3)
        
        assert neighbors.get("above") == 2, "Center should have Page 2 above"
        assert neighbors.get("below") == 8, "Center should have Page 8 below"
        assert neighbors.get("left") == 4, "Center should have Page 4 on left"
        assert neighbors.get("right") == 6, "Center should have Page 6 on right"
        assert len(neighbors) == 4, "Center piece should have exactly 4 neighbors"

    def test_edge_top_middle_3x3(self):
        """Test neighbors for top-middle edge (Page 2) in 3x3 grid."""
        neighbors = self.calculate_neighbors(2, 9, 3, 3)
        
        assert "above" not in neighbors, "Top-middle has no neighbor above"
        assert neighbors.get("below") == 5, "Top-middle should have Page 5 below"
        assert neighbors.get("left") == 1, "Top-middle should have Page 1 on left"
        assert neighbors.get("right") == 3, "Top-middle should have Page 3 on right"
        assert len(neighbors) == 3, "Top-middle should have exactly 3 neighbors"

    def test_vertical_strip_1x4(self):
        """Test neighbors for vertical strip (1 column, 4 rows)."""
        # Part 1: top
        neighbors = self.calculate_neighbors(1, 4, 4, 1)
        assert "above" not in neighbors
        assert "left" not in neighbors
        assert "right" not in neighbors
        assert neighbors.get("below") == 2
        
        # Part 2: middle-top
        neighbors = self.calculate_neighbors(2, 4, 4, 1)
        assert neighbors.get("above") == 1
        assert neighbors.get("below") == 3
        assert "left" not in neighbors
        assert "right" not in neighbors
        
        # Part 4: bottom
        neighbors = self.calculate_neighbors(4, 4, 4, 1)
        assert neighbors.get("above") == 3
        assert "below" not in neighbors

    def test_horizontal_strip_1x4(self):
        """Test neighbors for horizontal strip (1 row, 4 columns)."""
        # Part 1: left
        neighbors = self.calculate_neighbors(1, 4, 1, 4)
        assert "above" not in neighbors
        assert "below" not in neighbors
        assert "left" not in neighbors
        assert neighbors.get("right") == 2
        
        # Part 2: middle-left
        neighbors = self.calculate_neighbors(2, 4, 1, 4)
        assert neighbors.get("left") == 1
        assert neighbors.get("right") == 3
        assert "above" not in neighbors
        assert "below" not in neighbors
        
        # Part 4: right
        neighbors = self.calculate_neighbors(4, 4, 1, 4)
        assert neighbors.get("left") == 3
        assert "right" not in neighbors


class TestPageCountCalculation:
    """Test total page count calculation with duplex enabled."""

    @staticmethod
    def calculate_total_pages(
        num_parts: int,
        include_instructions: bool,
        include_duplex: bool
    ) -> int:
        """Calculate total PDF pages based on settings."""
        pages = num_parts  # Base: one page per part
        
        if include_instructions:
            pages += 1  # Instructions page
            if include_duplex:
                pages += 1  # Blank back page for instructions
        
        if include_duplex:
            pages += num_parts  # Back page for each part
        
        return pages

    def test_4_parts_no_extras(self):
        """4 parts with no instructions, no duplex = 4 pages."""
        assert self.calculate_total_pages(4, False, False) == 4

    def test_4_parts_instructions_only(self):
        """4 parts with instructions, no duplex = 5 pages."""
        assert self.calculate_total_pages(4, True, False) == 5

    def test_4_parts_duplex_only(self):
        """4 parts with duplex, no instructions = 8 pages (4 parts + 4 backs)."""
        assert self.calculate_total_pages(4, False, True) == 8

    def test_4_parts_instructions_and_duplex(self):
        """4 parts with instructions + duplex = 10 pages."""
        # 1 instructions + 1 blank + 4 parts + 4 backs = 10
        assert self.calculate_total_pages(4, True, True) == 10

    def test_9_parts_instructions_and_duplex(self):
        """9 parts (3x3 grid) with instructions + duplex = 20 pages."""
        # 1 instructions + 1 blank + 9 parts + 9 backs = 20
        assert self.calculate_total_pages(9, True, True) == 20

    def test_1_part_all_features(self):
        """1 part with all features = 4 pages."""
        # 1 instructions + 1 blank + 1 part + 1 back = 4
        assert self.calculate_total_pages(1, True, True) == 4


class TestYAxisFlip:
    """Test Y-axis coordinate flipping for PDF canvas."""

    def test_y_axis_flip_3x3(self):
        """Verify Y-axis flip puts Row 0 at top of page."""
        grid_rows = 3
        cell_size = 50  # arbitrary
        start_y = 100  # arbitrary start position
        
        # For row 0 (top row), cell_y should be highest
        r = 0
        cell_y_row0 = start_y + (grid_rows - r - 1) * cell_size
        
        # For row 2 (bottom row), cell_y should be lowest
        r = 2
        cell_y_row2 = start_y + (grid_rows - r - 1) * cell_size
        
        assert cell_y_row0 > cell_y_row2, "Row 0 should have higher Y (top of page)"
        assert cell_y_row0 == start_y + 2 * cell_size, "Row 0 Y position incorrect"
        assert cell_y_row2 == start_y, "Row 2 Y position incorrect"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])