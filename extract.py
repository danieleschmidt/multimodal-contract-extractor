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
    build_output_path,
)
from multimodal_contract_extractor.metrics import (
    PROCESSING_TIME,
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

    input_path = Path(args.file)
    if not input_path.is_file():
        logger.error("Input file not found: %s", input_path)
        return 1

    logger.info("Processing file %s", input_path)

    try:
        output_path = build_output_path(args.output, args.output_format)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return 1

    with PROCESSING_TIME.time():
        start_time = time.perf_counter()
        # Placeholder for real extraction work
        processing_time = time.perf_counter() - start_time
    logger.info("Processing completed in %.2fs", processing_time)
    info = DocumentInfo(
        filename=input_path.name,
        pages=0,
        processing_time=processing_time,
        confidence=1.0,
    )
    result = ExtractionResult(document_info=info, clauses=[])

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
        save_metrics(args.metrics_file)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
