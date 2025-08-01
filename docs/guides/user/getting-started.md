# Getting Started Guide

## Overview

Welcome to the Multimodal Contract Extractor! This guide will help you get up and running quickly with document processing. Whether you're processing a single contract or hundreds of documents, this guide covers the essential steps.

## Prerequisites

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for web interface
- For CLI usage: Python 3.8+ installed locally

### Supported Document Types
- **PDF Files**: Native and scanned PDFs
- **Image Files**: PNG, JPEG, TIFF, BMP formats
- **Contract Types**: NDAs, employment contracts, leases, service agreements

## Quick Start (Web Interface)

### Step 1: Access the Application
1. Navigate to the web interface URL
2. The application will load in your browser
3. You'll see the main document upload interface

### Step 2: Upload Your Document
1. Click the "Browse files" button or drag-and-drop your document
2. Select a PDF or image file from your computer
3. The file will be validated and uploaded automatically

### Step 3: Process the Document
1. Click the "Extract Clauses" button
2. Wait for processing to complete (typically 5-30 seconds)
3. View the real-time progress indicator

### Step 4: Review Results
1. Extracted clauses will appear in the results panel
2. Each clause shows:
   - **Type**: Category of the clause (e.g., termination, compensation)
   - **Text**: Full clause content
   - **Confidence**: Accuracy score (0-100%)
   - **Location**: Page and coordinates in the document

### Step 5: Export Results
1. Choose your preferred export format:
   - **JSON**: Structured data for programmatic use
   - **CSV**: Spreadsheet-compatible format
   - **XML**: Standardized markup format
2. Click "Download" to save the results

## Command Line Interface

### Installation
```bash
# Clone the repository
git clone https://github.com/your-org/multimodal-contract-extractor
cd multimodal-contract-extractor

# Install dependencies
pip install -r requirements.txt
```

### Single Document Processing
```bash
# Process a single contract
python extract.py --file contract.pdf --output results.json

# Specify output format
python extract.py --file contract.pdf --output results.csv --format csv

# Enable detailed logging
python extract.py --file contract.pdf --log-level debug
```

### Batch Processing
```bash
# Process a directory of documents
python batch_extract.py --input-dir ./contracts --output-dir ./results

# Process with custom configuration
python batch_extract.py --input-dir ./contracts --output-dir ./results --config custom-config.yml
```

## Understanding Results

### JSON Output Structure
```json
{
  "document_info": {
    "filename": "employment_contract.pdf",
    "pages": 5,
    "processing_time": 23.4,
    "overall_confidence": 0.89
  },
  "clauses": [
    {
      "id": "clause_001",
      "type": "termination",
      "title": "Termination for Cause",
      "text": "The Company may terminate...",
      "page": 3,
      "coordinates": [50, 300, 550, 450],
      "confidence": 0.94
    }
  ]
}
```

### Confidence Scores
- **90-100%**: High confidence, likely accurate
- **75-89%**: Good confidence, review recommended
- **60-74%**: Medium confidence, verification needed
- **Below 60%**: Low confidence, manual review required

## Best Practices

### Document Preparation
1. **Quality**: Use high-resolution scans (300+ DPI)
2. **Orientation**: Ensure documents are right-side up
3. **Contrast**: High contrast between text and background
4. **File Size**: Keep files under 50MB for optimal performance

### Processing Tips
1. **Review Low Confidence**: Always review clauses with <75% confidence
2. **Verify Critical Clauses**: Double-check important terms like dates and amounts
3. **Batch Similar Documents**: Process similar contract types together
4. **Save Configurations**: Use config files for consistent processing

### Security Considerations
1. **Sensitive Data**: Documents are processed locally and not stored
2. **Temporary Files**: Automatically cleaned up after processing
3. **Network Security**: Use HTTPS for web interface access
4. **Access Control**: Implement proper authentication for production use

## Troubleshooting

### Common Issues

#### "File format not supported"
- **Solution**: Ensure file is PDF, PNG, JPEG, TIFF, or BMP format
- **Workaround**: Convert unsupported formats using online tools

#### "Processing timeout"
- **Cause**: Large or complex documents may take longer
- **Solution**: Try processing smaller sections or increase timeout settings

#### "Low confidence scores"
- **Cause**: Poor document quality or unusual formatting
- **Solution**: Improve scan quality or try manual preprocessing

#### "No clauses detected"
- **Cause**: Document may not contain standard contract language
- **Solution**: Verify document type and content

### Getting Help
- **Documentation**: Check the full documentation in `/docs`
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join our discussion forums
- **Support**: Contact support for enterprise customers

## Next Steps

Once you're comfortable with basic usage:

1. **Explore Advanced Features**: Learn about custom configurations and batch processing
2. **API Integration**: Integrate with your existing systems using the REST API
3. **Custom Workflows**: Set up automated processing pipelines
4. **Performance Optimization**: Configure caching and parallel processing

## Examples

### Example 1: Processing an NDA
```bash
python extract.py --file nda.pdf --output nda_results.json
```

Expected output includes:
- Confidentiality clauses
- Term duration
- Permitted disclosures
- Remedies and penalties

### Example 2: Batch Processing Employment Contracts
```bash
python batch_extract.py --input-dir ./employment_contracts --output-dir ./hr_results
```

Results will include:
- Compensation terms
- Benefits information
- Termination conditions
- Non-compete clauses

## Additional Resources

- **API Documentation**: `/docs/api/`
- **Configuration Guide**: `CONFIGURATION.md`
- **Security Guide**: `SECURITY.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`
- **Contributing**: `CONTRIBUTING.md`

---

**Need more help?** Check out our other guides in the `/docs/guides/` directory or contact our support team.