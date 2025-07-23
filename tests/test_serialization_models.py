from dataclasses import fields, is_dataclass

from multimodal_contract_extractor.clause_detection import Clause
from multimodal_contract_extractor.serialization import DocumentInfo, ExtractionResult


def test_document_info_fields():
    assert is_dataclass(DocumentInfo)
    names = [f.name for f in fields(DocumentInfo)]
    assert names == ["filename", "pages", "processing_time", "confidence"]


def test_extraction_result_fields():
    assert is_dataclass(ExtractionResult)
    names = [f.name for f in fields(ExtractionResult)]
    assert names == ["document_info", "clauses"]


def test_extraction_result_contains_clause_list():
    clause = Clause(type="test", text="text", page=1)
    info = DocumentInfo(
        filename="file.pdf", pages=1, processing_time=0.0, confidence=1.0
    )
    result = ExtractionResult(document_info=info, clauses=[clause])
    assert result.document_info == info
    assert result.clauses == [clause]
