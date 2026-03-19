"""Tests for EntityExtractor."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multimodal_contract_extractor.entity_extractor import (
    EntityExtractor,
    ExtractedEntity,
    ENTITY_TYPES,
)
from multimodal_contract_extractor.clause_extractor import ExtractedClause


@pytest.fixture
def extractor():
    return EntityExtractor()


def make_clause(text: str, clause_type: str = "payment") -> ExtractedClause:
    """Helper: create a minimal ExtractedClause for testing."""
    return ExtractedClause(
        clause_type=clause_type,
        text=text,
        start_char=0,
        end_char=len(text),
        confidence=0.8,
    )


# ---------------------------------------------------------------------------
# Party extraction
# ---------------------------------------------------------------------------

class TestPartyExtraction:

    def test_detects_company_name_inc(self, extractor):
        text = "This Agreement is between Acme Technologies Inc. and Global Industries Ltd."
        entities = extractor.extract_from_text(text)
        party_values = [e.value for e in entities if e.entity_type == "party"]
        # Should find at least one company name
        assert len(party_values) >= 1
        assert any("Inc" in v or "Ltd" in v for v in party_values)

    def test_detects_referred_to_as(self, extractor):
        text = """The company, hereinafter referred to as "Contractor", agrees to deliver."""
        entities = extractor.extract_from_text(text)
        party_values = [e.value for e in entities if e.entity_type == "party"]
        assert any("Contractor" in v for v in party_values), \
            f"Expected 'Contractor' in parties, got: {party_values}"

    def test_detects_the_client(self, extractor):
        text = "The Client shall pay all invoices within 30 days."
        entities = extractor.extract_from_text(text)
        party_values = [e.value.lower() for e in entities if e.entity_type == "party"]
        assert any("client" in v for v in party_values)

    def test_detects_licensor_licensee(self, extractor):
        text = "The Licensor grants to the Licensee a non-exclusive license to use the software."
        entities = extractor.extract_from_text(text)
        party_values = [e.value.lower() for e in entities if e.entity_type == "party"]
        assert any("licensor" in v or "licensee" in v for v in party_values)


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

class TestDateExtraction:

    def test_detects_iso_date(self, extractor):
        text = "This Agreement is effective as of 2024-01-15."
        entities = extractor.extract_from_text(text)
        date_values = [e.value for e in entities if e.entity_type == "date"]
        assert "2024-01-15" in date_values

    def test_detects_long_date(self, extractor):
        text = "The contract expires on December 31, 2026."
        entities = extractor.extract_from_text(text)
        date_values = [e.value for e in entities if e.entity_type == "date"]
        assert any("December" in v and "2026" in v for v in date_values), \
            f"Expected December 31, 2026 in dates, got: {date_values}"

    def test_detects_duration(self, extractor):
        text = "Notice must be provided 30 days in advance."
        entities = extractor.extract_from_text(text)
        date_values = [e.value.lower() for e in entities if e.entity_type == "date"]
        assert any("30" in v and "day" in v for v in date_values)

    def test_detects_within_duration(self, extractor):
        text = "Payment is due within 14 days of invoice."
        entities = extractor.extract_from_text(text)
        date_values = [e.value.lower() for e in entities if e.entity_type == "date"]
        assert any("within" in v and "14" in v for v in date_values)


# ---------------------------------------------------------------------------
# Amount extraction
# ---------------------------------------------------------------------------

class TestAmountExtraction:

    def test_detects_dollar_amount(self, extractor):
        text = "The monthly fee is $15,000 USD."
        entities = extractor.extract_from_text(text)
        amount_values = [e.value for e in entities if e.entity_type == "amount"]
        assert any("15,000" in v or "15000" in v for v in amount_values), \
            f"Expected $15,000 in amounts, got: {amount_values}"

    def test_detects_eur_amount(self, extractor):
        text = "The purchase price shall be EUR 50,000.00."
        entities = extractor.extract_from_text(text)
        amount_values = [e.value for e in entities if e.entity_type == "amount"]
        assert any("EUR" in v and "50,000" in v for v in amount_values), \
            f"Expected EUR 50,000 in amounts, got: {amount_values}"

    def test_detects_percentage(self, extractor):
        text = "Interest shall accrue at 1.5% per month on overdue amounts."
        entities = extractor.extract_from_text(text)
        amount_values = [e.value for e in entities if e.entity_type == "amount"]
        assert any("1.5" in v and "%" in v for v in amount_values), \
            f"Expected 1.5% in amounts, got: {amount_values}"

    def test_detects_gbp_symbol(self, extractor):
        text = "The total contract value is £250,000."
        entities = extractor.extract_from_text(text)
        amount_values = [e.value for e in entities if e.entity_type == "amount"]
        assert any("250,000" in v for v in amount_values)


# ---------------------------------------------------------------------------
# Jurisdiction extraction
# ---------------------------------------------------------------------------

class TestJurisdictionExtraction:

    def test_detects_governed_by_law(self, extractor):
        text = "This Agreement shall be governed by the laws of England and Wales."
        entities = extractor.extract_from_text(text)
        juris_values = [e.value for e in entities if e.entity_type == "jurisdiction"]
        assert len(juris_values) >= 1, f"Expected jurisdiction, got: {juris_values}"

    def test_detects_courts_of(self, extractor):
        text = "Disputes shall be resolved by the courts of New York."
        entities = extractor.extract_from_text(text)
        juris_values = [e.value for e in entities if e.entity_type == "jurisdiction"]
        assert len(juris_values) >= 1

    def test_detects_standalone_jurisdiction(self, extractor):
        text = "The governing law is that of Germany."
        entities = extractor.extract_from_text(text)
        juris_values = [e.value for e in entities if e.entity_type == "jurisdiction"]
        assert any("Germany" in v for v in juris_values), \
            f"Expected Germany in jurisdictions, got: {juris_values}"


# ---------------------------------------------------------------------------
# Data category extraction
# ---------------------------------------------------------------------------

class TestDataCategoryExtraction:

    def test_detects_personal_data(self, extractor):
        text = "The Processor shall handle personal data in accordance with GDPR."
        entities = extractor.extract_from_text(text, clause_type="data_protection")
        dc_values = [e.value.lower() for e in entities if e.entity_type == "data_category"]
        assert any("personal data" in v for v in dc_values)

    def test_detects_sensitive_data_categories(self, extractor):
        text = "Processing of health data, biometric data, and genetic data requires explicit consent."
        entities = extractor.extract_from_text(text, clause_type="data_protection")
        dc_values = [e.value.lower() for e in entities if e.entity_type == "data_category"]
        assert any("health data" in v or "biometric data" in v or "genetic data" in v for v in dc_values)

    def test_data_categories_not_extracted_from_payment_clause_by_default(self, extractor):
        text = "The Client shall pay $5,000 for processing services."
        entities = extractor.extract_from_text(text, clause_type="payment")
        dc_values = [e for e in entities if e.entity_type == "data_category"]
        assert len(dc_values) == 0


# ---------------------------------------------------------------------------
# extract_from_clause / extract_from_clauses
# ---------------------------------------------------------------------------

class TestExtractFromClause:

    def test_extract_from_clause_uses_clause_type(self, extractor):
        clause = make_clause(
            "Personal data and health data shall be retained for 5 years.",
            clause_type="data_protection",
        )
        entities = extractor.extract_from_clause(clause)
        for e in entities:
            assert e.clause_type == "data_protection"

    def test_extract_from_clauses_aggregates(self, extractor):
        clauses = [
            make_clause("Pay $5,000 within 30 days.", "payment"),
            make_clause(
                "All confidential information must remain secret. "
                "The Receiving Party shall not disclose it.",
                "confidentiality",
            ),
        ]
        entities = extractor.extract_from_clauses(clauses)
        types_found = {e.entity_type for e in entities}
        assert "amount" in types_found or "date" in types_found

    def test_no_duplicate_entities(self, extractor):
        text = "Personal data must be protected. Personal data processing requires consent."
        entities = extractor.extract_from_text(text, clause_type="data_protection")
        values = [e.value.lower() for e in entities if e.entity_type == "data_category"]
        # "personal data" should appear only once
        assert values.count("personal data") <= 1


# ---------------------------------------------------------------------------
# Data model validation
# ---------------------------------------------------------------------------

class TestExtractedEntity:

    def test_entity_has_required_fields(self, extractor):
        text = "The Client shall pay $1,000 within 30 days."
        entities = extractor.extract_from_text(text)
        assert len(entities) > 0
        for e in entities:
            assert isinstance(e, ExtractedEntity)
            assert e.entity_type in ENTITY_TYPES
            assert isinstance(e.value, str)
            assert len(e.value) > 0

    def test_context_field_populated(self, extractor):
        text = "The monthly fee is $5,000, payable by the Client within 30 days."
        entities = extractor.extract_from_text(text)
        for e in entities:
            if e.context is not None:
                assert isinstance(e.context, str)

    def test_returns_list(self, extractor):
        result = extractor.extract_from_text("The Client pays $500.")
        assert isinstance(result, list)
