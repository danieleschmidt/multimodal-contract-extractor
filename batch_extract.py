from __future__ import annotations

import argparse
import sys
from pathlib import Path
import logging
import time

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
    sanitize_filename,
)
from multimodal_contract_extractor.metrics import (
    PROCESSING_TIME,
    PAGES_PROCESSED,
    record_memory_usage,
    save_metrics,
)
import uuid


from multimodal_contract_extractor import (  # noqa: E402
    __version__,
    DocumentInfo,
    ExtractionResult,
    serialize_to_json,
    serialize_to_xml,
    serialize_to_csv,
    SecurityError,
    validate_file_input,
)



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch extract contract clauses")
    parser.add_argument("--input-dir", required=True, help="Directory of documents")
    parser.add_argument("--output-dir", required=True, help="Directory for results")
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
            start = time.perf_counter()
            info = DocumentInfo(
                filename=file_path.name,
                pages=0,
                processing_time=0.0,
                confidence=1.0,
            )
            result = ExtractionResult(document_info=info, clauses=[])

            if args.output_format == "json":
                data = serialize_to_json(result, pretty=True)
            elif args.output_format == "xml":
                data = serialize_to_xml(result, pretty=True)
            else:  # csv
                data = serialize_to_csv(result, include_coordinates=args.include_coordinates)

            processing_time = time.perf_counter() - start
            logger.info("Processed %s in %.2fs", file_path.name, processing_time)
            name = sanitize_filename(f"{file_path.stem}.{args.output_format}")
            output_file = output_dir / name
            output_file.write_text(data)
            logger.info("Wrote %s", output_file)
            PAGES_PROCESSED.inc(info.pages)
            processed_files += 1

    logger.info("Batch processing complete: %d files processed, %d files skipped", 
                processed_files, skipped_files)
    record_memory_usage()
    if args.metrics_file:
        save_metrics(args.metrics_file)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
