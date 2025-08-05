"""Dataclasses and helpers for structured extraction output with enhanced format support."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional
from xml.etree.ElementTree import Element, SubElement, tostring  # nosec B405

from defusedxml.minidom import parseString

if TYPE_CHECKING:
    from .clause_detection import Clause

# Try to import optional dependencies
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tomli_w
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


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


# JSON Schema for validation
EXTRACTION_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "Contract Extraction Result",
    "description": "Schema for multimodal contract extraction results",
    "required": ["document_info", "clauses", "metadata"],
    "properties": {
        "document_info": {
            "type": "object",
            "required": ["filename", "pages", "processing_time", "overall_confidence", "document_type"],
            "properties": {
                "filename": {"type": "string"},
                "pages": {"type": "integer", "minimum": 1},
                "processing_time": {"type": "number", "minimum": 0},
                "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "document_type": {"type": "string"},
                "contract_type_scores": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            },
            "additionalProperties": False
        },
        "clauses": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "text", "page", "coordinates", "confidence"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "text": {"type": "string"},
                    "page": {"type": "integer", "minimum": 1},
                    "coordinates": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 0,
                        "maxItems": 4
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "key_terms": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "legal_significance": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    },
                    "contract_types": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "keywords_matched": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "context_indicators": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "advanced_confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "additionalProperties": False
            }
        },
        "metadata": {
            "type": "object",
            "required": ["extraction_timestamp", "model_version", "processing_method"],
            "properties": {
                "extraction_timestamp": {"type": "string", "format": "date-time"},
                "model_version": {"type": "string"},
                "processing_method": {"type": "string"},
                "features_enabled": {
                    "type": "object",
                    "properties": {
                        "multi_language_support": {"type": "boolean"},
                        "advanced_classification": {"type": "boolean"},
                        "adaptive_processing": {"type": "boolean"}
                    }
                },
                "adaptive_processing": {
                    "type": "object",
                    "properties": {
                        "strategy_used": {"type": "string"},
                        "improvement_achieved": {"type": "boolean"},
                        "total_attempts": {"type": "integer", "minimum": 1},
                        "consensus_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "processing_time": {"type": "number", "minimum": 0}
                    }
                }
            },
            "additionalProperties": True
        }
    },
    "additionalProperties": False
}


def serialize_to_yaml(result: ExtractionResult, *, pretty: bool = False) -> str:
    """Serialize an :class:`ExtractionResult` to a YAML string.
    
    Parameters
    ----------
    result:
        The extraction result to serialize.
    pretty:
        If ``True``, the YAML string is formatted with better readability.
        
    Returns
    -------
    str
        YAML representation of the extraction result.
        
    Raises
    ------
    ImportError
        If PyYAML is not installed.
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is required for YAML serialization. Install with: pip install PyYAML")

    result_dict = asdict(result)

    # Configure YAML output
    yaml_kwargs = {
        'default_flow_style': False,
        'allow_unicode': True,
        'sort_keys': False
    }

    if pretty:
        yaml_kwargs.update({
            'indent': 2,
            'width': 120,
        })

    return yaml.dump(result_dict, **yaml_kwargs)


def serialize_to_toml(result: ExtractionResult) -> str:
    """Serialize an :class:`ExtractionResult` to a TOML string.
    
    Parameters
    ----------
    result:
        The extraction result to serialize.
        
    Returns
    -------
    str
        TOML representation of the extraction result.
        
    Raises
    ------
    ImportError
        If tomli-w is not installed.
    """
    if not TOML_AVAILABLE:
        raise ImportError("tomli-w is required for TOML serialization. Install with: pip install tomli-w")

    result_dict = asdict(result)

    # TOML has some limitations, so we need to flatten nested structures
    flattened = _flatten_for_toml(result_dict)

    return tomli_w.dumps(flattened)


def validate_extraction_result(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate extraction result against the JSON schema.
    
    Parameters
    ----------
    data:
        The data to validate.
        
    Returns
    -------
    tuple[bool, Optional[str]]
        A tuple of (is_valid, error_message). If valid, error_message is None.
    """
    if not JSONSCHEMA_AVAILABLE:
        return True, "Schema validation skipped (jsonschema not available)"

    try:
        jsonschema.validate(data, EXTRACTION_RESULT_SCHEMA)
        return True, None
    except jsonschema.ValidationError as e:
        return False, f"Validation error: {e.message} at path: {'.'.join(str(p) for p in e.absolute_path)}"
    except jsonschema.SchemaError as e:
        return False, f"Schema error: {e.message}"


def serialize_with_validation(result: ExtractionResult, format: str, *,
                            pretty: bool = False, validate: bool = True) -> tuple[str, Optional[str]]:
    """Serialize extraction result with optional validation.
    
    Parameters
    ----------
    result:
        The extraction result to serialize.
    format:
        Output format: 'json', 'yaml', 'toml', 'xml', 'csv'.
    pretty:
        Whether to format output for readability (where applicable).
    validate:
        Whether to validate the data before serialization.
        
    Returns
    -------
    tuple[str, Optional[str]]
        A tuple of (serialized_data, validation_error). If validation passes,
        validation_error is None.
    """
    result_dict = asdict(result)

    # Validate if requested
    validation_error = None
    if validate:
        is_valid, error_msg = validate_extraction_result(result_dict)
        if not is_valid:
            validation_error = error_msg

    # Serialize based on format
    format_lower = format.lower()

    if format_lower == 'json':
        serialized = serialize_to_json(result, pretty=pretty)
    elif format_lower == 'yaml':
        serialized = serialize_to_yaml(result, pretty=pretty)
    elif format_lower == 'toml':
        serialized = serialize_to_toml(result)
    elif format_lower == 'xml':
        serialized = serialize_to_xml(result, pretty=pretty)
    elif format_lower == 'csv':
        serialized = serialize_to_csv(result, include_coordinates=True)
    else:
        raise ValueError(f"Unsupported format: {format}. Supported formats: json, yaml, toml, xml, csv")

    return serialized, validation_error


def _flatten_for_toml(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten nested dictionaries for TOML serialization.
    
    TOML has limitations with deeply nested structures, so we flatten them
    using dot notation for keys.
    """
    flattened = {}

    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict) and not _is_simple_dict(value):
            # Recursively flatten nested dictionaries
            flattened.update(_flatten_for_toml(value, full_key))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Handle list of dictionaries (like clauses)
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    item_prefix = f"{full_key}.{i}"
                    flattened.update(_flatten_for_toml(item, item_prefix))
                else:
                    flattened[f"{full_key}.{i}"] = item
        else:
            flattened[full_key] = value

    return flattened


def _is_simple_dict(d: Dict[str, Any]) -> bool:
    """Check if a dictionary contains only simple values (no nested dicts/lists)."""
    return all(not isinstance(v, (dict, list)) or (isinstance(v, list) and all(not isinstance(item, dict) for item in v)) for v in d.values())


def get_supported_formats() -> list[str]:
    """Get list of supported serialization formats.
    
    Returns
    -------
    list[str]
        List of supported format names.
    """
    formats = ['json', 'xml', 'csv']

    if YAML_AVAILABLE:
        formats.append('yaml')
    if TOML_AVAILABLE:
        formats.append('toml')

    return formats


def get_format_info() -> Dict[str, Dict[str, Any]]:
    """Get information about available serialization formats.
    
    Returns
    -------
    Dict[str, Dict[str, Any]]
        Information about each format including availability and features.
    """
    return {
        'json': {
            'available': True,
            'description': 'JavaScript Object Notation - widely supported structured data format',
            'features': ['pretty_printing', 'validation', 'nested_structures'],
            'file_extension': '.json'
        },
        'yaml': {
            'available': YAML_AVAILABLE,
            'description': 'YAML Ain\'t Markup Language - human-readable data serialization',
            'features': ['pretty_printing', 'human_readable', 'comments'],
            'file_extension': '.yaml',
            'requirements': ['PyYAML']
        },
        'toml': {
            'available': TOML_AVAILABLE,
            'description': 'Tom\'s Obvious, Minimal Language - configuration file format',
            'features': ['human_readable', 'strongly_typed'],
            'file_extension': '.toml',
            'requirements': ['tomli-w'],
            'limitations': ['flattened_structure']
        },
        'xml': {
            'available': True,
            'description': 'eXtensible Markup Language - structured markup format',
            'features': ['pretty_printing', 'hierarchical', 'widely_supported'],
            'file_extension': '.xml'
        },
        'csv': {
            'available': True,
            'description': 'Comma-Separated Values - tabular data format',
            'features': ['compact', 'spreadsheet_compatible'],
            'file_extension': '.csv',
            'limitations': ['flat_structure_only']
        }
    }


def export_to_file(result: ExtractionResult, file_path: str, format: str = None, *,
                  pretty: bool = True, validate: bool = True) -> tuple[bool, Optional[str]]:
    """Export extraction result to a file.
    
    Parameters
    ----------
    result:
        The extraction result to export.
    file_path:
        Path to the output file.
    format:
        Output format. If None, inferred from file extension.
    pretty:
        Whether to format output for readability.
    validate:
        Whether to validate before export.
        
    Returns
    -------
    tuple[bool, Optional[str]]
        A tuple of (success, error_message).
    """
    from pathlib import Path

    path = Path(file_path)

    # Infer format from extension if not provided
    if format is None:
        extension = path.suffix.lower()
        format_map = {'.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
                     '.toml': 'toml', '.xml': 'xml', '.csv': 'csv'}
        format = format_map.get(extension, 'json')

    try:
        # Serialize with validation
        serialized_data, validation_error = serialize_with_validation(
            result, format, pretty=pretty, validate=validate
        )

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(serialized_data)

        return True, validation_error

    except Exception as e:
        return False, str(e)
