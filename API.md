# API Documentation

This document provides comprehensive API documentation for the Multimodal Contract Extractor.

## Core APIs

### Document Loading

#### `load_document(file_path: str) -> Document`

Load a document from file system for processing.

**Parameters:**
- `file_path` (str): Path to the document file (PDF, PNG, JPEG, etc.)

**Returns:**
- `Document`: Document object containing pages and metadata

**Example:**
```python
from multimodal_contract_extractor.document import load_document

# Load a PDF document
document = load_document("contract.pdf")
print(f"Document has {len(document.pages)} pages")

# Access page content
for page in document.pages:
    print(f"Page {page.page_number}: {len(page.text)} characters")
```

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If the file format is not supported

#### `stream_document(file_path: str, chunk_size: int = 10) -> Iterator[Document]`

Load large documents in streaming chunks to reduce memory usage.

**Parameters:**
- `file_path` (str): Path to the document file
- `chunk_size` (int): Number of pages per chunk (default: 10)

**Returns:**
- `Iterator[Document]`: Iterator yielding document chunks

**Example:**
```python
from multimodal_contract_extractor.document import stream_document

# Process large document in chunks
for chunk in stream_document("large_contract.pdf", chunk_size=5):
    print(f"Processing chunk with {len(chunk.pages)} pages")
    # Process chunk...
```

### Clause Detection

#### `detect_clauses(document: Document, keywords: Dict[str, List[str]] = None) -> List[Clause]`

Extract clauses from a document using OCR and keyword matching.

**Parameters:**
- `document` (Document): Document object to process
- `keywords` (Dict[str, List[str]], optional): Custom keyword mappings for clause types

**Returns:**
- `List[Clause]`: List of detected clauses with metadata

**Example:**
```python
from multimodal_contract_extractor.document import load_document
from multimodal_contract_extractor.clause_detection import detect_clauses

# Basic clause detection
document = load_document("nda.pdf")
clauses = detect_clauses(document)

for clause in clauses:
    print(f"Type: {clause.type}")
    print(f"Text: {clause.text[:100]}...")
    print(f"Confidence: {clause.confidence}")
    print(f"Key terms: {clause.key_terms}")
    print("---")

# Custom keyword detection
custom_keywords = {
    "payment_terms": ["payment", "invoice", "billing", "due date"],
    "liability": ["liable", "responsibility", "damages", "indemnify"]
}

clauses = detect_clauses(document, keywords=custom_keywords)
```

### Document Processing

#### `extract_from_document(file_path: str) -> ExtractionResult`

High-level API for complete document processing pipeline.

**Parameters:**
- `file_path` (str): Path to the document file

**Returns:**
- `ExtractionResult`: Complete extraction result with document info and clauses

**Example:**
```python
from multimodal_contract_extractor.extraction import extract_from_document

# Complete document processing
result = extract_from_document("employment_contract.pdf")

# Access document metadata
print(f"Filename: {result.document_info.filename}")
print(f"Pages: {result.document_info.pages}")
print(f"Processing time: {result.document_info.processing_time}s")
print(f"Overall confidence: {result.document_info.overall_confidence}")

# Access extracted clauses
for clause in result.clauses:
    print(f"{clause.type}: {clause.title}")
```

### Configuration

#### `load_config(config_path: str = None) -> Config`

Load configuration from file and environment variables.

**Parameters:**
- `config_path` (str, optional): Path to YAML configuration file

**Returns:**
- `Config`: Configuration object with all settings

**Example:**
```python
from multimodal_contract_extractor.config import load_config, get_config

# Load from specific file
config = load_config("custom_config.yml")

# Load from default locations
config = get_config()

# Access configuration values
print(f"OCR cache limit: {config.ocr.cache_size_limit}")
print(f"Max file size: {config.security.max_file_size_mb}MB")
print(f"Base confidence: {config.extraction.base_confidence_score}")
```

#### `get_config() -> Config`

Get current configuration (loads defaults if not previously configured).

**Returns:**
- `Config`: Current configuration object

### Security & File Management

#### `TempFileManager(uploaded_file) -> ContextManager[Path]`

Secure context manager for temporary file handling with automatic cleanup.

**Parameters:**
- `uploaded_file`: File-like object with `name` and `read()` method

**Returns:**
- `ContextManager[Path]`: Context manager yielding temporary file path

**Example:**
```python
from web_app import TempFileManager

# Secure file processing
uploaded_file = request.files['document']
with TempFileManager(uploaded_file) as temp_path:
    # File is automatically cleaned up when exiting this block
    result = extract_from_document(temp_path)
    return result
```

**Features:**
- Automatic cleanup on context exit
- Exception-safe cleanup
- Restrictive file permissions (0o600)
- Path sanitization to prevent security issues

## Data Models

### Clause

Represents an extracted clause from a document.

**Attributes:**
- `id` (str): Unique clause identifier
- `type` (str): Clause type (e.g., "termination", "compensation")
- `title` (str): Human-readable clause title
- `text` (str): Full clause text content
- `page` (int): Page number where clause appears
- `coordinates` (List[int]): Bounding box coordinates [x1, y1, x2, y2]
- `confidence` (float): Confidence score (0.0-1.0)
- `key_terms` (List[str]): Important terms extracted from the clause

**Example:**
```python
clause = Clause(
    id="clause_001",
    type="termination",
    title="Termination for Cause",
    text="The Company may terminate this agreement...",
    page=3,
    coordinates=[50, 300, 550, 450],
    confidence=0.94,
    key_terms=["immediate termination", "written notice", "cause"]
)
```

### Document

Represents a loaded document with pages and metadata.

**Attributes:**
- `pages` (List[Page]): List of document pages
- `metadata` (Dict): Document metadata

### ExtractionResult

Complete result from document extraction process.

**Attributes:**
- `document_info` (DocumentInfo): Document metadata and processing info
- `clauses` (List[Clause]): List of extracted clauses

### Config

Configuration object with structured settings.

**Sections:**
- `ocr`: OCR-related settings
- `extraction`: Extraction algorithm settings
- `security`: Security and validation settings
- `health`: Health check settings
- `document`: Document processing settings

## CLI Commands

### extract.py

Process a single document file.

```bash
# Basic usage
python extract.py --file contract.pdf --output result.json

# With custom configuration
python extract.py --file contract.pdf --config custom.yml --output result.json

# With debug logging
python extract.py --file contract.pdf --log-level debug

# Multiple output formats
python extract.py --file contract.pdf --format json --output-dir ./results

# With metrics collection
python extract.py --file contract.pdf --metrics-file metrics.json
```

**Options:**
- `--file` / `-f`: Input file path (required)
- `--output` / `-o`: Output file path
- `--format`: Output format (json, xml, csv)
- `--config` / `-c`: Configuration file path
- `--log-level`: Logging level (debug, info, warning, error)
- `--output-dir`: Output directory path
- `--metrics-file`: Metrics output file path
- `--version`: Show version information

### batch_extract.py

Process multiple documents in batch.

```bash
# Basic batch processing
python batch_extract.py --input-dir ./contracts --output-dir ./results

# With custom configuration
python batch_extract.py --input-dir ./contracts --output-dir ./results --config custom.yml

# Specific output format
python batch_extract.py --input-dir ./contracts --output-dir ./results --format xml
```

**Options:**
- `--input-dir` / `-i`: Input directory path (required)
- `--output-dir` / `-o`: Output directory path (required)
- `--format`: Output format (json, xml, csv)
- `--config` / `-c`: Configuration file path
- `--log-level`: Logging level
- `--version`: Show version information

## Web Interface API

### Streamlit Application

The web interface provides an interactive document processing experience.

```bash
# Start web interface
streamlit run web_app.py

# With custom port
streamlit run web_app.py --server.port 8080
```

**Features:**
- File upload with validation
- Real-time processing status
- Results visualization
- Download processed results
- Error handling and recovery

### REST API Endpoints

When running in API mode, the following endpoints are available:

#### POST /api/extract

Extract clauses from uploaded document.

**Request:**
```bash
curl -X POST -F "file=@contract.pdf" http://localhost:8080/api/extract
```

**Response:**
```json
{
  "status": "success",
  "document_info": {
    "filename": "contract.pdf",
    "pages": 5,
    "processing_time": 12.3
  },
  "clauses": [
    {
      "type": "termination",
      "text": "...",
      "confidence": 0.94
    }
  ]
}
```

#### GET /api/health

Check system health and dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "dependencies": {
    "tesseract": "5.3.4",
    "poppler": "24.02.0",
    "python_packages": "all_installed"
  }
}
```

## Error Handling

### Common Exceptions

- `FileNotFoundError`: Input file not found
- `ValueError`: Invalid file format or parameters
- `ConfigurationError`: Invalid configuration settings
- `ExtractionError`: Document processing failed
- `SecurityError`: File validation failed

### Error Response Format

```json
{
  "status": "error",
  "error_code": "EXTRACTION_FAILED",
  "message": "Unable to process document",
  "details": {
    "file": "contract.pdf",
    "reason": "OCR processing failed"
  }
}
```

## Performance Considerations

### Memory Management

- Use `stream_document()` for large files (>10MB)
- Configure `extraction.file_size_threshold_mb` for automatic streaming
- Set appropriate `extraction.streaming_chunk_size` based on available memory

### Caching

- OCR results are cached automatically
- Configure `ocr.cache_size_limit` to control cache size
- Cache keys are based on image content hash

### Batch Processing

- Process multiple files in parallel using batch_extract.py
- Configure chunk sizes based on available system resources
- Monitor memory usage with built-in metrics

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, UploadFile
from multimodal_contract_extractor.extraction import extract_from_document
from web_app import TempFileManager

app = FastAPI()

@app.post("/extract")
async def extract_document(file: UploadFile):
    with TempFileManager(file) as temp_path:
        result = extract_from_document(temp_path)
        return result
```

### Django Integration

```python
from django.http import JsonResponse
from multimodal_contract_extractor.extraction import extract_from_document
from web_app import TempFileManager

def extract_view(request):
    uploaded_file = request.FILES['document']
    with TempFileManager(uploaded_file) as temp_path:
        result = extract_from_document(temp_path)
        return JsonResponse(result)
```

### Celery Task Integration

```python
from celery import Celery
from multimodal_contract_extractor.extraction import extract_from_document

app = Celery('contract_extractor')

@app.task
def process_document_async(file_path):
    result = extract_from_document(file_path)
    return result
```