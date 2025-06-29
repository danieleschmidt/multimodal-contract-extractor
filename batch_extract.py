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
)


from multimodal_contract_extractor import (  # noqa: E402
    __version__,
    DocumentInfo,
    ExtractionResult,
    serialize_to_json,
    serialize_to_xml,
    serialize_to_csv,
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
    setup_logging(args.log_level)
    logger.debug("Arguments: %s", args)

    if args.output_format not in SUPPORTED_FORMATS:
        logger.error("Unsupported format: %s", args.output_format)
        return 1

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        logger.error("Input directory not found: %s", input_dir)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Processing %s -> %s", input_dir, output_dir)

    for file_path in input_dir.iterdir():
        if not file_path.is_file():
            continue

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
        output_file = output_dir / f"{file_path.stem}.{args.output_format}"
        output_file.write_text(data)
        logger.info("Wrote %s", output_file)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
