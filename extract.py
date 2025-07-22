from __future__ import annotations

import argparse
import logging
import sys
import uuid
from pathlib import Path

# Ensure the src directory is importable when running the CLI without
# installing the package first.
SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

logger = logging.getLogger(__name__)

from multimodal_contract_extractor.cli_utils import (  # noqa: E402
    SUPPORTED_FORMATS,
    add_common_arguments,
    setup_logging,
)
from multimodal_contract_extractor.metrics import (  # noqa: E402
    PROCESSING_TIME,
    record_memory_usage,
    save_metrics,
)



from multimodal_contract_extractor import (  # noqa: E402
    __version__,
    DocumentInfo,
    ExtractionResult,
    serialize_to_json,
    serialize_to_xml,
    serialize_to_csv,
    SecurityError,
    validate_file_input,
    validate_output_path,
)

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract contract clauses")
    parser.add_argument("--file", required=True, help="Path to input document")
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (without extension to use output format)",
    )
    add_common_arguments(parser)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    request_id = uuid.uuid4().hex
    setup_logging(args.log_level, json_logs=args.json_logs, request_id=request_id)
    logger.debug("Arguments: %s", args)

    if args.output_format not in SUPPORTED_FORMATS:
        logger.error("Unsupported format: %s", args.output_format)
        return 1

    # Validate input file with security checks
    try:
        input_path = validate_file_input(Path(args.file))
        logger.info("Processing file %s", input_path)
    except SecurityError as exc:
        logger.error("Security validation failed: %s", exc)
        return 1

    # Validate output path with security checks
    try:
        output_path = validate_output_path(args.output, args.output_format)
    except SecurityError as exc:
        logger.error("Output validation failed: %s", exc)
        return 1

    with PROCESSING_TIME.time():
        from multimodal_contract_extractor import extract_from_document
        extraction_result = extract_from_document(input_path)
        
    processing_time = extraction_result["document_info"]["processing_time"]
    logger.info("Processing completed in %.2fs", processing_time)
    
    # Convert to legacy format for serialization compatibility
    info = DocumentInfo(
        filename=extraction_result["document_info"]["filename"],
        pages=extraction_result["document_info"]["pages"],
        processing_time=extraction_result["document_info"]["processing_time"],
        confidence=extraction_result["document_info"]["overall_confidence"],
    )
    
    # Convert clauses to Clause objects
    from multimodal_contract_extractor.clause_detection import Clause
    clauses = [
        Clause(
            type=clause_data["type"],
            text=clause_data["text"],
            page=clause_data["page"],
            coordinates=clause_data["coordinates"]
        )
        for clause_data in extraction_result["clauses"]
    ]
    
    result = ExtractionResult(document_info=info, clauses=clauses)

    if args.output_format == "json":
        data = serialize_to_json(result, pretty=True)
    elif args.output_format == "xml":
        data = serialize_to_xml(result, pretty=True)
    else:  # csv
        data = serialize_to_csv(result, include_coordinates=args.include_coordinates)

    output_path.write_text(data)
    logger.info("Wrote output to %s", output_path)
    record_memory_usage()
    if args.metrics_file:
        save_metrics(args.metrics_file, format=args.metrics_format)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
