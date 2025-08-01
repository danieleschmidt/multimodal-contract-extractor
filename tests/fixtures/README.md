# Test Fixtures

This directory contains test fixtures and sample data used across the test suite.

## Structure

- `contracts/` - Sample contract documents for testing
- `images/` - Sample image files for OCR testing  
- `data/` - JSON fixtures and test data files
- `configs/` - Test configuration files

## Usage

Test fixtures are automatically loaded by pytest and can be accessed in tests via fixture parameters:

```python
def test_document_processing(sample_contract_data):
    # Use the fixture data
    assert sample_contract_data["document_info"]["filename"]
```

## Adding New Fixtures

When adding new test fixtures:

1. Place sample files in appropriate subdirectories
2. Update `conftest.py` if new fixture functions are needed
3. Document any special requirements or dependencies
4. Ensure fixtures use synthetic or anonymized data only

## Security Note

**Never commit real contract documents or sensitive data to this repository.** Use only synthetic test data or properly anonymized samples.

## Synthetic Data

All contract samples should be clearly synthetic and not based on real agreements. Use generic company names, addresses, and terms that cannot be mistaken for real legal documents.