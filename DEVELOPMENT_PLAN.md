# 📝 Project Vision

> A short 2–3 sentence description of what this repo does, for whom, and why.

# 📅 12-Week Roadmap

## I1: Foundation & Security
- **Themes**: Security, Developer UX
- **Goals / Epics**
  - Harden input handling and remove placeholders
  - Establish CI reliability and linting hooks
- **Definition of Done**
  - No hardcoded temp files; validation on all CLI paths
  - CI passes on clean clone

## I2: Performance & Observability
- **Themes**: Performance, Observability
- **Goals / Epics**
  - Improve document streaming efficiency
  - Add structured logging and basic metrics
- **Definition of Done**
  - Stream loading uses chunked processing
  - Logs emit JSON with timestamps; metrics exported

## I3: Advanced Features & UX
- **Themes**: ML Integration, UX
- **Goals / Epics**
  - Integrate OCR/VLM models for clause extraction
  - Polish Streamlit demo and docs
- **Definition of Done**
  - Models configurable via environment variables
  - Web demo showcases extraction end‑to‑end

# ✅ Epic & Task Checklist

### 🔒 Increment 1: Security & Refactoring
- [x] [EPIC] Eliminate hardcoded paths
  - [x] Validate user input and sanitize filenames
  - [x] Add unit tests for CLI argument errors
- [x] [EPIC] Improve CI stability
  - [x] Add `ruff` and `bandit` pre-commit hooks
  - [x] Enable parallel test execution

### ⚡️ Increment 2: Performance & Observability
- [ ] [EPIC] Optimize PDF streaming
  - [ ] Benchmark chunk sizes for large files
  - [ ] Document memory usage impact
- [ ] [EPIC] Add logging & metrics
  - [ ] JSON logs with request IDs
  - [ ] Basic Prometheus metrics

### 🚀 Increment 3: Features & UX
- [ ] [EPIC] Integrate OCR/VLM models
  - [ ] Hook up Tesseract or PaddleOCR
  - [ ] Call vision-language model for clause ranking
- [ ] [EPIC] Enhance web interface
  - [ ] File upload preview and status messages
  - [ ] Update README examples

# ⚠️ Risks & Mitigation
- Dependency supply chain vulnerabilities → Pin versions and monitor CVEs
- OCR accuracy on handwritten docs → Provide manual review workflow
- Large PDF memory use → Stream pages and set file size limits
- CI flakiness → Use containerized test environment

# 📊 KPIs & Metrics
- [ ] >85% test coverage
- [ ] <15 min CI pipeline time
- [ ] <5% error rate on core service
- [ ] 100% secrets loaded from vault/env

# 👥 Ownership & Roles
- Security tasks — **DevOps**
- Performance optimizations — **Backend**
- Web app and UX — **Frontend**/ML
