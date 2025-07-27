# ADR-001: Use Streamlit for Web Interface

## Status
Accepted

## Context
We need a web interface for the contract extraction tool that allows users to upload documents and view results. The interface should be simple to develop and maintain while providing a good user experience.

## Decision
We will use Streamlit as the web framework for the user interface.

## Rationale
- **Rapid Development**: Streamlit allows for quick prototyping and development of data science applications
- **Python Native**: Stays within the Python ecosystem, reducing technology complexity
- **Built-in Components**: Provides file upload, charts, and data display components out of the box
- **Minimal Learning Curve**: Easy for Python developers to adopt
- **Good for MVP**: Perfect for getting a working interface quickly

## Alternatives Considered
1. **FastAPI + React**: More scalable but requires frontend expertise
2. **Flask**: More flexible but requires more boilerplate code
3. **Django**: Overkill for this use case

## Consequences
### Positive
- Fast development and iteration
- Easy to maintain and modify
- Good integration with Python data processing libraries
- Built-in caching and session management

### Negative
- Limited customization options for UI/UX
- Less suitable for complex user interactions
- Single-page application limitations
- May need to migrate for advanced features

## Implementation
- Use Streamlit for file upload interface
- Display processing results in structured format
- Implement progress indicators for long-running operations
- Add configuration options through sidebar

## Review Date
To be reviewed in 6 months or when user requirements outgrow Streamlit capabilities.