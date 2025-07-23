"""Dataclasses and helpers for structured extraction output."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec B405

from defusedxml.minidom import parseString

if TYPE_CHECKING:
    from .clause_detection import Clause


@dataclass
class DocumentInfo:
    """Metadata about a processed document."""

    filename: str
    pages: int
    processing_time: float
    confidence: float


@dataclass
class ExtractionResult:
    """Structured result of clause extraction."""

    document_info: DocumentInfo
    clauses: list[Clause]


def serialize_to_json(result: ExtractionResult, *, pretty: bool = False) -> str:
    """Serialize an :class:`ExtractionResult` to a JSON string.

    Parameters
    ----------
    result:
        The extraction result to serialize.
    pretty:
        If ``True``, the JSON string is formatted with indentation.
    """

    result_dict = asdict(result)
    if pretty:
        return json.dumps(result_dict, indent=2)
    return json.dumps(result_dict)


def serialize_to_xml(result: ExtractionResult, *, pretty: bool = False) -> str:
    """Serialize an :class:`ExtractionResult` to an XML string.

    Parameters
    ----------
    result:
        The extraction result to serialize.
    pretty:
        If ``True``, the XML string is formatted with indentation.
    """

    root = Element("contract")

    info_el = SubElement(root, "document_info")
    for field, value in asdict(result.document_info).items():
        child = SubElement(info_el, field)
        child.text = str(value)

    clauses_el = SubElement(root, "clauses")
    for clause in result.clauses:
        clause_el = SubElement(clauses_el, "clause")
        SubElement(clause_el, "type").text = clause.type
        SubElement(clause_el, "text").text = clause.text
        SubElement(clause_el, "page").text = str(clause.page)

    xml_str = tostring(root, encoding="unicode")
    if pretty:
        xml_str = parseString(xml_str).toprettyxml(indent="  ")
    return xml_str


def serialize_to_csv(
    result: ExtractionResult,
    *,
    include_coordinates: bool = False,
) -> str:
    """Serialize an :class:`ExtractionResult` to a CSV string."""

    headers = ["type", "text", "page"]
    if include_coordinates:
        headers += ["x1", "y1", "x2", "y2"]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for clause in result.clauses:
        row = [clause.type, clause.text, clause.page]
        if include_coordinates:
            if clause.coordinates:
                row.extend(map(str, clause.coordinates))
            else:
                row.extend(["", "", "", ""])
        writer.writerow(row)

    return output.getvalue()
