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

from multimodal_contract_extractor import (  # noqa: E402
    DocumentInfo,
    ExtractionResult,
    SecurityError,
    __version__,
    validate_file_input,
    validate_output_path,
)
from multimodal_contract_extractor.cli_utils import (  # noqa: E402
    add_common_arguments,
    setup_logging,
)
from multimodal_contract_extractor.metrics import (  # noqa: E402
    PROCESSING_TIME,
    record_memory_usage,
    save_metrics,
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
        "--language",
        default=None,
        help="Document language code (e.g., en, es, fr, de, ja, zh). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--disable-advanced-classification",
        action="store_true",
        help="Disable advanced clause classification for specialized contract types",
    )
    parser.add_argument(
        "--disable-adaptive-processing",
        action="store_true",
        help="Disable adaptive processing pipeline for low-confidence extractions",
    )
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

    # Check if the requested format is supported
    try:
        from multimodal_contract_extractor.serialization import get_supported_formats
        supported_formats = get_supported_formats()
        if args.output_format not in supported_formats:
            logger.error("Unsupported format: %s. Supported formats: %s",
                        args.output_format, ', '.join(supported_formats))
            return 1
    except ImportError as e:
        logger.error("Failed to check format support: %s", e)
        return 1

    # Validate input file with security checks
    try:
        input_path = validate_file_input(Path(args.file))
        logger.info("Processing file %s", input_path)
    except SecurityError as exc:
        logger.exception("Security validation failed: %s", exc)
        return 1

    # Validate output path with security checks
    try:
        output_path = validate_output_path(args.output, args.output_format)
    except SecurityError as exc:
        logger.exception("Output validation failed: %s", exc)
        return 1

    with PROCESSING_TIME.time():
        from multimodal_contract_extractor import extract_from_document

        extraction_result = extract_from_document(
            input_path,
            language_code=args.language,
            enable_advanced_classification=not args.disable_advanced_classification,
            enable_adaptive_processing=not args.disable_adaptive_processing
        )

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
            coordinates=clause_data["coordinates"],
        )
        for clause_data in extraction_result["clauses"]
    ]

    result = ExtractionResult(document_info=info, clauses=clauses)

    # Use enhanced serialization with validation
    from multimodal_contract_extractor.serialization import serialize_with_validation

    try:
        data, validation_error = serialize_with_validation(
            result,
            args.output_format,
            pretty=True,
            validate=True
        )

        if validation_error:
            logger.warning("Validation warning: %s", validation_error)

    except Exception as e:
        logger.error("Serialization failed: %s", e)
        return 1

    output_path.write_text(data)
    logger.info("Wrote output to %s", output_path)
    record_memory_usage()
    if args.metrics_file:
        save_metrics(args.metrics_file, format=args.metrics_format)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
