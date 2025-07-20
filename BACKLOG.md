# Development Backlog - Impact Ranked (WSJF)

## High-Impact Items (Score: 8-10)

### 🎯 P1: ✅ COMPLETED - Implement Real Clause Extraction (Score: 10)
- **Impact**: High (enables core value proposition) ✅
- **Effort**: High (ML integration, model selection) 
- **Risk**: Medium (dependency on external models)
- **Description**: Replace placeholder extraction with OCR + VLM pipeline
- **Completed**: v0.3.0 (2025-07-20)
- **Tasks**:
  - [x] Integrate Tesseract/PaddleOCR for text extraction ✅
  - [x] Add keyword-based clause classification (foundation for future VLM) ✅  
  - [x] Implement confidence scoring ✅
  - [x] Add clause boundary detection ✅
- **Future Enhancement**: Upgrade from keyword-based to VLM-based classification

### 🔐 P2: ✅ COMPLETED - Security Hardening (Score: 9)
- **Impact**: High (production readiness, compliance) ✅
- **Effort**: Medium (input validation, sanitization)
- **Risk**: Low (well-established patterns)
- **Description**: Eliminate security vulnerabilities for production use
- **Completed**: v0.2.0 (2025-07-19)
- **Tasks**:
  - [x] Add input file validation and sanitization ✅
  - [x] Implement file size limits and timeout controls ✅
  - [x] Add secrets management for API keys ✅
  - [x] Enable secure file handling ✅

### ⚡ P3: Performance Optimization (Score: 8)
- **Impact**: Medium (user experience, scalability)
- **Effort**: Medium (streaming, caching)
- **Risk**: Low (iterative improvements)
- **Description**: Optimize for large documents and batch processing
- **Tasks**:
  - [ ] Implement document streaming for large PDFs
  - [ ] Add memory usage optimization
  - [ ] Benchmark and optimize processing pipeline
  - [ ] Add caching for repeated operations

## Medium-Impact Items (Score: 6-7)

### 📊 P4: Enhanced Observability (Score: 7)
- **Impact**: Medium (debugging, monitoring)
- **Effort**: Low (extend existing metrics)
- **Risk**: Low (non-breaking additions)
- **Description**: Improve logging and metrics for production monitoring
- **Tasks**:
  - [ ] Add structured JSON logging with request IDs
  - [ ] Implement comprehensive metrics (processing time, accuracy)
  - [ ] Add health check endpoints
  - [ ] Create monitoring dashboards

### 🎨 P5: Web Interface Polish (Score: 6)
- **Impact**: Medium (user experience)
- **Effort**: Medium (UI improvements)
- **Risk**: Low (cosmetic changes)
- **Description**: Enhance Streamlit demo for better UX
- **Tasks**:
  - [ ] Add file upload preview and validation
  - [ ] Implement real-time processing status
  - [ ] Add extraction result visualization
  - [ ] Improve error handling and messaging

### 🧪 P6: Test Coverage Enhancement (Score: 6)
- **Impact**: Medium (code quality, confidence)
- **Effort**: Medium (additional test cases)
- **Risk**: Low (testing improvements)
- **Description**: Achieve >90% test coverage with integration tests
- **Tasks**:
  - [ ] Add integration tests for full pipeline
  - [ ] Test error conditions and edge cases
  - [ ] Add performance benchmark tests
  - [ ] Implement contract-type specific tests

## Low-Impact Items (Score: 3-5)

### 📚 P7: Documentation Enhancement (Score: 4)
- **Impact**: Low (developer experience)
- **Effort**: Medium (comprehensive docs)
- **Risk**: Low (documentation only)
- **Description**: Create comprehensive API and deployment docs
- **Tasks**:
  - [ ] Add API documentation with examples
  - [ ] Create deployment guides for different environments
  - [ ] Add troubleshooting guides
  - [ ] Document model configuration options

### 🌐 P8: Multi-format Support (Score: 3)
- **Impact**: Low (nice-to-have features)
- **Effort**: High (new format parsers)
- **Risk**: Medium (format complexity)
- **Description**: Support additional document formats
- **Tasks**:
  - [ ] Add DOCX support
  - [ ] Add image format support (TIFF, BMP)
  - [ ] Add RTF support
  - [ ] Add format auto-detection

## Technical Debt

### 🔧 TD1: Remove Hardcoded Placeholders
- **Location**: extract.py:83
- **Impact**: Blocks core functionality
- **Effort**: High (full implementation required)

### 🔧 TD2: Improve Error Handling
- **Location**: Various CLI modules
- **Impact**: User experience
- **Effort**: Medium (consistent error patterns)

### 🔧 TD3: Configuration Management
- **Location**: Scattered configuration
- **Impact**: Maintainability
- **Effort**: Medium (centralized config)

---

## Scoring Methodology (WSJF)
**Score = (Business Value + Time Criticality + Risk Reduction) / Job Size**

- Business Value: 1-5 (user impact, revenue potential)
- Time Criticality: 1-5 (urgency, market timing)
- Risk Reduction: 1-5 (technical risk mitigation)
- Job Size: 1-5 (effort required, 1=small, 5=very large)

## Next Sprint Selection Criteria
1. Must have Score ≥ 8 OR be blocking other high-value work
2. Consider team capacity and skill alignment
3. Balance quick wins with foundational improvements
4. Prioritize security and core functionality over features