"""Repository pattern implementations for data access."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..models.contract import Contract, ContractParty
from ..models.processing import ProcessingResult
from .connection import DatabaseConnection, get_db_connection

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository class with common database operations."""

    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize repository with database connection."""
        self.db = db_connection or get_db_connection()

    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string for database storage."""
        if data is None:
            return ""
        try:
            return json.dumps(data, default=str)  # default=str handles datetime objects
        except Exception as e:
            logger.warning(f"Failed to serialize data to JSON: {e}")
            return ""

    def _deserialize_json(self, json_str: str, default: Any = None) -> Any:
        """Deserialize JSON string from database."""
        if not json_str:
            return default or {}
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to deserialize JSON: {e}")
            return default or {}


class ContractRepository(BaseRepository):
    """Repository for managing contract data persistence."""

    def save(self, contract: Contract) -> bool:
        """
        Save a contract to the database.
        
        Args:
            contract: Contract instance to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Convert contract to database format
            contract_data = {
                'id': str(contract.id),
                'title': contract.title,
                'contract_type': contract.contract_type.value,
                'filename': contract.filename,
                'pages': contract.pages,
                'file_size_bytes': contract.file_size_bytes,
                'created_date': contract.created_date.isoformat() if contract.created_date else None,
                'effective_date': contract.effective_date.isoformat() if contract.effective_date else None,
                'expiration_date': contract.expiration_date.isoformat() if contract.expiration_date else None,
                'processed_at': contract.processed_at.isoformat(),
                'processing_time_seconds': contract.processing_time_seconds,
                'overall_confidence': contract.overall_confidence,
                'language': contract.language,
                'jurisdiction': contract.jurisdiction,
                'governing_law': contract.governing_law,
                'key_terms': self._serialize_json(contract.key_terms),
                'updated_at': datetime.utcnow().isoformat(),
            }

            # Save main contract record
            query = """
                INSERT OR REPLACE INTO contracts (
                    id, title, contract_type, filename, pages, file_size_bytes,
                    created_date, effective_date, expiration_date, processed_at,
                    processing_time_seconds, overall_confidence, language,
                    jurisdiction, governing_law, key_terms, updated_at
                ) VALUES (
                    :id, :title, :contract_type, :filename, :pages, :file_size_bytes,
                    :created_date, :effective_date, :expiration_date, :processed_at,
                    :processing_time_seconds, :overall_confidence, :language,
                    :jurisdiction, :governing_law, :key_terms, :updated_at
                )
            """

            self.db.execute_update(query, contract_data)

            # Save contract parties
            self._save_contract_parties(contract)

            # Save legal clauses
            self._save_legal_clauses(contract)

            logger.debug(f"Contract {contract.id} saved successfully")
            return True

        except Exception as e:
            logger.exception(f"Error saving contract {contract.id}: {str(e)}")
            return False

    def find_by_id(self, contract_id: UUID | str) -> Optional[Contract]:
        """
        Find a contract by its ID.
        
        Args:
            contract_id: Contract ID to search for
            
        Returns:
            Contract instance if found, None otherwise
        """
        try:
            query = "SELECT * FROM contracts WHERE id = :id"
            results = self.db.execute_query(query, {'id': str(contract_id)})

            if not results:
                return None

            contract_data = results[0]
            contract = self._build_contract_from_data(contract_data)

            # Load related data
            contract.parties = self._load_contract_parties(contract.id)
            contract.clauses = self._load_legal_clauses(contract.id)

            return contract

        except Exception as e:
            logger.exception(f"Error finding contract {contract_id}: {str(e)}")
            return None

    def find_by_filename(self, filename: str) -> List[Contract]:
        """
        Find contracts by filename.
        
        Args:
            filename: Filename to search for
            
        Returns:
            List of matching contracts
        """
        try:
            query = "SELECT * FROM contracts WHERE filename = :filename ORDER BY processed_at DESC"
            results = self.db.execute_query(query, {'filename': filename})

            contracts = []
            for contract_data in results:
                contract = self._build_contract_from_data(contract_data)
                contracts.append(contract)

            return contracts

        except Exception as e:
            logger.exception(f"Error finding contracts by filename {filename}: {str(e)}")
            return []

    def find_by_type(self, contract_type: str) -> List[Contract]:
        """
        Find contracts by type.
        
        Args:
            contract_type: Contract type to search for
            
        Returns:
            List of matching contracts
        """
        try:
            query = "SELECT * FROM contracts WHERE contract_type = :type ORDER BY processed_at DESC"
            results = self.db.execute_query(query, {'type': contract_type})

            contracts = []
            for contract_data in results:
                contract = self._build_contract_from_data(contract_data)
                contracts.append(contract)

            return contracts

        except Exception as e:
            logger.exception(f"Error finding contracts by type {contract_type}: {str(e)}")
            return []

    def find_recent(self, limit: int = 10) -> List[Contract]:
        """
        Find recently processed contracts.
        
        Args:
            limit: Maximum number of contracts to return
            
        Returns:
            List of recent contracts
        """
        try:
            query = "SELECT * FROM contracts ORDER BY processed_at DESC LIMIT :limit"
            results = self.db.execute_query(query, {'limit': limit})

            contracts = []
            for contract_data in results:
                contract = self._build_contract_from_data(contract_data)
                contracts.append(contract)

            return contracts

        except Exception as e:
            logger.exception(f"Error finding recent contracts: {str(e)}")
            return []

    def delete(self, contract_id: UUID | str) -> bool:
        """
        Delete a contract and all related data.
        
        Args:
            contract_id: Contract ID to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            query = "DELETE FROM contracts WHERE id = :id"
            rows_affected = self.db.execute_update(query, {'id': str(contract_id)})

            if rows_affected > 0:
                logger.debug(f"Contract {contract_id} deleted successfully")
                return True
            else:
                logger.warning(f"Contract {contract_id} not found for deletion")
                return False

        except Exception as e:
            logger.exception(f"Error deleting contract {contract_id}: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get contract statistics from the database.
        
        Returns:
            Dictionary with contract statistics
        """
        try:
            stats = {}

            # Total contracts
            result = self.db.execute_query("SELECT COUNT(*) as count FROM contracts")
            stats['total_contracts'] = result[0]['count']

            # Contracts by type
            query = "SELECT contract_type, COUNT(*) as count FROM contracts GROUP BY contract_type"
            results = self.db.execute_query(query)
            stats['by_type'] = {row['contract_type']: row['count'] for row in results}

            # Processing statistics
            query = """
                SELECT 
                    AVG(processing_time_seconds) as avg_processing_time,
                    MIN(processing_time_seconds) as min_processing_time,
                    MAX(processing_time_seconds) as max_processing_time,
                    AVG(overall_confidence) as avg_confidence
                FROM contracts 
                WHERE processing_time_seconds > 0
            """
            results = self.db.execute_query(query)
            if results:
                stats['processing'] = results[0]

            # Recent activity
            query = """
                SELECT DATE(processed_at) as date, COUNT(*) as count 
                FROM contracts 
                WHERE processed_at >= datetime('now', '-30 days')
                GROUP BY DATE(processed_at)
                ORDER BY date DESC
            """
            results = self.db.execute_query(query)
            stats['recent_activity'] = results

            return stats

        except Exception as e:
            logger.exception(f"Error getting contract statistics: {str(e)}")
            return {}

    def _build_contract_from_data(self, data: Dict[str, Any]) -> Contract:
        """Build a Contract instance from database data."""
        from ..models.contract import ContractType

        return Contract(
            id=UUID(data['id']),
            title=data.get('title'),
            contract_type=ContractType(data['contract_type']),
            filename=data.get('filename'),
            pages=data.get('pages', 0),
            file_size_bytes=data.get('file_size_bytes'),
            created_date=datetime.fromisoformat(data['created_date']) if data.get('created_date') else None,
            effective_date=datetime.fromisoformat(data['effective_date']) if data.get('effective_date') else None,
            expiration_date=datetime.fromisoformat(data['expiration_date']) if data.get('expiration_date') else None,
            processed_at=datetime.fromisoformat(data['processed_at']),
            processing_time_seconds=data.get('processing_time_seconds', 0.0),
            overall_confidence=data.get('overall_confidence', 0.0),
            language=data.get('language', 'en'),
            jurisdiction=data.get('jurisdiction'),
            governing_law=data.get('governing_law'),
            key_terms=self._deserialize_json(data.get('key_terms', '')),
        )

    def _save_contract_parties(self, contract: Contract) -> None:
        """Save contract parties to database."""
        # Delete existing parties
        delete_query = "DELETE FROM contract_parties WHERE contract_id = :contract_id"
        self.db.execute_update(delete_query, {'contract_id': str(contract.id)})

        # Insert new parties
        for party in contract.parties:
            party_data = {
                'contract_id': str(contract.id),
                'name': party.name,
                'role': party.role,
                'address': party.address,
                'email': party.email,
                'phone': party.phone,
                'entity_type': party.entity_type,
            }

            insert_query = """
                INSERT INTO contract_parties (
                    contract_id, name, role, address, email, phone, entity_type
                ) VALUES (
                    :contract_id, :name, :role, :address, :email, :phone, :entity_type
                )
            """

            self.db.execute_update(insert_query, party_data)

    def _load_contract_parties(self, contract_id: UUID) -> List[ContractParty]:
        """Load contract parties from database."""
        query = "SELECT * FROM contract_parties WHERE contract_id = :contract_id"
        results = self.db.execute_query(query, {'contract_id': str(contract_id)})

        parties = []
        for party_data in results:
            party = ContractParty(
                name=party_data['name'],
                role=party_data['role'],
                address=party_data.get('address'),
                email=party_data.get('email'),
                phone=party_data.get('phone'),
                entity_type=party_data.get('entity_type'),
            )
            parties.append(party)

        return parties

    def _save_legal_clauses(self, contract: Contract) -> None:
        """Save legal clauses to database."""
        # Delete existing clauses
        delete_query = "DELETE FROM legal_clauses WHERE contract_id = :contract_id"
        self.db.execute_update(delete_query, {'contract_id': str(contract.id)})

        # Insert new clauses
        for clause in contract.clauses:
            if hasattr(clause, 'to_dict'):
                clause_data = {
                    'id': str(clause.id) if hasattr(clause, 'id') else None,
                    'contract_id': str(contract.id),
                    'type': clause.type.value if hasattr(clause, 'type') else 'unknown',
                    'title': getattr(clause, 'title', None),
                    'text': getattr(clause, 'text', str(clause)),
                    'page': getattr(clause, 'page', 1),
                    'coordinates': self._serialize_json(getattr(clause, 'coordinates', [])),
                    'confidence': getattr(clause, 'confidence', 0.0),
                    'key_terms': self._serialize_json(getattr(clause, 'key_terms', [])),
                    'entities': self._serialize_json(getattr(clause, 'entities', {})),
                    'obligations': self._serialize_json(getattr(clause, 'obligations', [])),
                    'conditions': self._serialize_json(getattr(clause, 'conditions', [])),
                    'dates': self._serialize_json([d.isoformat() for d in getattr(clause, 'dates', [])]),
                    'amounts': self._serialize_json(getattr(clause, 'amounts', [])),
                    'section_number': getattr(clause, 'section_number', None),
                    'parent_section': getattr(clause, 'parent_section', None),
                    'is_mandatory': getattr(clause, 'is_mandatory', True),
                    'risk_level': getattr(clause, 'risk_level', 'medium'),
                }

                insert_query = """
                    INSERT INTO legal_clauses (
                        id, contract_id, type, title, text, page, coordinates,
                        confidence, key_terms, entities, obligations, conditions,
                        dates, amounts, section_number, parent_section,
                        is_mandatory, risk_level
                    ) VALUES (
                        :id, :contract_id, :type, :title, :text, :page, :coordinates,
                        :confidence, :key_terms, :entities, :obligations, :conditions,
                        :dates, :amounts, :section_number, :parent_section,
                        :is_mandatory, :risk_level
                    )
                """

                self.db.execute_update(insert_query, clause_data)

    def _load_legal_clauses(self, contract_id: UUID) -> List[Any]:
        """Load legal clauses from database."""
        query = "SELECT * FROM legal_clauses WHERE contract_id = :contract_id ORDER BY page, id"
        results = self.db.execute_query(query, {'contract_id': str(contract_id)})

        clauses = []
        for clause_data in results:
            # Convert back to LegalClause object
            from ..models.clause import ClauseType, LegalClause

            dates = []
            date_strings = self._deserialize_json(clause_data.get('dates', ''), [])
            for date_str in date_strings:
                try:
                    dates.append(datetime.fromisoformat(date_str))
                except ValueError:
                    pass

            clause = LegalClause(
                id=UUID(clause_data['id']) if clause_data['id'] else None,
                type=ClauseType(clause_data['type']),
                title=clause_data.get('title'),
                text=clause_data['text'],
                page=clause_data['page'],
                coordinates=self._deserialize_json(clause_data.get('coordinates', ''), []),
                confidence=clause_data['confidence'],
                key_terms=self._deserialize_json(clause_data.get('key_terms', ''), []),
                entities=self._deserialize_json(clause_data.get('entities', ''), {}),
                obligations=self._deserialize_json(clause_data.get('obligations', ''), []),
                conditions=self._deserialize_json(clause_data.get('conditions', ''), []),
                dates=dates,
                amounts=self._deserialize_json(clause_data.get('amounts', ''), []),
                section_number=clause_data.get('section_number'),
                parent_section=clause_data.get('parent_section'),
                is_mandatory=bool(clause_data.get('is_mandatory', True)),
                risk_level=clause_data.get('risk_level', 'medium'),
            )

            clauses.append(clause)

        return clauses


class ProcessingResultRepository(BaseRepository):
    """Repository for managing processing result data."""

    def save(self, result: ProcessingResult) -> bool:
        """
        Save a processing result to the database.
        
        Args:
            result: ProcessingResult instance to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            result_data = {
                'id': str(result.id),
                'document_path': result.document_path,
                'status': result.status.value,
                'started_at': result.started_at.isoformat(),
                'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                'current_stage': result.current_stage.value,
                'validation_result': self._serialize_json(result.validation.to_dict() if result.validation else None),
                'metrics': self._serialize_json(result.metrics.to_dict()),
                'extracted_data': self._serialize_json(result.extracted_data),
                'errors': self._serialize_json([error.to_dict() for error in result.errors]),
                'processing_config': self._serialize_json(result.processing_config),
                'updated_at': datetime.utcnow().isoformat(),
            }

            query = """
                INSERT OR REPLACE INTO processing_results (
                    id, document_path, status, started_at, completed_at,
                    current_stage, validation_result, metrics, extracted_data,
                    errors, processing_config, updated_at
                ) VALUES (
                    :id, :document_path, :status, :started_at, :completed_at,
                    :current_stage, :validation_result, :metrics, :extracted_data,
                    :errors, :processing_config, :updated_at
                )
            """

            self.db.execute_update(query, result_data)
            logger.debug(f"Processing result {result.id} saved successfully")
            return True

        except Exception as e:
            logger.exception(f"Error saving processing result {result.id}: {str(e)}")
            return False

    def find_by_id(self, result_id: UUID | str) -> Optional[ProcessingResult]:
        """
        Find a processing result by its ID.
        
        Args:
            result_id: Processing result ID to search for
            
        Returns:
            ProcessingResult instance if found, None otherwise
        """
        try:
            query = "SELECT * FROM processing_results WHERE id = :id"
            results = self.db.execute_query(query, {'id': str(result_id)})

            if not results:
                return None

            return self._build_result_from_data(results[0])

        except Exception as e:
            logger.exception(f"Error finding processing result {result_id}: {str(e)}")
            return None

    def find_by_status(self, status: str) -> List[ProcessingResult]:
        """
        Find processing results by status.
        
        Args:
            status: Processing status to search for
            
        Returns:
            List of matching processing results
        """
        try:
            query = "SELECT * FROM processing_results WHERE status = :status ORDER BY started_at DESC"
            results = self.db.execute_query(query, {'status': status})

            return [self._build_result_from_data(data) for data in results]

        except Exception as e:
            logger.exception(f"Error finding processing results by status {status}: {str(e)}")
            return []

    def _build_result_from_data(self, data: Dict[str, Any]) -> ProcessingResult:
        """Build a ProcessingResult instance from database data."""
        from ..models.processing import (
            ProcessingMetrics,
            ProcessingStage,
            ProcessingStatus,
            ValidationResult,
        )

        # Build validation result
        validation = None
        if data.get('validation_result'):
            validation_data = self._deserialize_json(data['validation_result'])
            validation = ValidationResult(**validation_data)

        # Build metrics
        metrics_data = self._deserialize_json(data.get('metrics', ''), {})
        metrics = ProcessingMetrics()
        for key, value in metrics_data.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)

        return ProcessingResult(
            id=UUID(data['id']),
            document_path=data.get('document_path'),
            status=ProcessingStatus(data['status']),
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            validation=validation,
            metrics=metrics,
            extracted_data=self._deserialize_json(data.get('extracted_data', ''), {}),
            current_stage=ProcessingStage(data['current_stage']),
            processing_config=self._deserialize_json(data.get('processing_config', ''), {}),
        )
