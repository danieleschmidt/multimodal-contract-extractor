from __future__ import annotations

from pathlib import Path
import sys


def main() -> None:
    import streamlit as st  # Lazy import so tests don't require streamlit
    from multimodal_contract_extractor import (
        load_document,
        detect_clauses,
        DocumentInfo,
        ExtractionResult,
        serialize_to_json,
    )

    st.title("Multimodal Contract Extractor")
    uploaded = st.file_uploader("Upload contract file")
    if uploaded is None:
        st.info("Please upload a PDF or image document.")
        return

    tmp_path = Path("uploaded_contract")
    tmp_path.write_bytes(uploaded.read())
    document = load_document(tmp_path)
    clauses = detect_clauses(document)
    info = DocumentInfo(
        filename=uploaded.name,
        pages=len(document.pages),
        processing_time=0.0,
        confidence=1.0,
    )
    result = ExtractionResult(document_info=info, clauses=clauses)
    st.json(serialize_to_json(result, pretty=True))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
