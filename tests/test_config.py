"""Tests for centralized configuration management."""

import os
import tempfile
from unittest.mock import patch

import pytest

from multimodal_contract_extractor.config import (
    Config,
    ConfigValidationError,
    get_config,
    load_config,
    validate_config,
)


def reset_config_singleton():
    """Reset the configuration singleton for test isolation."""
    import multimodal_contract_extractor.config as config_module

    config_module._config_instance = None


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_config_values(self):
        """Test that default configuration contains expected values."""
        config = Config()

        # OCR Configuration
        assert config.ocr.cache_size_limit == 100
        assert config.ocr.context_window_size == 100

        # Extraction Configuration
        assert config.extraction.base_confidence_score == 0.75
        assert config.extraction.length_bonus_divisor == 1000
        assert config.extraction.max_confidence_cap == 0.95
        assert config.extraction.file_size_threshold_mb == 10
        assert config.extraction.streaming_chunk_size == 5

        # Security Configuration
        assert config.security.max_file_size_mb == 100
        assert config.security.request_id_length_limit == 64

        # Health Check Configuration
        assert config.health.check_timeout_seconds == 5

        # Document Processing Configuration
        assert config.document.default_streaming_chunk_size == 10


class TestConfigLoading:
    """Test configuration loading from various sources."""

    def setup_method(self):
        """Reset config singleton before each test."""
        reset_config_singleton()

    def teardown_method(self):
        """Reset config singleton after each test."""
        reset_config_singleton()

    def test_load_config_from_environment(self):
        """Test loading configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "MCE_OCR_CACHE_SIZE_LIMIT": "200",
                "MCE_EXTRACTION_BASE_CONFIDENCE_SCORE": "0.8",
                "MCE_SECURITY_MAX_FILE_SIZE_MB": "150",
            },
        ):
            config = load_config()
            assert config.ocr.cache_size_limit == 200
            assert config.extraction.base_confidence_score == 0.8
            assert config.security.max_file_size_mb == 150

    def test_load_config_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_content = """
ocr:
  cache_size_limit: 250
  context_window_size: 150

extraction:
  base_confidence_score: 0.85
  max_confidence_cap: 0.98

security:
  max_file_size_mb: 200
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = load_config(config_path=config_path)
            assert config.ocr.cache_size_limit == 250
            assert config.ocr.context_window_size == 150
            assert config.extraction.base_confidence_score == 0.85
            assert config.extraction.max_confidence_cap == 0.98
            assert config.security.max_file_size_mb == 200
        finally:
            os.unlink(config_path)

    def test_environment_overrides_file_config(self):
        """Test that environment variables override file configuration."""
        config_content = """
ocr:
  cache_size_limit: 250

extraction:
  base_confidence_score: 0.85
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "MCE_OCR_CACHE_SIZE_LIMIT": "300",  # Override file value
                },
            ):
                config = load_config(config_path=config_path)
                assert config.ocr.cache_size_limit == 300  # From env
                assert config.extraction.base_confidence_score == 0.85  # From file
        finally:
            os.unlink(config_path)


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config_passes_validation(self):
        """Test that a valid configuration passes validation."""
        config = Config()
        # Should not raise any exception
        validate_config(config)

    def test_invalid_confidence_score_raises_error(self):
        """Test that invalid confidence scores raise validation errors."""
        config = Config()
        config.extraction.base_confidence_score = 1.5  # Invalid: > 1.0

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "base_confidence_score must be between 0.0 and 1.0" in str(
            exc_info.value
        )

    def test_negative_cache_size_raises_error(self):
        """Test that negative cache sizes raise validation errors."""
        config = Config()
        config.ocr.cache_size_limit = -10  # Invalid: negative

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "cache_size_limit must be positive" in str(exc_info.value)

    def test_zero_file_size_threshold_raises_error(self):
        """Test that zero file size thresholds raise validation errors."""
        config = Config()
        config.extraction.file_size_threshold_mb = 0  # Invalid: zero

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(config)
        assert "file_size_threshold_mb must be positive" in str(exc_info.value)


class TestConfigSingleton:
    """Test configuration singleton pattern."""

    def setup_method(self):
        """Reset config singleton before each test."""
        reset_config_singleton()

    def teardown_method(self):
        """Reset config singleton after each test."""
        reset_config_singleton()

    def test_get_config_returns_same_instance(self):
        """Test that get_config() returns the same instance consistently."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_config_reload_updates_singleton(self):
        """Test that reloading configuration updates the singleton."""
        get_config()  # Initialize singleton

        # Reload with environment override
        with patch.dict(
            os.environ,
            {
                "MCE_OCR_CACHE_SIZE_LIMIT": "999",
            },
        ):
            new_config = load_config(reload=True)
            assert new_config.ocr.cache_size_limit == 999

            # Verify singleton was updated
            singleton_config = get_config()
            assert singleton_config.ocr.cache_size_limit == 999


class TestConfigIntegration:
    """Test configuration integration with existing modules."""

    def setup_method(self):
        """Reset config singleton before each test."""
        reset_config_singleton()

    def teardown_method(self):
        """Reset config singleton after each test."""
        reset_config_singleton()

    def test_config_can_replace_hardcoded_values(self):
        """Test that config values can replace hardcoded values in modules."""
        config = get_config()

        # These should match the values currently hardcoded in the modules
        assert config.ocr.cache_size_limit >= 1
        assert 0.0 < config.extraction.base_confidence_score <= 1.0
        assert config.security.max_file_size_mb > 0
        assert config.health.check_timeout_seconds > 0

    def test_config_yaml_schema_example(self):
        """Test that the example YAML schema loads correctly."""
        example_config = """
# Multimodal Contract Extractor Configuration
ocr:
  cache_size_limit: 100
  context_window_size: 100

extraction:
  base_confidence_score: 0.75
  length_bonus_divisor: 1000
  max_confidence_cap: 0.95
  file_size_threshold_mb: 10
  streaming_chunk_size: 5

security:
  max_file_size_mb: 100
  request_id_length_limit: 64

health:
  check_timeout_seconds: 5

document:
  default_streaming_chunk_size: 10
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(example_config)
            config_path = f.name

        try:
            config = load_config(config_path=config_path)
            validate_config(config)  # Should not raise

            # Verify all values loaded correctly
            assert config.ocr.cache_size_limit == 100
            assert config.extraction.base_confidence_score == 0.75
            assert config.security.max_file_size_mb == 100
            assert config.health.check_timeout_seconds == 5
            assert config.document.default_streaming_chunk_size == 10
        finally:
            os.unlink(config_path)
