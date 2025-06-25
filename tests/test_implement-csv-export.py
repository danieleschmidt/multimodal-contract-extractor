
from multimodal_contract_extractor.serialization import serialize_to_csv, DocumentInfo, ExtractionResult
from multimodal_contract_extractor.clause_detection import Clause

def _sample_result():
    info = DocumentInfo(filename="file.pdf", pages=2, processing_time=0.0, confidence=1.0)
    clauses = [Clause(type="a", text="t1", page=1), Clause(type="b", text="t2", page=2)]
    return ExtractionResult(document_info=info, clauses=clauses)

def test_csv_has_header_row():
    csv_data = serialize_to_csv(_sample_result())
    header = csv_data.splitlines()[0]
    assert 'type' in header and 'text' in header and 'page' in header

def test_one_line_per_clause():
    csv_data = serialize_to_csv(_sample_result())
    lines = csv_data.strip().splitlines()
    assert len(lines) == 3

def test_coordinates_included_when_configured():
    info = DocumentInfo(filename="file.pdf", pages=1, processing_time=0.0, confidence=1.0)
    clause = Clause(type='c', text='t3', page=1, coordinates=(0,0,10,10))
    result = ExtractionResult(document_info=info, clauses=[clause])
    csv_data = serialize_to_csv(result, include_coordinates=True)
    header = csv_data.splitlines()[0]
    assert 'x1' in header and 'y1' in header and 'x2' in header and 'y2' in header
    values = csv_data.splitlines()[1].split(',')
    assert values[-4:] == ['0', '0', '10', '10']
