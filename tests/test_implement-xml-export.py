from xml.etree import ElementTree as ET

from multimodal_contract_extractor.serialization import (
    DocumentInfo,
    ExtractionResult,
    serialize_to_xml,
)
from multimodal_contract_extractor.clause_detection import Clause

INFO = DocumentInfo(filename="file.pdf", pages=1, processing_time=0.0, confidence=1.0)
CLAUSE = Clause(type="test", text="text", page=1)
RESULT = ExtractionResult(document_info=INFO, clauses=[CLAUSE])


def test_serialize_to_xml_returns_well_formed():
    xml_data = serialize_to_xml(RESULT)
    ET.fromstring(xml_data)


def test_root_contains_clauses():
    xml_data = serialize_to_xml(RESULT)
    root = ET.fromstring(xml_data)
    assert root.tag == "contract"
    assert root.find("clauses") is not None


SPECIAL_CLAUSE = Clause(type="special", text="5 > 3 & 2 < 4", page=1)
RESULT_SPECIAL = ExtractionResult(document_info=INFO, clauses=[SPECIAL_CLAUSE])


def test_handles_special_characters():
    xml_data = serialize_to_xml(RESULT_SPECIAL)
    root = ET.fromstring(xml_data)
    text = root.find("clauses").find("clause").find("text").text
    assert text == "5 > 3 & 2 < 4"
