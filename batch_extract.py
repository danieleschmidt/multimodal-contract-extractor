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
)
from multimodal_contract_extractor.cli_utils import (  # noqa: E402
    add_common_arguments,
    sanitize_filename,
    setup_logging,
)
from multimodal_contract_extractor.metrics import (  # noqa: E402
    PAGES_PROCESSED,
    PROCESSING_TIME,
    record_memory_usage,
    save_metrics,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch extract contract clauses")
    parser.add_argument("--input-dir", required=True, help="Directory of documents")
    parser.add_argument("--output-dir", required=True, help="Directory for results")
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

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        logger.error("Input directory not found: %s", input_dir)
        return 1

    output_dir = Path(args.output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        logger.error("Output directory is not a directory: %s", output_dir)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Processing %s -> %s", input_dir, output_dir)

    processed_files = 0
    skipped_files = 0

    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

        # Validate file with security checks
        try:
            validate_file_input(file_path)
        except SecurityError as exc:
            logger.warning("Skipping file %s: %s", file_path.name, exc)
            skipped_files += 1
            continue

        with PROCESSING_TIME.time():
            from multimodal_contract_extractor import extract_from_document

            extraction_result = extract_from_document(
                file_path,
                language_code=args.language,
                enable_advanced_classification=not args.disable_advanced_classification,
                enable_adaptive_processing=not args.disable_adaptive_processing
            )

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
            from multimodal_contract_extractor.serialization import (
                serialize_with_validation,
            )

            try:
                data, validation_error = serialize_with_validation(
                    result,
                    args.output_format,
                    pretty=True,
                    validate=True
                )

                if validation_error:
                    logger.warning("Validation warning for %s: %s", file_path.name, validation_error)

            except Exception as e:
                logger.error("Serialization failed for %s: %s", file_path.name, e)
                skipped_files += 1
                continue

            logger.info("Processed %s in %.2fs", file_path.name, info.processing_time)
            name = sanitize_filename(f"{file_path.stem}.{args.output_format}")
            output_file = output_dir / name
            output_file.write_text(data)
            logger.info("Wrote %s", output_file)
            PAGES_PROCESSED.inc(info.pages)
            processed_files += 1

    logger.info(
        "Batch processing complete: %d files processed, %d files skipped",
        processed_files,
        skipped_files,
    )
    record_memory_usage()
    if args.metrics_file:
        save_metrics(args.metrics_file)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
