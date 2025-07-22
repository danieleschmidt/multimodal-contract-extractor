"""End-to-end integration tests for CLI tools with real document processing."""

import json
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.test_helpers import create_test_pdf


class TestExtractCLIEndToEnd:
    """Test complete extract.py workflows from file input to output generation."""

    def test_extract_cli_processes_real_pdf_to_json(self, tmp_path):
        """Test complete workflow: PDF input -> processing -> JSON output."""
        # Create test PDF with contract text
        input_pdf = tmp_path / "contract.pdf"
        output_json = tmp_path / "result.json"
        
        create_test_pdf(
            input_pdf, 
            "CONFIDENTIALITY AGREEMENT\n\n"
            "The employee agrees to maintain confidentiality of all proprietary information.\n"
            "This agreement may be terminated by either party with 30 days notice.\n"
            "Payment terms are net 30 days from invoice date."
        )
        
        # Run extract.py CLI
        result = subprocess.run([
            sys.executable, "extract.py",
            "--file", str(input_pdf),
            "--output", str(output_json)
        ], capture_output=True, text=True)
        
        # Verify CLI execution succeeded
        assert result.returncode == 0, f"CLI failed with: {result.stderr}"
        assert output_json.exists(), "Output JSON file was not created"
        
        # Verify JSON output structure and content
        with open(output_json) as f:
            data = json.load(f)
        
        assert "document_info" in data
        assert "clauses" in data
        
        # Verify document info
        doc_info = data["document_info"]
        assert doc_info["filename"] == "contract.pdf"
        assert doc_info["pages"] > 0
        assert doc_info["processing_time"] > 0
        
        # Should detect some clauses from our contract text
        clauses = data["clauses"]
        assert len(clauses) > 0, "Should have detected at least one clause"
        
        # Verify clause structure
        for clause in clauses:
            assert "id" in clause
            assert "type" in clause  
            assert "text" in clause
            assert "page" in clause
            assert "confidence" in clause
            assert clause["page"] > 0
            assert 0 <= clause["confidence"] <= 1

    def test_extract_cli_handles_multiple_output_formats(self, tmp_path):
        """Test CLI can generate different output formats from same input."""
        input_pdf = tmp_path / "contract.pdf"
        
        create_test_pdf(input_pdf, "Confidentiality clause: All information is confidential.")
        
        formats_to_test = ["json", "xml", "csv"]
        
        for fmt in formats_to_test:
            output_file = tmp_path / f"result.{fmt}"
            
            result = subprocess.run([
                sys.executable, "extract.py",
                "--file", str(input_pdf),
                "--output", str(output_file),
                "--format", fmt
            ], capture_output=True, text=True)
            
            assert result.returncode == 0, f"CLI failed for format {fmt}: {result.stderr}"
            assert output_file.exists(), f"Output file not created for format {fmt}"
            assert output_file.stat().st_size > 0, f"Empty output file for format {fmt}"

    def test_extract_cli_with_debug_logging(self, tmp_path):
        """Test CLI with debug logging produces detailed output."""
        input_pdf = tmp_path / "contract.pdf"
        output_json = tmp_path / "result.json"
        
        create_test_pdf(input_pdf, "Sample contract with termination clause.")
        
        result = subprocess.run([
            sys.executable, "extract.py",
            "--file", str(input_pdf),
            "--output", str(output_json),
            "--log-level", "debug"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        
        # Debug logging should produce detailed output
        stderr_output = result.stderr.lower()
        assert "debug" in stderr_output or "processing" in stderr_output

    def test_extract_cli_error_handling_invalid_file(self, tmp_path):
        """Test CLI properly handles invalid input files."""
        nonexistent_file = tmp_path / "does_not_exist.pdf"
        output_json = tmp_path / "result.json"
        
        result = subprocess.run([
            sys.executable, "extract.py", 
            "--file", str(nonexistent_file),
            "--output", str(output_json)
        ], capture_output=True, text=True)
        
        # Should exit with error code
        assert result.returncode != 0
        assert not output_json.exists(), "Should not create output for invalid input"

    def test_extract_cli_with_metrics_file(self, tmp_path):
        """Test CLI generates metrics file when requested.""" 
        input_pdf = tmp_path / "contract.pdf"
        output_json = tmp_path / "result.json"
        metrics_file = tmp_path / "metrics.json"
        
        create_test_pdf(input_pdf, "Contract with payment terms: Net 30 days.")
        
        result = subprocess.run([
            sys.executable, "extract.py",
            "--file", str(input_pdf), 
            "--output", str(output_json),
            "--metrics-file", str(metrics_file),
            "--metrics-format", "json"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output_json.exists()
        assert metrics_file.exists()
        
        # Verify metrics content
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        assert "processing_time" in metrics
        assert "document_size" in metrics
        assert "clauses_found" in metrics
        assert metrics["processing_time"] > 0


class TestBatchExtractCLIEndToEnd:
    """Test complete batch_extract.py workflows with real document processing."""

    def test_batch_extract_processes_multiple_files(self, tmp_path):
        """Test batch processing of multiple PDF files."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create multiple test PDFs
        contract_texts = [
            "NDA: Employee must maintain confidentiality of all trade secrets.",
            "Employment Agreement: Termination requires 2 weeks notice.",
            "Service Agreement: Payment terms are net 45 days."
        ]
        
        for i, text in enumerate(contract_texts):
            pdf_file = input_dir / f"contract_{i+1}.pdf"
            create_test_pdf(pdf_file, text)
        
        # Run batch extraction
        result = subprocess.run([
            sys.executable, "batch_extract.py",
            "--input-dir", str(input_dir),
            "--output-dir", str(output_dir)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Batch extraction failed: {result.stderr}"
        
        # Verify output files were created
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == 3, f"Expected 3 output files, got {len(output_files)}"
        
        # Verify each output file has valid content
        for output_file in output_files:
            with open(output_file) as f:
                data = json.load(f)
            
            assert "document_info" in data
            assert "clauses" in data
            assert data["document_info"]["pages"] > 0

    def test_batch_extract_handles_mixed_formats(self, tmp_path):
        """Test batch processing with mixed PDF and image files."""
        input_dir = tmp_path / "input" 
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create PDF
        pdf_file = input_dir / "contract.pdf"
        create_test_pdf(pdf_file, "Confidentiality: All information is proprietary.")
        
        # Create a simple PNG (we'll simulate this since creating real images is complex)
        png_file = input_dir / "contract.png"
        # For testing, we'll create a minimal valid PNG
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00'
            b'\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        png_file.write_bytes(png_data)
        
        # Run batch processing
        result = subprocess.run([
            sys.executable, "batch_extract.py",
            "--input-dir", str(input_dir),
            "--output-dir", str(output_dir)
        ], capture_output=True, text=True)
        
        # Should process PDF successfully, may skip PNG if OCR can't handle it
        assert result.returncode == 0
        
        # At minimum should have processed the PDF
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) >= 1

    def test_batch_extract_error_recovery(self, tmp_path):
        """Test batch processing continues after individual file failures."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output" 
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create valid PDF
        valid_pdf = input_dir / "valid_contract.pdf"
        create_test_pdf(valid_pdf, "Valid contract with confidentiality clause.")
        
        # Create invalid/corrupted file  
        invalid_file = input_dir / "corrupted.pdf"
        invalid_file.write_text("This is not a valid PDF file")
        
        # Create another valid PDF
        valid_pdf2 = input_dir / "another_contract.pdf"
        create_test_pdf(valid_pdf2, "Another valid contract with termination terms.")
        
        # Run batch processing
        result = subprocess.run([
            sys.executable, "batch_extract.py",
            "--input-dir", str(input_dir),
            "--output-dir", str(output_dir)
        ], capture_output=True, text=True)
        
        # Should have some success despite failures
        # (may not be returncode 0 if there were errors, but should have processed valid files)
        
        # Verify valid files were processed
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) >= 1, "Should have processed at least one valid file"
        
        # Verify the valid outputs have proper structure
        for output_file in output_files:
            with open(output_file) as f:
                data = json.load(f)
            assert "document_info" in data
            assert "clauses" in data

    def test_batch_extract_empty_directory(self, tmp_path):
        """Test batch processing handles empty input directory gracefully."""
        input_dir = tmp_path / "empty_input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        result = subprocess.run([
            sys.executable, "batch_extract.py",
            "--input-dir", str(input_dir),
            "--output-dir", str(output_dir) 
        ], capture_output=True, text=True)
        
        # Should complete without error (though may have specific exit code)
        # Check that no output files were created
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == 0


class TestCLIConfigurationIntegration:
    """Test CLI tools with different configuration setups."""

    def test_extract_with_custom_config_file(self, tmp_path):
        """Test CLI extraction with custom configuration file."""
        input_pdf = tmp_path / "contract.pdf"
        output_json = tmp_path / "result.json"
        config_file = tmp_path / "config.yml"
        
        create_test_pdf(input_pdf, "Confidentiality and payment terms contract.")
        
        # Create custom config
        config_content = """
ocr:
  cache_size_limit: 50
  context_window_size: 200

extraction:
  base_confidence_score: 0.8
  length_bonus_divisor: 500

security:
  max_file_size_mb: 50
"""
        config_file.write_text(config_content)
        
        # Run with custom config
        with patch.dict('os.environ', {'MCE_CONFIG_PATH': str(config_file)}):
            result = subprocess.run([
                sys.executable, "extract.py",
                "--file", str(input_pdf),
                "--output", str(output_json)
            ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output_json.exists()
        
        # Verify extraction completed with custom settings
        with open(output_json) as f:
            data = json.load(f)
        
        assert "document_info" in data
        assert "clauses" in data

    def test_extract_with_environment_overrides(self, tmp_path):
        """Test CLI extraction with environment variable configuration."""
        input_pdf = tmp_path / "contract.pdf" 
        output_json = tmp_path / "result.json"
        
        create_test_pdf(input_pdf, "Contract with confidentiality and termination clauses.")
        
        # Set environment variables
        env_vars = {
            'MCE_EXTRACTION_BASE_CONFIDENCE_SCORE': '0.9',
            'MCE_OCR_CACHE_SIZE_LIMIT': '25',
            'MCE_SECURITY_MAX_FILE_SIZE_MB': '200'
        }
        
        with patch.dict('os.environ', env_vars):
            result = subprocess.run([
                sys.executable, "extract.py",
                "--file", str(input_pdf),
                "--output", str(output_json)
            ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output_json.exists()
        
        with open(output_json) as f:
            data = json.load(f)
        
        assert "document_info" in data
        assert "clauses" in data