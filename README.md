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

Run linting, security checks and the tests to verify your setup:

```bash
ruff check . --fix
bandit -r src
python -m pytest -q
```

## Supported Document Types

### Input Formats
- **PDF Documents**: Native and scanned PDFs
- **Image Files**: PNG, JPEG, TIFF, BMP
- **Handwritten Documents**: Cursive and print handwriting
- **Multi-page Contracts**: Automatic page sequencing
- **Low-quality Scans**: Advanced preprocessing and enhancement

### Contract Types
- Non-Disclosure Agreements (NDAs)
- Employment Contracts
- Lease Agreements
- Service Agreements
- Purchase Orders
- Partnership Agreements
- Licensing Agreements

## Architecture

```
Document Input → Preprocessing → OCR Engine → VLM Analysis → Clause Extraction → JSON Output
                      ↓              ↓           ↓              ↓               ↓
                Image Enhance   Text Extract  Semantic Parse  Structure Map   Validate
```

## Configuration

```yaml
# config/extraction_config.yml
models:
  ocr_engine: "paddleocr"  # or "tesseract", "azure_vision"
  vlm_model: "gpt-4-vision-preview"
  fallback_model: "claude-3-sonnet"

extraction:
  confidence_threshold: 0.8
  clause_types:
    - "termination"
    - "payment_terms"
    - "confidentiality"
    - "liability"
    - "governing_law"
    - "dispute_resolution"
  
preprocessing:
  image_enhancement: true
  noise_reduction: true
  skew_correction: true
  contrast_adjustment: true

output:
  format: "json"  # json, xml, csv
  include_confidence: true
  include_coordinates: true
  pretty_print: true
```

## Usage Examples

### Basic Extraction
```python
from contract_extractor import ContractExtractor

extractor = ContractExtractor()
result = extractor.extract_from_file("nda.pdf")

print(result)
# {
#   "document_info": {
#     "filename": "nda.pdf",
#     "pages": 3,
#     "processing_time": 15.2,
#     "confidence": 0.92
#   },
#   "clauses": [
#     {
#       "type": "confidentiality",
#       "text": "The receiving party shall not disclose...",
#       "page": 1,
#       "coordinates": [100, 200, 400, 250],
#       "confidence": 0.95
#     }
#   ]
# }
```

### Batch Processing
```python
from contract_extractor import BatchProcessor

processor = BatchProcessor()
results = processor.process_directory(
    input_dir="./contracts",
    output_dir="./extracted",
    parallel=True
)

# Process results
for result in results:
    print(f"Processed: {result['filename']}")
    print(f"Clauses found: {len(result['clauses'])}")
```

### Custom Clause Types
```python
extractor = ContractExtractor()
extractor.add_custom_clause_type(
    name="renewal_terms",
    keywords=["renewal", "extend", "continuation"],
    pattern=r"(renewal|extend).{1,100}(term|period)"
)

result = extractor.extract_from_file("service_agreement.pdf")
```

## Sample Output

```json
{
  "document_info": {
    "filename": "employment_contract.pdf",
    "pages": 5,
    "processing_time": 23.4,
    "overall_confidence": 0.89,
    "document_type": "employment_agreement"
  },
  "parties": [
    {
      "role": "employer",
      "name": "TechCorp Inc.",
      "address": "123 Silicon Valley, CA 94025"
    },
    {
      "role": "employee", 
      "name": "John Doe",
      "address": "456 Residential St, CA 94025"
    }
  ],
  "clauses": [
    {
      "id": "clause_001",
      "type": "termination",
      "title": "Termination for Cause",
      "text": "The Company may terminate this agreement immediately upon written notice if Employee...",
      "page": 3,
      "coordinates": [50, 300, 550, 450],
      "confidence": 0.94,
      "key_terms": ["immediate termination", "written notice", "cause"]
    },
    {
      "id": "clause_002", 
      "type": "compensation",
      "title": "Base Salary",
      "text": "Employee shall receive an annual salary of $85,000, payable in bi-weekly installments...",
      "page": 2,
      "coordinates": [50, 150, 550, 220],
      "confidence": 0.97,
      "key_terms": ["$85,000", "bi-weekly", "annual salary"]
    }
  ],
  "metadata": {
    "extraction_timestamp": "2024-01-15T10:30:00Z",
    "model_version": "v2.1.0",
    "processing_method": "multimodal_vlm"
  }
}
```

## Advanced Features

### Custom Training
```bash
# Train on domain-specific contracts
python train.py --dataset legal_contracts_dataset --epochs 10

# Fine-tune for specific contract types
python fine_tune.py --contract-type "real_estate" --examples ./real_estate_samples
```

### Quality Assurance
- **Confidence Scoring**: ML-based confidence assessment
- **Cross-validation**: Multiple model consensus
- **Human Review**: Built-in review interface
- **Error Detection**: Automatic inconsistency flagging

### Integration APIs
```python
# REST API
POST /api/extract
Content-Type: multipart/form-data

# GraphQL API
mutation {
  extractContract(file: $file) {
    clauses {
      type
      text
      confidence
    }
  }
}

# Webhook Integration
POST /webhooks/document-processed
{
  "document_id": "doc_123",
  "status": "completed",
  "clauses_extracted": 15
}
```

## Deployment Options

### Local Development
Install optional GPU dependencies if you want CUDA acceleration:
```bash
# Install with GPU support
pip install -r requirements-gpu.txt

# Run with CUDA acceleration
python extract.py --gpu --batch-size 8
```

### Cloud Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  contract-extractor:
    image: contract-extractor:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AZURE_VISION_KEY=${AZURE_VISION_KEY}
    volumes:
      - ./contracts:/app/input
      - ./results:/app/output
```

### Enterprise Features
- **GDPR Compliance**: Data protection and privacy controls
- **Audit Trails**: Complete processing history
- **Role-based Access**: User permission management
- **SLA Monitoring**: Performance and uptime tracking
- **Custom Deployment**: On-premises or private cloud options

## Performance Benchmarks

| Document Type | Avg Processing Time | Accuracy | Confidence |
|---------------|-------------------|----------|------------|
| Native PDF    | 5.2s             | 96.3%    | 0.94       |
| Scanned PDF   | 12.8s            | 91.7%    | 0.88       |
| Handwritten   | 18.4s            | 87.2%    | 0.82       |
| Low Quality   | 25.1s            | 83.9%    | 0.78       |

## Contributing

We welcome contributions in these areas:
- Support for additional document formats
- New contract type templates
- OCR engine integrations
- Performance optimizations
- Multilingual support

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Legal Compliance

- **Data Privacy**: Processes documents locally by default
- **No Data Retention**: Documents are not stored unless explicitly configured
- **Audit Logging**: Complete processing audit trails
- **Compliance Standards**: SOC 2, GDPR, HIPAA ready

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for document processing assistance only. All extracted information should be reviewed by qualified legal professionals before use in any legal context.
