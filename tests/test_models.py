"""Unit tests for data models."""

from datetime import datetime, timedelta

import pytest

from src.models.clause import ClauseType, LegalClause
from src.models.contract import Contract, ContractParty, ContractType
from src.models.processing import ProcessingResult, ProcessingStatus, ValidationResult


class TestContractParty:
    """Test ContractParty model."""

    def test_valid_party_creation(self):
        """Test creating a valid contract party."""
        party = ContractParty(
            name="John Doe",
            role="employee",
            email="john@example.com",
            address="123 Main St"
        )

        assert party.name == "John Doe"
        assert party.role == "employee"
        assert party.email == "john@example.com"
        assert party.address == "123 Main St"

    def test_invalid_email_raises_error(self):
        """Test that invalid email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            ContractParty(
                name="John Doe",
                role="employee",
                email="invalid-email"
            )

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Party name cannot be empty"):
            ContractParty(name="", role="employee")

    def test_empty_role_raises_error(self):
        """Test that empty role raises ValueError."""
        with pytest.raises(ValueError, match="Party role cannot be empty"):
            ContractParty(name="John Doe", role="")

    def test_party_to_dict(self):
        """Test converting party to dictionary."""
        party = ContractParty(
            name="John Doe",
            role="employee",
            email="john@example.com"
        )

        party_dict = party.to_dict()

        assert party_dict["name"] == "John Doe"
        assert party_dict["role"] == "employee"
        assert party_dict["email"] == "john@example.com"


class TestContract:
    """Test Contract model."""

    def test_contract_creation(self):
        """Test creating a contract with basic information."""
        contract = Contract(
            filename="test_contract.pdf",
            contract_type=ContractType.EMPLOYMENT,
            pages=5
        )

        assert contract.filename == "test_contract.pdf"
        assert contract.contract_type == ContractType.EMPLOYMENT
        assert contract.pages == 5
        assert contract.parties == []
        assert contract.clauses == []

    def test_add_party(self):
        """Test adding a party to a contract."""
        contract = Contract()
        party = ContractParty(name="John Doe", role="employee")

        contract.add_party(party)

        assert len(contract.parties) == 1
        assert contract.parties[0] == party

    def test_add_duplicate_party_raises_error(self):
        """Test that adding duplicate party raises ValueError."""
        contract = Contract()
        party1 = ContractParty(name="John Doe", role="employee")
        party2 = ContractParty(name="John Doe", role="employee")

        contract.add_party(party1)

        with pytest.raises(ValueError, match="Party already exists"):
            contract.add_party(party2)

    def test_get_party_by_role(self):
        """Test getting party by role."""
        contract = Contract()
        employee = ContractParty(name="John Doe", role="employee")
        employer = ContractParty(name="ACME Corp", role="employer")

        contract.add_party(employee)
        contract.add_party(employer)

        found_employee = contract.get_party_by_role("employee")
        found_employer = contract.get_party_by_role("employer")

        assert found_employee == employee
        assert found_employer == employer
        assert contract.get_party_by_role("nonexistent") is None

    def test_contract_expiration(self):
        """Test contract expiration logic."""
        # Future expiration
        future_contract = Contract(
            expiration_date=datetime.utcnow() + timedelta(days=30)
        )
        assert not future_contract.is_expired()
        assert future_contract.is_effective()

        # Past expiration
        expired_contract = Contract(
            expiration_date=datetime.utcnow() - timedelta(days=30)
        )
        assert expired_contract.is_expired()
        assert not expired_contract.is_effective()

    def test_duration_calculation(self):
        """Test contract duration calculation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        contract = Contract(
            effective_date=start_date,
            expiration_date=end_date
        )

        duration = contract.duration_days()
        expected_duration = (end_date - start_date).days

        assert duration == expected_duration

    def test_contract_classification(self):
        """Test automatic contract type classification."""
        # NDA classification
        nda_clause = LegalClause(
            type=ClauseType.CONFIDENTIALITY,
            text="Party agrees to maintain confidentiality of proprietary information."
        )

        contract = Contract(clauses=[nda_clause])
        classified_type = contract.classify_contract_type()

        assert classified_type == ContractType.NDA

    def test_financial_terms_extraction(self):
        """Test extraction of financial terms from contract."""
        payment_clause = LegalClause(
            type=ClauseType.PAYMENT_TERMS,
            text="Employee shall receive annual salary of $75,000 USD payable monthly."
        )

        contract = Contract(clauses=[payment_clause])
        financial_terms = contract.extract_financial_terms()

        assert "amounts" in financial_terms
        assert "currencies" in financial_terms
        assert "USD" in financial_terms["currencies"]

    def test_contract_summary(self):
        """Test contract summary generation."""
        contract = Contract(
            title="Employment Agreement",
            contract_type=ContractType.EMPLOYMENT,
            pages=3,
            overall_confidence=0.95
        )

        party = ContractParty(name="John Doe", role="employee")
        contract.add_party(party)

        summary = contract.get_summary()

        assert summary["title"] == "Employment Agreement"
        assert summary["type"] == "employment_agreement"
        assert summary["pages"] == 3
        assert summary["confidence"] == 0.95
        assert summary["parties_count"] == 1
        assert len(summary["key_parties"]) == 1

    def test_contract_to_dict_and_from_dict(self):
        """Test contract serialization and deserialization."""
        original_contract = Contract(
            title="Test Contract",
            contract_type=ContractType.SERVICE,
            filename="test.pdf",
            pages=2
        )

        party = ContractParty(name="Test Party", role="client")
        original_contract.add_party(party)

        # Convert to dict
        contract_dict = original_contract.to_dict()

        # Convert back to contract
        restored_contract = Contract.from_dict(contract_dict)

        assert restored_contract.title == original_contract.title
        assert restored_contract.contract_type == original_contract.contract_type
        assert restored_contract.filename == original_contract.filename
        assert restored_contract.pages == original_contract.pages
        assert len(restored_contract.parties) == 1
        assert restored_contract.parties[0].name == "Test Party"


class TestLegalClause:
    """Test LegalClause model."""

    def test_clause_creation(self):
        """Test creating a legal clause."""
        clause = LegalClause(
            type=ClauseType.TERMINATION,
            text="This agreement may be terminated with 30 days notice.",
            page=1,
            confidence=0.9
        )

        assert clause.type == ClauseType.TERMINATION
        assert "30 days notice" in clause.text
        assert clause.page == 1
        assert clause.confidence == 0.9

    def test_automatic_key_terms_extraction(self):
        """Test automatic extraction of key terms."""
        clause = LegalClause(
            text="Employee shall receive $50,000 annually within 30 days of employment start."
        )

        # Key terms should be automatically extracted
        assert len(clause.key_terms) > 0
        assert any("$50,000" in term for term in clause.key_terms)
        assert any("30 days" in term for term in clause.key_terms)

    def test_entity_extraction(self):
        """Test automatic entity extraction."""
        clause = LegalClause(
            text="John Smith of ACME Corporation agrees to the terms set forth in New York."
        )

        entities = clause.entities
        assert "persons" in entities
        assert "organizations" in entities
        assert "locations" in entities

    def test_obligation_extraction(self):
        """Test extraction of legal obligations."""
        clause = LegalClause(
            text="Employee shall maintain confidentiality and must not disclose proprietary information."
        )

        assert len(clause.obligations) > 0
        assert any("maintain confidentiality" in obligation for obligation in clause.obligations)

    def test_condition_extraction(self):
        """Test extraction of conditional terms."""
        clause = LegalClause(
            text="If the employee terminates, unless provided otherwise, confidentiality shall remain."
        )

        assert len(clause.conditions) > 0
        assert any("employee terminates" in condition for condition in clause.conditions)

    def test_date_extraction(self):
        """Test extraction and parsing of dates."""
        clause = LegalClause(
            text="Agreement effective January 1, 2024 and expires on 12/31/2024."
        )

        assert len(clause.dates) >= 1
        assert any(date.year == 2024 for date in clause.dates)

    def test_amount_extraction(self):
        """Test extraction of financial amounts."""
        clause = LegalClause(
            text="Base salary of $75,000 plus bonus of USD 5,000 annually."
        )

        assert len(clause.amounts) >= 2
        assert any("$75,000" in amount for amount in clause.amounts)
        assert any("5,000" in amount for amount in clause.amounts)

    def test_clause_type_classification(self):
        """Test automatic clause type classification."""
        # Compensation clause
        comp_clause = LegalClause(
            text="Employee shall receive annual salary compensation of $60,000."
        )
        assert comp_clause.type == ClauseType.COMPENSATION

        # Termination clause
        term_clause = LegalClause(
            text="This agreement may be terminated by either party with notice."
        )
        assert term_clause.type == ClauseType.TERMINATION

        # Confidentiality clause
        conf_clause = LegalClause(
            text="All proprietary information shall remain confidential and not be disclosed."
        )
        assert conf_clause.type == ClauseType.CONFIDENTIALITY

    def test_risk_level_assessment(self):
        """Test automatic risk level assessment."""
        # High risk clause
        high_risk_clause = LegalClause(
            text="Employee accepts unlimited liability for any breach of this agreement."
        )
        assert high_risk_clause.risk_level == "high"

        # Low risk clause
        low_risk_clause = LegalClause(
            text="This agreement shall be governed by the laws of California."
        )
        assert low_risk_clause.risk_level == "low"

    def test_financial_clause_detection(self):
        """Test detection of financial clauses."""
        financial_clause = LegalClause(
            type=ClauseType.COMPENSATION,
            text="Annual salary of $80,000."
        )

        non_financial_clause = LegalClause(
            type=ClauseType.GOVERNING_LAW,
            text="Governed by California law."
        )

        assert financial_clause.is_financial_clause()
        assert not non_financial_clause.is_financial_clause()

    def test_deadline_detection(self):
        """Test detection of clauses with deadlines."""
        deadline_clause = LegalClause(
            text="Payment must be made within 30 days of invoice date."
        )

        no_deadline_clause = LegalClause(
            text="This agreement shall be governed by applicable law."
        )

        assert deadline_clause.has_deadline()
        assert not no_deadline_clause.has_deadline()

    def test_clause_summary(self):
        """Test clause summary generation."""
        clause = LegalClause(
            type=ClauseType.PAYMENT_TERMS,
            title="Payment Schedule",
            text="Payments shall be made monthly by the 15th of each month.",
            page=2,
            confidence=0.92,
            risk_level="medium"
        )

        summary = clause.get_clause_summary()

        assert summary["type"] == "payment_terms"
        assert summary["title"] == "Payment Schedule"
        assert summary["page"] == 2
        assert summary["confidence"] == 0.92
        assert summary["risk_level"] == "medium"
        assert summary["has_deadline"] is True

    def test_clause_serialization(self):
        """Test clause to_dict and from_dict methods."""
        original_clause = LegalClause(
            type=ClauseType.LIABILITY,
            title="Limitation of Liability",
            text="Liability shall be limited to direct damages only.",
            page=3,
            confidence=0.88
        )

        # Convert to dict
        clause_dict = original_clause.to_dict()

        # Convert back to clause
        restored_clause = LegalClause.from_dict(clause_dict)

        assert restored_clause.type == original_clause.type
        assert restored_clause.title == original_clause.title
        assert restored_clause.text == original_clause.text
        assert restored_clause.page == original_clause.page
        assert restored_clause.confidence == original_clause.confidence


class TestProcessingResult:
    """Test ProcessingResult model."""

    def test_processing_result_creation(self):
        """Test creating a processing result."""
        result = ProcessingResult(
            document_path="/path/to/contract.pdf",
            status=ProcessingStatus.PENDING
        )

        assert result.document_path == "/path/to/contract.pdf"
        assert result.status == ProcessingStatus.PENDING
        assert result.errors == []
        assert result.extracted_data == {}

    def test_status_updates(self):
        """Test processing status updates."""
        result = ProcessingResult()

        assert result.completed_at is None

        result.set_status(ProcessingStatus.IN_PROGRESS)
        assert result.status == ProcessingStatus.IN_PROGRESS
        assert result.completed_at is None

        result.set_status(ProcessingStatus.COMPLETED)
        assert result.status == ProcessingStatus.COMPLETED
        assert result.completed_at is not None

    def test_error_handling(self):
        """Test processing error handling."""
        from src.models.processing import ProcessingStage

        result = ProcessingResult()

        # Add recoverable error
        result.add_error(
            stage=ProcessingStage.OCR_EXTRACTION,
            error_type="OCRError",
            message="OCR confidence low",
            recoverable=True
        )

        assert result.has_errors()
        assert not result.has_non_recoverable_errors()
        assert result.status == ProcessingStatus.PENDING  # Should not change for recoverable error

        # Add non-recoverable error
        result.add_error(
            stage=ProcessingStage.VALIDATION,
            error_type="ValidationError",
            message="Invalid file format",
            recoverable=False
        )

        assert result.has_non_recoverable_errors()
        assert result.status == ProcessingStatus.FAILED

    def test_success_determination(self):
        """Test determining if processing was successful."""
        # Successful result
        successful_result = ProcessingResult()
        successful_result.set_status(ProcessingStatus.COMPLETED)
        successful_result.validation = ValidationResult(is_valid=True)

        assert successful_result.is_successful()

        # Failed result
        failed_result = ProcessingResult()
        failed_result.set_status(ProcessingStatus.FAILED)

        assert not failed_result.is_successful()

    def test_processing_time_calculation(self):
        """Test processing time calculation."""
        result = ProcessingResult()
        start_time = result.started_at

        # Simulate processing completion
        result.set_status(ProcessingStatus.COMPLETED)

        processing_time = result.get_processing_time()
        assert processing_time is not None
        assert processing_time >= 0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        # Completed result
        completed_result = ProcessingResult()
        completed_result.set_status(ProcessingStatus.COMPLETED)
        assert completed_result.get_success_rate() == 1.0

        # Failed result
        failed_result = ProcessingResult()
        failed_result.set_status(ProcessingStatus.FAILED)
        success_rate = failed_result.get_success_rate()
        assert 0.0 <= success_rate < 1.0

    def test_result_summary(self):
        """Test processing result summary generation."""
        result = ProcessingResult(
            document_path="/test/contract.pdf"
        )
        result.set_status(ProcessingStatus.COMPLETED)
        result.validation = ValidationResult(is_valid=True, file_size_bytes=1024000)
        result.metrics.pages_processed = 5
        result.metrics.clauses_detected = 12
        result.metrics.overall_confidence = 0.91

        summary = result.generate_summary()

        assert summary["document_path"] == "/test/contract.pdf"
        assert summary["status"] == "completed"
        assert summary["success"] is True
        assert summary["pages_processed"] == 5
        assert summary["clauses_detected"] == 12
        assert summary["overall_confidence"] == 0.91
        assert summary["file_size_mb"] == 1.0  # 1024000 bytes = 1MB

    def test_result_serialization(self):
        """Test processing result serialization."""
        from src.models.processing import ProcessingStage

        original_result = ProcessingResult(
            document_path="/test/document.pdf"
        )
        original_result.set_status(ProcessingStatus.COMPLETED)
        original_result.current_stage = ProcessingStage.SERIALIZATION
        original_result.validation = ValidationResult(is_valid=True)

        # Convert to dict
        result_dict = original_result.to_dict()

        # Convert back to result
        restored_result = ProcessingResult.from_dict(result_dict)

        assert restored_result.document_path == original_result.document_path
        assert restored_result.status == original_result.status
        assert restored_result.current_stage == original_result.current_stage
        assert restored_result.validation.is_valid == original_result.validation.is_valid


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_adding_errors_and_warnings(self):
        """Test adding validation errors and warnings."""
        result = ValidationResult(is_valid=True)

        # Add warning (should not affect validity)
        result.add_warning("File is large")
        assert result.is_valid is True
        assert len(result.warnings) == 1

        # Add error (should set invalid)
        result.add_error("File format not supported")
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validation_result_serialization(self):
        """Test validation result to_dict method."""
        result = ValidationResult(
            is_valid=False,
            file_size_bytes=2048000,
            file_type="application/pdf",
            pages_detected=3
        )
        result.add_error("Test error")
        result.add_warning("Test warning")

        result_dict = result.to_dict()

        assert result_dict["is_valid"] is False
        assert result_dict["file_size_bytes"] == 2048000
        assert result_dict["file_type"] == "application/pdf"
        assert result_dict["pages_detected"] == 3
        assert len(result_dict["errors"]) == 1
        assert len(result_dict["warnings"]) == 1
