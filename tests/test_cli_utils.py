import argparse

from multimodal_contract_extractor import cli_utils


def test_add_common_arguments_defaults():
    parser = argparse.ArgumentParser()
    cli_utils.add_common_arguments(parser)
    args = parser.parse_args([])
    assert args.output_format == "json"
    assert args.include_coordinates is False
    assert args.log_level == "info"


def test_supported_formats_constant():
    assert "json" in cli_utils.SUPPORTED_FORMATS
    assert "xml" in cli_utils.SUPPORTED_FORMATS
    assert "csv" in cli_utils.SUPPORTED_FORMATS
