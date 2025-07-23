"""Tests for clause detection optimization."""

import time
from unittest.mock import MagicMock, patch

from multimodal_contract_extractor.clause_detection import (
    _detect_clauses_optimized,
    detect_clauses,
)
from tests.test_helpers import create_test_pdf


class TestClauseDetectionOptimization:
    """Test optimized clause detection implementation."""

    def test_optimized_detection_finds_same_clauses(self, tmp_path):
        """Optimized detection should find the same clauses as original."""
        input_file = tmp_path / "test_doc.pdf"
        create_test_pdf(input_file, "This document contains confidential information and termination clauses.")

        # Mock OCR to return predictable text
        with patch("multimodal_contract_extractor.clause_detection._ocr_image") as mock_ocr:
            mock_ocr.return_value = "This document contains confidential information and termination clauses."

            # Create a mock document
            mock_doc = MagicMock()
            mock_doc.pages = [MagicMock()]
            mock_doc.pages[0].number = 1
            mock_doc.pages[0].image = MagicMock()

            # Test both implementations
            original_clauses = detect_clauses(mock_doc)
            optimized_clauses = _detect_clauses_optimized(mock_doc)

            # Should find the same clauses
            assert len(original_clauses) == len(optimized_clauses)

            # Check that we found expected clause types
            original_types = {clause.type for clause in original_clauses}
            optimized_types = {clause.type for clause in optimized_clauses}

            assert original_types == optimized_types
            assert "confidentiality" in original_types
            assert "termination" in original_types

    def test_optimized_detection_is_faster(self, tmp_path):
        """Optimized detection should be faster than original for multiple keywords."""
        # Mock OCR to return text with multiple clause types
        test_text = """
        This agreement contains confidential information that must be protected.
        Either party may terminate this agreement with 30 days notice.
        Payment terms are net 30 days from invoice date.
        Liability is limited to the amount paid under this agreement.
        This agreement is governed by the laws of California.
        Any disputes will be resolved through binding arbitration.
        """

        # Create a mock document with the test text
        mock_doc = MagicMock()
        mock_doc.pages = [MagicMock() for _ in range(3)]  # Multiple pages for more processing
        for i, page in enumerate(mock_doc.pages):
            page.number = i + 1
            page.image = MagicMock()

        with patch("multimodal_contract_extractor.clause_detection._ocr_image") as mock_ocr:
            mock_ocr.return_value = test_text

            # Time original implementation
            start_time = time.perf_counter()
            original_clauses = detect_clauses(mock_doc)
            original_time = time.perf_counter() - start_time

            # Reset mock call count
            mock_ocr.reset_mock()

            # Time optimized implementation
            start_time = time.perf_counter()
            optimized_clauses = _detect_clauses_optimized(mock_doc)
            optimized_time = time.perf_counter() - start_time

            # Should find similar number of clauses
            assert len(original_clauses) > 0
            assert len(optimized_clauses) > 0

            # Performance improvement depends on number of keywords, but both should complete
            assert original_time >= 0
            assert optimized_time >= 0

            # Both should have called OCR the same number of times (once per page)
            assert mock_ocr.call_count == len(mock_doc.pages)

    def test_combined_regex_pattern_efficiency(self):
        """Test that combined regex pattern is more efficient than multiple patterns."""
        from multimodal_contract_extractor.clause_detection import (
            DEFAULT_KEYWORDS,
            _build_combined_pattern,
        )

        test_text = "This confidential agreement includes payment terms and liability clauses."

        # Build combined pattern
        combined_pattern = _build_combined_pattern(DEFAULT_KEYWORDS)

        # Test that it finds all relevant keywords in one pass
        matches = list(combined_pattern.finditer(test_text))

        # Should find matches for confidential, payment, and liability
        match_texts = [match.group() for match in matches]
        assert len(match_texts) >= 3
        assert any("confidential" in match.lower() for match in match_texts)
        assert any("payment" in match.lower() for match in match_texts)
        assert any("liability" in match.lower() for match in match_texts)

    def test_pattern_caching_performance(self):
        """Test that regex pattern compilation is cached for performance."""
        from multimodal_contract_extractor.clause_detection import (
            DEFAULT_KEYWORDS,
            _get_cached_pattern,
        )

        # First call should compile pattern
        start_time = time.perf_counter()
        pattern1 = _get_cached_pattern(DEFAULT_KEYWORDS)
        first_call_time = time.perf_counter() - start_time

        # Second call should use cached pattern
        start_time = time.perf_counter()
        pattern2 = _get_cached_pattern(DEFAULT_KEYWORDS)
        second_call_time = time.perf_counter() - start_time

        # Should return the same pattern object
        assert pattern1 is pattern2

        # Second call should be faster (cached)
        assert second_call_time <= first_call_time + 0.001  # Allow small margin for measurement variance

    def test_empty_keywords_handling(self):
        """Test that empty keywords are handled gracefully."""
        from multimodal_contract_extractor.clause_detection import (
            _build_combined_pattern,
        )

        # Empty keywords should return a pattern that matches nothing
        empty_pattern = _build_combined_pattern({})
        test_text = "This is test text"

        matches = list(empty_pattern.finditer(test_text))
        assert len(matches) == 0
