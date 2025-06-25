import json

from multimodal_contract_extractor.serialization import serialize_to_json, DocumentInfo, ExtractionResult
from multimodal_contract_extractor.clause_detection import Clause

INFO = DocumentInfo(filename="file.pdf", pages=1, processing_time=0.0, confidence=1.0)
CLAUSE = Clause(type="test", text="some text", page=1)
RESULT = ExtractionResult(document_info=INFO, clauses=[CLAUSE])


def test_serialize_to_json_returns_valid_json():
    data = serialize_to_json(RESULT)
    parsed = json.loads(data)
    assert isinstance(parsed, dict)


def test_output_includes_required_keys():
    parsed = json.loads(serialize_to_json(RESULT))
    assert 'document_info' in parsed and 'clauses' in parsed


def test_pretty_print_indentation():
    pretty = serialize_to_json(RESULT, pretty=True)
    assert '\n' in pretty and pretty.count('\n') > 1
