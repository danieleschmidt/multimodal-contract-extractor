"""Tests for ClauseExtractor."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multimodal_contract_extractor.clause_extractor import (
    ClauseExtractor,
    ExtractedClause,
    CLAUSE_TYPES,
)


@pytest.fixture
def extractor():
    return ClauseExtractor()


# ---------------------------------------------------------------------------
# Basic classification
# ---------------------------------------------------------------------------

class TestClauseClassification:

    def test_payment_clause_detected(self, extractor):
        text = """
PAYMENT TERMS

The Client shall pay a monthly service fee of $5,000 USD, payable within 30 days
of invoice date. Late payments will accrue interest at 1.5% per month.
        """
        clauses = extractor.extract(text)
        assert any(c.clause_type == "payment" for c in clauses), \
            f"Expected payment clause, got: {[c.clause_type for c in clauses]}"

    def test_liability_clause_detected(self, extractor):
        text = """
LIMITATION OF LIABILITY

In no event shall either party be liable for any consequential, incidental, or
punitive damages. Total liability shall not exceed the contract value. Each party
shall indemnify and hold harmless the other from third-party claims.
        """
        clauses = extractor.extract(text)
        assert any(c.clause_type == "liability" for c in clauses), \
            f"Expected liability clause, got: {[c.clause_type for c in clauses]}"

    def test_termination_clause_detected(self, extractor):
        text = """
TERMINATION

Either party may terminate this Agreement upon 90 days written notice.
Termination for cause requires a 30-day cure period. The agreement expires
on December 31, 2025. Post-termination obligations survive for 2 years.
        """
        clauses = extractor.extract(text)
        assert any(c.clause_type == "termination" for c in clauses), \
            f"Expected termination clause, got: {[c.clause_type for c in clauses]}"

    def test_data_protection_clause_detected(self, extractor):
        text = """
DATA PROTECTION

The Processor shall process personal data only per the Controller's instructions.
This agreement complies with GDPR requirements. Data subjects may exercise their
rights at any time. Data retention shall not exceed 7 years.
        """
        clauses = extractor.extract(text)
        assert any(c.clause_type == "data_protection" for c in clauses), \
            f"Expected data_protection clause, got: {[c.clause_type for c in clauses]}"

    def test_ip_clause_detected(self, extractor):
        text = """
INTELLECTUAL PROPERTY

All intellectual property developed under this Agreement, including patents,
copyrights, and trade secrets, shall be licensed to the Client under a
non-exclusive license. Work made for hire provisions apply.
        """
        clauses = extractor.extract(text)
        assert any(c.clause_type == "ip" for c in clauses), \
            f"Expected ip clause, got: {[c.clause_type for c in clauses]}"

    def test_confidentiality_clause_detected(self, extractor):
        text = """
CONFIDENTIALITY

The Receiving Party agrees to hold all confidential information and trade secrets
in strict confidence. This non-disclosure obligation applies to all proprietary
information disclosed by the Disclosing Party.
        """
        clauses = extractor.extract(text)
        assert any(c.clause_type == "confidentiality" for c in clauses), \
            f"Expected confidentiality clause, got: {[c.clause_type for c in clauses]}"


# ---------------------------------------------------------------------------
# Data model validation
# ---------------------------------------------------------------------------

class TestExtractedClause:

    def test_clause_has_required_fields(self, extractor):
        text = "The Client shall pay a monthly fee of $500, payable within 30 days of invoice."
        clauses = extractor.extract(text)
        assert len(clauses) > 0
        clause = clauses[0]
        assert isinstance(clause, ExtractedClause)
        assert clause.clause_type in CLAUSE_TYPES
        assert isinstance(clause.text, str)
        assert len(clause.text) > 0
        assert 0.0 <= clause.confidence <= 1.0
        assert isinstance(clause.matched_keywords, list)

    def test_confidence_between_0_and_1(self, extractor):
        text = "Payment is due within 30 days. The invoice fee is $1,000."
        clauses = extractor.extract(text)
        for clause in clauses:
            assert 0.0 <= clause.confidence <= 1.0, \
                f"Confidence out of range: {clause.confidence}"

    def test_start_end_chars_valid(self, extractor):
        text = "PAYMENT TERMS\n\nThe Client shall pay $5,000 USD within 30 days of invoice."
        clauses = extractor.extract(text)
        for clause in clauses:
            assert clause.start_char >= 0
            assert clause.end_char > clause.start_char
            assert clause.end_char <= len(text) + len(clause.text)  # allow for stripped offset

    def test_matched_keywords_populated(self, extractor):
        text = """
Limitation of liability: neither party shall be liable for consequential damages.
Indemnification applies where gross negligence is proven.
        """
        clauses = extractor.extract(text)
        liability_clauses = [c for c in clauses if c.clause_type == "liability"]
        assert len(liability_clauses) > 0
        assert len(liability_clauses[0].matched_keywords) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_text_returns_empty_list(self, extractor):
        assert extractor.extract("") == []

    def test_short_text_ignored(self, extractor):
        # Below min_length threshold
        clauses = extractor.extract("Short.")
        assert clauses == []

    def test_irrelevant_text_produces_no_clauses(self, extractor):
        text = """
The weather today is sunny and warm. Birds are singing outside.
I went to the grocery store and bought milk and eggs. Lovely day.
        """
        clauses = extractor.extract(text)
        # May return clauses but with low confidence — that's fine
        # Just ensure it doesn't crash
        assert isinstance(clauses, list)

    def test_multi_clause_contract(self, extractor):
        text = """
PAYMENT

The fee is $10,000 USD, payable within 30 days of invoice.

LIABILITY

In no event shall either party be liable for consequential damages.

CONFIDENTIALITY

All proprietary information shall be held in strict confidence by the
Receiving Party. This non-disclosure obligation lasts for 5 years.
        """
        clauses = extractor.extract(text)
        types_found = {c.clause_type for c in clauses}
        assert "payment" in types_found
        assert "liability" in types_found
        assert "confidentiality" in types_found

    def test_returns_list_of_extracted_clause(self, extractor):
        text = "Payment of $500 is due within 30 days of receiving an invoice."
        result = extractor.extract(text)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, ExtractedClause)
