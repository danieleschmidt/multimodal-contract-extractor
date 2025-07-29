# OpenAPI Specification

Interactive REST API documentation with OpenAPI/Swagger.

## API Specification

<!-- swagger-ui config="swagger_config.json" -->

```yaml
openapi: 3.0.3
info:
  title: Multimodal Contract Extractor API
  description: |
    REST API for extracting clauses from contracts using vision-language models.
    
    ## Features
    - PDF and image document processing
    - OCR with Tesseract
    - Advanced clause detection
    - Secure file handling
    - Performance monitoring
    
  version: 0.1.0
  contact:
    name: Terragon Labs
    url: https://github.com/terragon-labs/multimodal-contract-extractor
    email: contact@terragon.ai
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8501
    description: Development server
  - url: https://api.example.com/v1
    description: Production server

paths:
  /api/v1/extract:
    post:
      summary: Extract clauses from document
      description: |
        Upload a document and extract contract clauses using OCR and NLP.
        Supports PDF and image formats.
      operationId: extractClauses
      tags:
        - Extraction
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: Document file (PDF or image)
                format:
                  type: string
                  enum: [json, xml, csv]
                  default: json
                  description: Output format
                confidence_threshold:
                  type: number
                  minimum: 0.0
                  maximum: 1.0
                  default: 0.8
                  description: Minimum confidence threshold for clause detection
              required:
                - file
      responses:
        '200':
          description: Extraction successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractionResult'
            application/xml:
              schema:
                $ref: '#/components/schemas/ExtractionResultXML'
            text/csv:
              schema:
                type: string
                description: CSV formatted results
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '413':
          description: File too large
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Unsupported file format
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /api/v1/batch:
    post:
      summary: Batch process multiple documents
      description: |
        Process multiple documents in a single request.
        Returns results for all successfully processed documents.
      operationId: batchExtract
      tags:
        - Extraction
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                files:
                  type: array
                  items:
                    type: string
                    format: binary
                  description: Multiple document files
                format:
                  type: string
                  enum: [json, xml, csv]
                  default: json
                parallel:
                  type: boolean
                  default: true
                  description: Process files in parallel
              required:
                - files
      responses:
        '200':
          description: Batch processing completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BatchResult'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /api/v1/health:
    get:
      summary: Health check
      description: Check API health and system status
      operationId: healthCheck
      tags:
        - System
      responses:
        '200':
          description: System healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthStatus'
        '503':
          description: System unhealthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthStatus'

  /api/v1/metrics:
    get:
      summary: Get system metrics
      description: Retrieve performance and usage metrics
      operationId: getMetrics
      tags:
        - System
      responses:
        '200':
          description: Metrics retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Metrics'

  /api/v1/config:
    get:
      summary: Get configuration
      description: Retrieve current system configuration
      operationId: getConfig
      tags:
        - Configuration
      responses:
        '200':
          description: Configuration retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Configuration'

components:
  schemas:
    ExtractionResult:
      type: object
      properties:
        success:
          type: boolean
          description: Whether extraction was successful
        document_id:
          type: string
          description: Unique document identifier
        clauses:
          type: array
          items:
            $ref: '#/components/schemas/Clause'
        metadata:
          $ref: '#/components/schemas/DocumentMetadata'
        processing_time:
          type: number
          description: Processing time in seconds
        confidence_score:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: Overall confidence score
      required:
        - success
        - document_id
        - clauses
        - processing_time

    Clause:
      type: object
      properties:
        id:
          type: string
          description: Unique clause identifier
        text:
          type: string
          description: Extracted clause text
        category:
          type: string
          enum: [payment, termination, liability, confidentiality, other]
          description: Clause category
        confidence:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: Confidence score for this clause
        coordinates:
          $ref: '#/components/schemas/BoundingBox'
        page_number:
          type: integer
          minimum: 1
          description: Page number where clause was found
      required:
        - id
        - text
        - category
        - confidence

    BoundingBox:
      type: object
      properties:
        x:
          type: number
          description: X coordinate
        y:
          type: number
          description: Y coordinate
        width:
          type: number
          description: Bounding box width
        height:
          type: number
          description: Bounding box height
      required:
        - x
        - y
        - width
        - height

    DocumentMetadata:
      type: object
      properties:
        filename:
          type: string
          description: Original filename
        file_size:
          type: integer
          description: File size in bytes
        mime_type:
          type: string
          description: MIME type
        page_count:
          type: integer
          description: Number of pages
        language:
          type: string
          description: Detected language
        creation_date:
          type: string
          format: date-time
          description: Document creation date
        ocr_confidence:
          type: number
          description: OCR confidence score

    BatchResult:
      type: object
      properties:
        success:
          type: boolean
        total_files:
          type: integer
        processed_files:
          type: integer
        failed_files:
          type: integer
        results:
          type: array
          items:
            $ref: '#/components/schemas/ExtractionResult'
        errors:
          type: array
          items:
            type: object
            properties:
              filename:
                type: string
              error:
                type: string
        total_processing_time:
          type: number

    HealthStatus:
      type: object
      properties:
        status:
          type: string
          enum: [healthy, unhealthy, degraded]
        timestamp:
          type: string
          format: date-time
        version:
          type: string
        uptime:
          type: number
          description: Uptime in seconds
        checks:
          type: object
          properties:
            database:
              type: string
              enum: [ok, error]
            storage:
              type: string
              enum: [ok, error]
            ocr_engine:
              type: string
              enum: [ok, error]
            memory:
              type: string
              enum: [ok, warning, error]

    Metrics:
      type: object
      properties:
        requests_total:
          type: integer
        requests_successful:
          type: integer
        requests_failed:
          type: integer
        avg_processing_time:
          type: number
        documents_processed:
          type: integer
        memory_usage:
          type: object
          properties:
            current:
              type: number
            peak:
              type: number
        cpu_usage:
          type: number

    Configuration:
      type: object
      properties:
        ocr:
          type: object
          properties:
            engine:
              type: string
            language:
              type: string
            confidence_threshold:
              type: number
        processing:
          type: object
          properties:
            max_file_size:
              type: integer
            batch_size:
              type: integer
            timeout:
              type: integer
        output:
          type: object
          properties:
            formats:
              type: array
              items:
                type: string

    Error:
      type: object
      properties:
        error:
          type: string
          description: Error type
        message:
          type: string
          description: Human-readable error message
        details:
          type: object
          description: Additional error details
        timestamp:
          type: string
          format: date-time
        request_id:
          type: string
          description: Unique request identifier
      required:
        - error
        - message
        - timestamp

    ExtractionResultXML:
      type: object
      xml:
        name: extraction_result
      properties:
        success:
          type: boolean
          xml:
            attribute: true
        document_id:
          type: string
        clauses:
          type: array
          items:
            type: object
            xml:
              name: clause
            properties:
              id:
                type: string
                xml:
                  attribute: true
              text:
                type: string
              category:
                type: string
              confidence:
                type: number

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    BearerAuth:
      type: http
      scheme: bearer

tags:
  - name: Extraction
    description: Document processing and clause extraction
  - name: System
    description: System health and monitoring
  - name: Configuration
    description: Configuration management

externalDocs:
  description: Find more info here
  url: https://github.com/terragon-labs/multimodal-contract-extractor
```

<!-- /swagger-ui -->

## Try It Out

You can test the API endpoints directly from this documentation using the interactive Swagger UI above.

### Authentication

For production deployments, API endpoints may require authentication:

```bash
# Using API Key
curl -H "X-API-Key: your-api-key" \
     -X POST http://localhost:8501/api/v1/extract

# Using Bearer Token  
curl -H "Authorization: Bearer your-token" \
     -X POST http://localhost:8501/api/v1/extract
```

### Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Development**: 100 requests per minute
- **Production**: 1000 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request - Invalid parameters |
| 401  | Unauthorized - Missing or invalid authentication |
| 413  | Payload Too Large - File exceeds size limit |
| 422  | Unprocessable Entity - Unsupported file format |
| 429  | Too Many Requests - Rate limit exceeded |
| 500  | Internal Server Error - Processing failed |

## SDK Examples

### Python

```python
import requests

# Extract from single document
with open('contract.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8501/api/v1/extract',
        files={'file': f},
        data={'format': 'json'}
    )

result = response.json()
print(f"Found {len(result['clauses'])} clauses")
```

### JavaScript

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('format', 'json');

fetch('/api/v1/extract', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log(`Found ${data.clauses.length} clauses`);
});
```

### cURL

```bash
# Extract clauses
curl -X POST \
  -F "file=@contract.pdf" \
  -F "format=json" \
  http://localhost:8501/api/v1/extract

# Check health
curl http://localhost:8501/api/v1/health

# Get metrics
curl http://localhost:8501/api/v1/metrics
```