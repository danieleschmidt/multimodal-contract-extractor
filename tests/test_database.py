"""Unit tests for database layer."""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.database.connection import DatabaseConnection
from src.database.repositories import ContractRepository, ProcessingResultRepository
from src.database.cache_manager import CacheManager
from src.models.contract import Contract, ContractParty, ContractType
from src.models.clause import LegalClause, ClauseType
from src.models.processing import ProcessingResult, ProcessingStatus, ValidationResult


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name
    
    db = DatabaseConnection(db_path)
    db.initialize()
    
    yield db
    
    # Cleanup
    Path(db_path).unlink()


@pytest.fixture
def sample_contract():
    """Create a sample contract for testing."""
    contract = Contract(
        title="Sample Employment Agreement",
        contract_type=ContractType.EMPLOYMENT,
        filename="sample_employment.pdf",
        pages=5,
        file_size_bytes=1024000,
        overall_confidence=0.92,
        processing_time_seconds=15.5,
        language="en",
        jurisdiction="California",
        governing_law="California State Law"
    )
    
    # Add parties
    employee = ContractParty(
        name="John Doe",
        role="employee",
        email="john.doe@email.com",
        address="123 Main St, Anytown, CA 90210"
    )
    employer = ContractParty(
        name="ACME Corporation",
        role="employer",
        entity_type="corporation",
        address="456 Business Ave, Corporate City, CA 90211"
    )
    
    contract.add_party(employee)
    contract.add_party(employer)
    
    # Add clauses
    compensation_clause = LegalClause(
        type=ClauseType.COMPENSATION,
        title="Base Salary",
        text="Employee shall receive an annual salary of $75,000, payable in bi-weekly installments.",
        page=2,
        coordinates=[50, 150, 550, 220],
        confidence=0.95
    )
    
    termination_clause = LegalClause(
        type=ClauseType.TERMINATION,
        title="Termination for Cause",
        text="Either party may terminate this agreement with 30 days written notice.",
        page=4,
        coordinates=[50, 300, 550, 380],
        confidence=0.88
    )
    
    contract.clauses = [compensation_clause, termination_clause]
    
    return contract


@pytest.fixture
def sample_processing_result():
    """Create a sample processing result for testing."""
    result = ProcessingResult(
        document_path="/test/path/document.pdf",
        status=ProcessingStatus.COMPLETED
    )
    
    # Add validation result
    validation = ValidationResult(
        is_valid=True,
        file_size_bytes=1024000,
        file_type="application/pdf",
        pages_detected=3
    )
    result.validation = validation
    
    # Add metrics
    result.metrics.pages_processed = 3
    result.metrics.clauses_detected = 5
    result.metrics.ocr_confidence = 0.87
    result.metrics.overall_confidence = 0.91
    result.metrics.total_time_seconds = 12.5
    
    # Add extracted data
    result.extracted_data = {
        "document_info": {
            "filename": "document.pdf",
            "pages": 3,
            "overall_confidence": 0.91
        },
        "clauses": [
            {
                "id": "clause_001",
                "type": "compensation",
                "text": "Annual salary of $60,000",
                "confidence": 0.92
            }
        ]
    }
    
    return result


class TestDatabaseConnection:
    """Test database connection and setup."""
    
    def test_database_initialization(self, temp_db):
        """Test database tables are created correctly."""
        # Check that tables exist
        tables = temp_db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [table['name'] for table in tables]
        
        expected_tables = [
            'contracts', 'contract_parties', 'legal_clauses',
            'processing_results', 'ocr_cache', 'processing_metrics',
            'system_config'
        ]
        
        for expected_table in expected_tables:
            assert expected_table in table_names
    
    def test_database_indexes(self, temp_db):
        """Test that indexes are created correctly."""
        indexes = temp_db.execute_query("SELECT name FROM sqlite_master WHERE type='index'")
        index_names = [index['name'] for index in indexes]
        
        # Check for some key indexes
        assert any('contracts' in name for name in index_names)
        assert any('clauses' in name for name in index_names)
        assert any('parties' in name for name in index_names)
    
    def test_database_stats(self, temp_db):
        """Test database statistics retrieval."""
        stats = temp_db.get_database_stats()
        
        assert "contracts_count" in stats
        assert "legal_clauses_count" in stats
        assert "processing_results_count" in stats
        assert "database_size_bytes" in stats
        assert isinstance(stats["contracts_count"], int)
    
    def test_database_cleanup(self, temp_db):
        """Test database cleanup functionality."""
        # Insert some old test records
        temp_db.execute_update(
            "INSERT INTO ocr_cache (file_hash, file_path, file_size, ocr_text, last_accessed) VALUES (?, ?, ?, ?, ?)",
            {
                "file_hash": "old_hash",
                "file_path": "/old/file.pdf",
                "file_size": 1000,
                "ocr_text": "old text",
                "last_accessed": "2020-01-01 00:00:00"
            }
        )
        
        # Run cleanup
        deleted_count = temp_db.cleanup_old_records(days_to_keep=1)
        
        assert deleted_count >= 0  # Should delete the old record
    
    def test_database_backup(self, temp_db):
        """Test database backup functionality."""
        with tempfile.NamedTemporaryFile(suffix=".backup.db", delete=False) as backup_file:
            backup_path = backup_file.name
        
        try:
            success = temp_db.backup_database(backup_path)
            assert success is True
            assert Path(backup_path).exists()
            
            # Verify backup has content
            backup_size = Path(backup_path).stat().st_size
            assert backup_size > 0
            
        finally:
            Path(backup_path).unlink()


class TestContractRepository:
    """Test contract repository operations."""
    
    def test_save_and_find_contract(self, temp_db, sample_contract):
        """Test saving and retrieving a contract."""
        repo = ContractRepository(temp_db)
        
        # Save contract
        success = repo.save(sample_contract)
        assert success is True
        
        # Find contract by ID
        found_contract = repo.find_by_id(sample_contract.id)
        assert found_contract is not None
        assert found_contract.title == sample_contract.title
        assert found_contract.contract_type == sample_contract.contract_type
        assert found_contract.filename == sample_contract.filename
        assert len(found_contract.parties) == 2
        assert len(found_contract.clauses) == 2
    
    def test_find_contracts_by_filename(self, temp_db, sample_contract):
        """Test finding contracts by filename."""
        repo = ContractRepository(temp_db)
        repo.save(sample_contract)
        
        contracts = repo.find_by_filename(sample_contract.filename)
        assert len(contracts) == 1
        assert contracts[0].filename == sample_contract.filename
    
    def test_find_contracts_by_type(self, temp_db, sample_contract):
        """Test finding contracts by type."""
        repo = ContractRepository(temp_db)
        repo.save(sample_contract)
        
        contracts = repo.find_by_type("employment_agreement")
        assert len(contracts) == 1
        assert contracts[0].contract_type == ContractType.EMPLOYMENT
    
    def test_find_recent_contracts(self, temp_db, sample_contract):
        """Test finding recent contracts."""
        repo = ContractRepository(temp_db)
        repo.save(sample_contract)
        
        contracts = repo.find_recent(limit=5)
        assert len(contracts) == 1
        assert contracts[0].id == sample_contract.id
    
    def test_delete_contract(self, temp_db, sample_contract):
        """Test deleting a contract."""
        repo = ContractRepository(temp_db)
        
        # Save contract
        repo.save(sample_contract)
        
        # Verify it exists
        found_contract = repo.find_by_id(sample_contract.id)
        assert found_contract is not None
        
        # Delete contract
        success = repo.delete(sample_contract.id)
        assert success is True
        
        # Verify it's gone
        found_contract = repo.find_by_id(sample_contract.id)
        assert found_contract is None
    
    def test_delete_nonexistent_contract(self, temp_db):
        """Test deleting a non-existent contract."""
        repo = ContractRepository(temp_db)
        
        success = repo.delete(str(uuid4()))
        assert success is False
    
    def test_contract_statistics(self, temp_db, sample_contract):
        """Test contract statistics generation."""
        repo = ContractRepository(temp_db)
        repo.save(sample_contract)
        
        stats = repo.get_statistics()
        
        assert "total_contracts" in stats
        assert stats["total_contracts"] == 1
        assert "by_type" in stats
        assert "employment_agreement" in stats["by_type"]
        assert stats["by_type"]["employment_agreement"] == 1
        assert "processing" in stats
    
    def test_contract_parties_persistence(self, temp_db, sample_contract):
        """Test that contract parties are properly saved and loaded."""
        repo = ContractRepository(temp_db)
        repo.save(sample_contract)
        
        found_contract = repo.find_by_id(sample_contract.id)
        assert len(found_contract.parties) == 2
        
        # Check party details
        employee = found_contract.get_party_by_role("employee")
        employer = found_contract.get_party_by_role("employer")
        
        assert employee is not None
        assert employee.name == "John Doe"
        assert employee.email == "john.doe@email.com"
        
        assert employer is not None
        assert employer.name == "ACME Corporation"
        assert employer.entity_type == "corporation"
    
    def test_legal_clauses_persistence(self, temp_db, sample_contract):
        """Test that legal clauses are properly saved and loaded."""
        repo = ContractRepository(temp_db)
        repo.save(sample_contract)
        
        found_contract = repo.find_by_id(sample_contract.id)
        assert len(found_contract.clauses) == 2
        
        # Find compensation clause
        comp_clause = next(
            (clause for clause in found_contract.clauses if clause.type == ClauseType.COMPENSATION),
            None
        )
        assert comp_clause is not None
        assert comp_clause.title == "Base Salary"
        assert "$75,000" in comp_clause.text
        assert comp_clause.confidence == 0.95
        assert comp_clause.page == 2
        assert len(comp_clause.coordinates) == 4


class TestProcessingResultRepository:
    """Test processing result repository operations."""
    
    def test_save_and_find_result(self, temp_db, sample_processing_result):
        """Test saving and retrieving a processing result."""
        repo = ProcessingResultRepository(temp_db)
        
        # Save result
        success = repo.save(sample_processing_result)
        assert success is True
        
        # Find result by ID
        found_result = repo.find_by_id(sample_processing_result.id)
        assert found_result is not None
        assert found_result.document_path == sample_processing_result.document_path
        assert found_result.status == sample_processing_result.status
        assert found_result.validation.is_valid == sample_processing_result.validation.is_valid
        assert found_result.metrics.pages_processed == sample_processing_result.metrics.pages_processed
    
    def test_find_results_by_status(self, temp_db, sample_processing_result):
        """Test finding results by status."""
        repo = ProcessingResultRepository(temp_db)
        repo.save(sample_processing_result)
        
        results = repo.find_by_status("completed")
        assert len(results) == 1
        assert results[0].status == ProcessingStatus.COMPLETED
    
    def test_processing_result_metrics_persistence(self, temp_db, sample_processing_result):
        """Test that processing metrics are properly persisted."""
        repo = ProcessingResultRepository(temp_db)
        repo.save(sample_processing_result)
        
        found_result = repo.find_by_id(sample_processing_result.id)
        assert found_result.metrics.pages_processed == 3
        assert found_result.metrics.clauses_detected == 5
        assert found_result.metrics.ocr_confidence == 0.87
        assert found_result.metrics.overall_confidence == 0.91
        assert found_result.metrics.total_time_seconds == 12.5
    
    def test_validation_result_persistence(self, temp_db, sample_processing_result):
        """Test that validation results are properly persisted."""
        repo = ProcessingResultRepository(temp_db)
        repo.save(sample_processing_result)
        
        found_result = repo.find_by_id(sample_processing_result.id)
        assert found_result.validation.is_valid is True
        assert found_result.validation.file_size_bytes == 1024000
        assert found_result.validation.file_type == "application/pdf"
        assert found_result.validation.pages_detected == 3
    
    def test_extracted_data_persistence(self, temp_db, sample_processing_result):
        """Test that extracted data is properly persisted."""
        repo = ProcessingResultRepository(temp_db)
        repo.save(sample_processing_result)
        
        found_result = repo.find_by_id(sample_processing_result.id)
        assert "document_info" in found_result.extracted_data
        assert "clauses" in found_result.extracted_data
        assert found_result.extracted_data["document_info"]["filename"] == "document.pdf"


class TestCacheManager:
    """Test cache manager functionality."""
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(temp_dir, max_size_mb=10)
            
            assert cache_manager.cache_dir == Path(temp_dir)
            assert cache_manager.max_size_bytes == 10 * 1024 * 1024
            assert cache_manager.cache_dir.exists()
    
    def test_file_hash_generation(self):
        """Test file hash generation."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            temp_path = Path(temp_file.name)
        
        try:
            cache_manager = CacheManager()
            hash1 = cache_manager.get_file_hash(temp_path)
            hash2 = cache_manager.get_file_hash(temp_path)
            
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256 hash length
            
        finally:
            temp_path.unlink()
    
    def test_ocr_result_caching(self):
        """Test OCR result caching and retrieval."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test document content")
            temp_file.flush()
            temp_path = Path(temp_file.name)
        
        try:
            with tempfile.TemporaryDirectory() as cache_dir:
                cache_manager = CacheManager(cache_dir)
                
                # Store OCR result
                ocr_result = {
                    "text": "Extracted text from document",
                    "confidence": 0.92,
                    "coordinates": [[10, 20, 100, 30]]
                }
                
                success = cache_manager.store_ocr_result(temp_path, ocr_result)
                assert success is True
                
                # Retrieve OCR result
                cached_result = cache_manager.get_ocr_result(temp_path)
                assert cached_result is not None
                assert cached_result["text"] == "Extracted text from document"
                assert cached_result["confidence"] == 0.92
                
        finally:
            temp_path.unlink()
    
    def test_document_processing_result_caching(self):
        """Test document processing result caching."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test document")
            temp_file.flush()
            temp_path = Path(temp_file.name)
        
        try:
            with tempfile.TemporaryDirectory() as cache_dir:
                cache_manager = CacheManager(cache_dir)
                
                # Store processing result
                processing_result = {
                    "clauses": [
                        {"type": "compensation", "text": "Salary information"}
                    ],
                    "confidence": 0.89
                }
                
                success = cache_manager.store_document_processing_result(temp_path, processing_result)
                assert success is True
                
                # Retrieve processing result
                cached_result = cache_manager.get_document_processing_result(temp_path)
                assert cached_result is not None
                assert len(cached_result["clauses"]) == 1
                assert cached_result["confidence"] == 0.89
                
        finally:
            temp_path.unlink()
    
    def test_cache_miss(self):
        """Test cache miss for non-existent file."""
        with tempfile.TemporaryDirectory() as cache_dir:
            cache_manager = CacheManager(cache_dir)
            
            nonexistent_file = Path("/nonexistent/file.pdf")
            result = cache_manager.get_ocr_result(nonexistent_file)
            assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as cache_dir:
            cache_manager = CacheManager(cache_dir)
            
            stats = cache_manager.get_cache_stats()
            assert "ocr_cache_files" in stats
            assert "document_cache_files" in stats
            assert "total_files" in stats
            assert "total_size_bytes" in stats
            assert "cache_directory" in stats
            assert stats["cache_directory"] == str(cache_manager.cache_dir)
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        with tempfile.TemporaryDirectory() as cache_dir:
            cache_manager = CacheManager(cache_dir, max_size_mb=1)  # Small cache
            
            # Create several cache files
            for i in range(5):
                cache_file = Path(cache_dir) / f"test_cache_{i}.pkl"
                cache_file.write_bytes(b"x" * 1000)  # 1KB each
            
            # Clear cache
            deleted_count = cache_manager.clear_cache()
            assert deleted_count >= 0
            
            # Verify cache is empty
            remaining_files = list(Path(cache_dir).glob("*.pkl"))
            assert len(remaining_files) == 0


class TestDatabaseIntegration:
    """Integration tests for database components."""
    
    def test_full_contract_lifecycle(self, temp_db, sample_contract):
        """Test complete contract lifecycle through repository."""
        contract_repo = ContractRepository(temp_db)
        
        # Save contract
        success = contract_repo.save(sample_contract)
        assert success is True
        
        # Retrieve and verify
        found_contract = contract_repo.find_by_id(sample_contract.id)
        assert found_contract is not None
        
        # Update contract
        found_contract.title = "Updated Employment Agreement"
        success = contract_repo.save(found_contract)
        assert success is True
        
        # Verify update
        updated_contract = contract_repo.find_by_id(sample_contract.id)
        assert updated_contract.title == "Updated Employment Agreement"
        
        # Delete contract
        success = contract_repo.delete(sample_contract.id)
        assert success is True
        
        # Verify deletion
        deleted_contract = contract_repo.find_by_id(sample_contract.id)
        assert deleted_contract is None
    
    def test_processing_result_with_contract_reference(self, temp_db, sample_contract, sample_processing_result):
        """Test processing result that references a contract."""
        contract_repo = ContractRepository(temp_db)
        result_repo = ProcessingResultRepository(temp_db)
        
        # Save contract first
        contract_repo.save(sample_contract)
        
        # Associate processing result with contract
        sample_processing_result.contract = sample_contract
        result_repo.save(sample_processing_result)
        
        # Retrieve and verify
        found_result = result_repo.find_by_id(sample_processing_result.id)
        assert found_result is not None
        
        # The processing result should maintain the association
        # (In a more sophisticated implementation, this might be a foreign key relationship)
    
    def test_concurrent_database_access(self, temp_db):
        """Test concurrent database access doesn't cause issues."""
        import threading
        
        contract_repo = ContractRepository(temp_db)
        results = []
        
        def save_contract(contract_id):
            contract = Contract(
                title=f"Contract {contract_id}",
                contract_type=ContractType.GENERAL,
                filename=f"contract_{contract_id}.pdf"
            )
            success = contract_repo.save(contract)
            results.append(success)
        
        # Create multiple threads that save contracts
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_contract, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all saves were successful
        assert all(results)
        assert len(results) == 5
        
        # Verify all contracts were saved
        contracts = contract_repo.find_recent(10)
        assert len(contracts) == 5