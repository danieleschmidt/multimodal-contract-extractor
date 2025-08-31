# Repository Context

## Structure:
./.terragon/generate-backlog.py
./.terragon/value-discovery.py
./API.md
./ARCHITECTURE.md
./AUTONOMOUS_BACKLOG.md
./AUTONOMOUS_SDLC_COMPLETION_REPORT_v4.md
./AUTONOMOUS_SDLC_ENHANCEMENT_COMPLETION_REPORT.md
./AUTONOMOUS_SDLC_EXECUTION_SUMMARY.md
./AUTONOMOUS_SDLC_EXECUTION_SUMMARY_v2.md
./autonomous_sdlc_progressive_orchestrator.py
./AUTONOMOUS_SDLC_PROGRESSIVE_QUALITY_GATES_DOCUMENTATION.md
./AUTONOMOUS_SDLC_V4_COMPLETION_REPORT.md
./AUTONOMOUS_SDLC_V4_FINAL_COMPLETION_REPORT.md
./AUTONOMOUS_SDLC_V4_PRODUCTION_DEPLOYMENT_GUIDE.md
./AUTONOMOUS_SDLC_V5_COMPLETION_REPORT.md
./AUTONOMOUS_SDLC_V5_DEPLOYMENT_GUIDE.md
./AUTONOMOUS_SDLC_V6_DEPLOYMENT_GUIDE.md
./BACKLOG.md
./basic_autonomous_validation.py
./basic_quality_tests.py

## README (if exists):
# Multimodal-Contract-Extractor

Vision-Language-Model pipeline that intelligently identifies and extracts clauses from scanned PDFs, handwritten contracts, and image-based documents, outputting structured JSON data.

## Features

- **Multimodal Processing**: Handles scanned PDFs, images, and handwritten documents
- **Clause Detection**: Advanced OCR + Vision-Language Models for precise clause identification
- **Structured Output**: Exports extracted data as JSON, XML, or CSV formats
- **Legal Template Recognition**: Pre-trained on common contract types (NDAs, employment, leases)
- **Batch Processing**: Handle multiple documents simultaneously
- **Confidence Scoring**: Quality assessment for each extracted clause
- **Human-in-the-Loop**: Review interface for verification and corrections

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Process a single contract
python extract.py --file contract.pdf --output extracted_data.json

# Batch process multiple files
python batch_extract.py --input-dir ./contracts --output-dir ./results

# Enable debug logging
python extract.py --file contract.pdf --log-level debug

# Start web interface for interactive processing
streamlit run web_app.py

# Check CLI version
python extract.py --version
python batch_extract.py --version
```

## Development

Create a virtual environment and install both runtime and development
dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```


## Main files:
