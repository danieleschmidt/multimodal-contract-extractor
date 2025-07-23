# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Multimodal Contract Extractor.

## Quick Diagnosis

### Health Check

Run the built-in health check to identify system issues:

```bash
python -c "from multimodal_contract_extractor.health import health_check; health_check()"
```

Expected output:
```
Health check passed: All dependencies are available
- Tesseract OCR: v5.3.4
- Poppler utilities: v24.02.0
- Python packages: all installed
```

### Version Information

```bash
python extract.py --version
python batch_extract.py --version
```

### Test Installation

```bash
# Quick test with sample file
python extract.py --file tests/fixtures/sample.pdf --output test_result.json

# Run test suite
pytest tests/ -v
```

## Common Issues

### Installation Problems

#### Issue: `ModuleNotFoundError: No module named 'multimodal_contract_extractor'`

**Cause**: Package not installed or virtual environment not activated.

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install package
pip install -r requirements.txt
pip install -e .
```

#### Issue: `FileNotFoundError: [Errno 2] No such file or directory: 'tesseract'`

**Cause**: Tesseract OCR not installed or not in PATH.

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Windows
choco install tesseract

# Verify installation
tesseract --version
which tesseract  # Linux/Mac
where tesseract  # Windows
```

#### Issue: `PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?`

**Cause**: Poppler utilities not installed.

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install poppler-utils

# macOS
brew install poppler

# Windows
choco install poppler

# Verify installation
pdfinfo -v
which pdfinfo  # Linux/Mac
```

### Configuration Issues

#### Issue: `ConfigurationError: Invalid configuration file`

**Cause**: Malformed YAML configuration file.

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Use example configuration
cp config.example.yml config.yml

# Check configuration loading
python -c "from multimodal_contract_extractor.config import load_config; print(load_config())"
```

#### Issue: Environment variables not being loaded

**Cause**: Incorrect environment variable naming or format.

**Solution**:
```bash
# Check environment variables
env | grep MCE_

# Correct format
export MCE_OCR_CACHE_SIZE_LIMIT=100
export MCE_EXTRACTION_BASE_CONFIDENCE_SCORE=0.8

# Verify loading
python -c "from multimodal_contract_extractor.config import get_config; c = get_config(); print(f'Cache limit: {c.ocr.cache_size_limit}')"
```

### Document Processing Issues

#### Issue: `ValueError: Unsupported file format`

**Cause**: File format not supported or file corrupted.

**Solution**:
```bash
# Check file type
file contract.pdf
mimetype contract.pdf  # Linux

# Convert to supported format
# PDF to PDF (repair)
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -o repaired.pdf input.pdf

# Image to supported format
convert image.tiff image.png  # ImageMagick
```

#### Issue: `ExtractionError: OCR processing failed`

**Cause**: Poor image quality, unsupported language, or corrupted file.

**Diagnosis**:
```python
from multimodal_contract_extractor.document import load_document
import pytesseract

document = load_document("problematic.pdf")
for page in document.pages:
    try:
        text = pytesseract.image_to_string(page.image)
        print(f"Page {page.page_number}: {len(text)} characters extracted")
    except Exception as e:
        print(f"Page {page.page_number} failed: {e}")
```

**Solutions**:
1. **Improve image quality**:
   ```bash
   # Increase DPI for PDF conversion
   export MCE_DOCUMENT_PDF_DPI=300
   ```

2. **Install language packs**:
   ```bash
   sudo apt install tesseract-ocr-fra tesseract-ocr-deu
   tesseract --list-langs
   ```

3. **Preprocess images**:
   ```python
   from PIL import Image, ImageEnhance
   
   # Enhance contrast and sharpness
   image = Image.open("document.png")
   enhancer = ImageEnhance.Contrast(image)
   image = enhancer.enhance(2.0)
   enhancer = ImageEnhance.Sharpness(image)
   image = enhancer.enhance(2.0)
   ```

#### Issue: `MemoryError: Unable to allocate memory`

**Cause**: Large documents exceeding available memory.

**Solutions**:
1. **Enable streaming**:
   ```python
   from multimodal_contract_extractor.document import stream_document
   
   for chunk in stream_document("large_document.pdf", chunk_size=5):
       # Process in smaller chunks
       pass
   ```

2. **Adjust configuration**:
   ```yaml
   # config.yml
   extraction:
     file_size_threshold_mb: 10  # Lower threshold for streaming
     streaming_chunk_size: 3     # Smaller chunks
   
   document:
     default_streaming_chunk_size: 5
   ```

3. **Increase system memory or use swap**:
   ```bash
   # Add swap space (Linux)
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Performance Issues

#### Issue: Very slow processing

**Diagnosis**:
```python
import time
from multimodal_contract_extractor.extraction import extract_from_document

start_time = time.time()
result = extract_from_document("document.pdf")
processing_time = time.time() - start_time
print(f"Processing took {processing_time:.2f} seconds")
print(f"Cache hit rate: {result.metadata.get('cache_hit_rate', 'unknown')}")
```

**Solutions**:
1. **Enable caching**:
   ```yaml
   # config.yml
   ocr:
     cache_size_limit: 500  # Increase cache size
   ```

2. **Optimize chunk sizes**:
   ```yaml
   extraction:
     streaming_chunk_size: 10  # Larger chunks if memory allows
   ```

3. **Use performance monitoring**:
   ```bash
   python extract.py --file document.pdf --metrics-file metrics.json
   ```

#### Issue: High memory usage

**Diagnosis**:
```bash
# Monitor memory during processing
python -c "
import psutil
from multimodal_contract_extractor.extraction import extract_from_document

process = psutil.Process()
print(f'Memory before: {process.memory_info().rss / 1024 / 1024:.1f} MB')

result = extract_from_document('document.pdf')

print(f'Memory after: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

**Solutions**:
1. **Force garbage collection**:
   ```python
   import gc
   gc.collect()  # Force cleanup after processing
   ```

2. **Reduce cache size**:
   ```yaml
   ocr:
     cache_size_limit: 50  # Smaller cache
   ```

3. **Use streaming for all files**:
   ```yaml
   extraction:
     file_size_threshold_mb: 1  # Stream all files
   ```

### Web Interface Issues

#### Issue: `StreamlitAPIException: No uploaded file`

**Cause**: File upload component not working properly.

**Solutions**:
1. **Check browser compatibility**:
   - Use Chrome, Firefox, or Safari
   - Clear browser cache
   - Disable ad blockers

2. **Check file size limits**:
   ```yaml
   security:
     max_file_size_mb: 100  # Adjust limit
   ```

3. **Debug upload process**:
   ```python
   # Add to web_app.py for debugging
   if uploaded_file:
       st.write(f"File name: {uploaded_file.name}")
       st.write(f"File size: {uploaded_file.size} bytes")
   ```

#### Issue: Web interface crashes during processing

**Diagnosis**:
```bash
# Run with debug logging
streamlit run web_app.py --logger.level=debug
```

**Solutions**:
1. **Increase timeout**:
   ```bash
   streamlit run web_app.py --server.maxUploadSize=200
   ```

2. **Add error handling**:
   ```python
   try:
       result = process_upload_with_cleanup(uploaded_file)
       st.success("Processing completed!")
   except Exception as e:
       st.error(f"Processing failed: {str(e)}")
       st.exception(e)  # Show full traceback in debug mode
   ```

### CLI Issues

#### Issue: `FileNotFoundError: [Errno 2] No such file or directory`

**Cause**: Input file path incorrect or file doesn't exist.

**Solutions**:
```bash
# Check file exists
ls -la contract.pdf
file contract.pdf

# Use absolute path
python extract.py --file /full/path/to/contract.pdf

# Check current directory
pwd
ls -la
```

#### Issue: Permission denied when creating output files

**Cause**: Insufficient permissions for output directory.

**Solutions**:
```bash
# Check permissions
ls -la output_directory/

# Create directory with proper permissions
mkdir -p output && chmod 755 output

# Use different output location
python extract.py --file contract.pdf --output ~/Documents/result.json
```

### Batch Processing Issues

#### Issue: Some files in batch fail to process

**Diagnosis**:
```bash
# Run with debug logging
python batch_extract.py --input-dir ./contracts --output-dir ./results --log-level debug
```

**Solutions**:
1. **Check individual files**:
   ```bash
   for file in contracts/*.pdf; do
       echo "Testing $file"
       python extract.py --file "$file" --output "test_$(basename "$file").json" || echo "FAILED: $file"
   done
   ```

2. **Skip problematic files**:
   ```python
   import os
   from pathlib import Path
   
   failed_files = []
   for file_path in Path("contracts").glob("*.pdf"):
       try:
           result = extract_from_document(file_path)
       except Exception as e:
           failed_files.append((file_path, str(e)))
           print(f"Skipping {file_path}: {e}")
   
   print(f"Failed files: {len(failed_files)}")
   ```

## Debugging Tools

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export MCE_LOG_LEVEL=DEBUG
```

### Profiling Performance

```python
import cProfile
import pstats

def profile_extraction():
    from multimodal_contract_extractor.extraction import extract_from_document
    result = extract_from_document("document.pdf")
    return result

# Profile the extraction
cProfile.run('profile_extraction()', 'profile_stats')

# Analyze results
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions by cumulative time
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def extract_with_memory_tracking():
    from multimodal_contract_extractor.extraction import extract_from_document
    result = extract_from_document("document.pdf")
    return result

# Run with: python -m memory_profiler script.py
```

### Testing Components Individually

```python
# Test document loading
from multimodal_contract_extractor.document import load_document
document = load_document("contract.pdf")
print(f"Loaded {len(document.pages)} pages")

# Test OCR
import pytesseract
from PIL import Image
image = Image.open("page1.png")
text = pytesseract.image_to_string(image)
print(f"Extracted {len(text)} characters")

# Test clause detection
from multimodal_contract_extractor.clause_detection import detect_clauses
clauses = detect_clauses(document)
print(f"Found {len(clauses)} clauses")
```

## Error Codes Reference

### System Errors (1xxx)
- `1001`: Tesseract not installed
- `1002`: Poppler not installed  
- `1003`: Python dependencies missing
- `1004`: Configuration file not found
- `1005`: Invalid configuration format

### File Errors (2xxx)
- `2001`: File not found
- `2002`: Unsupported file format
- `2003`: File corrupted or unreadable
- `2004`: File too large
- `2005`: Permission denied

### Processing Errors (3xxx)
- `3001`: OCR processing failed
- `3002`: Document parsing failed
- `3003`: Clause detection failed
- `3004`: Memory allocation failed
- `3005`: Processing timeout

### Output Errors (4xxx)
- `4001`: Output directory not writable
- `4002`: Output format not supported
- `4003`: Serialization failed

## Getting Help

### Collect Diagnostic Information

```bash
#!/bin/bash
# diagnostic.sh - Collect system information

echo "=== System Information ==="
uname -a
python --version
pip --version

echo "=== Dependencies ==="
tesseract --version
pdfinfo -v
python -c "import pytesseract, pdf2image, Pillow; print('Python packages OK')"

echo "=== Configuration ==="
python -c "from multimodal_contract_extractor.config import get_config; print(get_config())"

echo "=== Health Check ==="
python -c "from multimodal_contract_extractor.health import health_check; health_check()"

echo "=== Recent Logs ==="
tail -n 50 logs/application.log 2>/dev/null || echo "No logs found"

echo "=== Environment Variables ==="
env | grep MCE_ | sort
```

### Support Channels

1. **GitHub Issues**: Report bugs with diagnostic information
2. **Documentation**: Check README.md and API.md
3. **Community**: Stack Overflow with tag `multimodal-contract-extractor`

### Bug Report Template

```markdown
## Bug Description
Brief description of the issue

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.12.3]
- Package version: [output of `python extract.py --version`]

## Steps to Reproduce
1. Run command: `python extract.py --file example.pdf`
2. Expected: Successful extraction
3. Actual: Error message

## Error Output
```
[Full error traceback here]
```

## Diagnostic Information
```
[Output of diagnostic.sh script]
```

## Additional Context
Any other relevant information
```

### Performance Issues Template

```markdown
## Performance Issue
Description of slow performance

## System Specs
- CPU: [e.g., Intel i7-9700K]
- RAM: [e.g., 16GB]
- Storage: [e.g., SSD]

## Document Details
- File size: [e.g., 15MB]
- Pages: [e.g., 25 pages]
- Format: [e.g., Scanned PDF]

## Timing Information
- Processing time: [e.g., 120 seconds]
- Expected time: [e.g., <30 seconds]

## Configuration
```yaml
[Your config.yml content]
```

## Profiling Data
[Output from performance profiling]
```

## Advanced Troubleshooting

### Database Issues (if using external storage)

```python
# Test database connection
from multimodal_contract_extractor.database import get_connection
try:
    conn = get_connection()
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
```

### Network Issues (if using remote services)

```bash
# Test network connectivity
curl -I https://api.openai.com/v1/models
ping -c 4 8.8.8.8

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

### Container-specific Issues

```bash
# Check container logs
docker logs contract-extractor

# Execute commands in container
docker exec -it contract-extractor bash

# Check container resources
docker stats contract-extractor
```

### Kubernetes Issues

```bash
# Check pod status
kubectl get pods -l app=contract-extractor

# Check pod logs
kubectl logs -f deployment/contract-extractor

# Describe pod for events
kubectl describe pod <pod-name>

# Check resource usage
kubectl top pods
```