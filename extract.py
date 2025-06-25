from __future__ import annotations

import argparse
import sys
from pathlib import Path

from multimodal_contract_extractor import (
    DocumentInfo,
    ExtractionResult,
    serialize_to_json,
    serialize_to_xml,
    serialize_to_csv,
)


SUPPORTED_FORMATS = {"json", "xml", "csv"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract contract clauses")
    parser.add_argument("--file", required=True, help="Path to input document")
    parser.add_argument(
        "--output-format",
        default="json",
        help="Output format: json, xml, or csv",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (without extension to use output format)",
    )
    parser.add_argument(
        "--include-coordinates",
        action="store_true",
        help="Include coordinates in CSV output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.output_format not in SUPPORTED_FORMATS:
        print(f"Unsupported format: {args.output_format}", file=sys.stderr)
        return 1

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        if output_path.suffix == "":
            output_path = output_path.with_suffix(f".{args.output_format}")
    else:
        output_path = Path(f"result.{args.output_format}")

    info = DocumentInfo(
        filename=input_path.name,
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

    output_path.write_text(data)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
