"""Enhanced Streamlit web application with WebSocket support for real-time collaboration."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
import websockets

# Ensure the src directory is importable
SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from multimodal_contract_extractor import (
    DocumentInfo,
    ExtractionResult,
    extract_from_document,
    get_supported_languages,
    serialize_to_json,
)
from multimodal_contract_extractor.clause_detection import Clause
from multimodal_contract_extractor.websocket_server import (
    ProcessingProgressTracker,
    start_websocket_server,
)

logger = logging.getLogger(__name__)

# WebSocket configuration
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765

# Global state for WebSocket connection
if 'websocket_connection' not in st.session_state:
    st.session_state.websocket_connection = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None
if 'collaboration_messages' not in st.session_state:
    st.session_state.collaboration_messages = []
if 'connected_users' not in st.session_state:
    st.session_state.connected_users = set()


class WebSocketClientManager:
    """Manages WebSocket client connection."""

    def __init__(self):
        self.websocket = None
        self.user_id = st.session_state.user_id
        self.session_id = st.session_state.session_id
        self.running = False

    async def connect(self) -> bool:
        """Connect to WebSocket server."""
        try:
            uri = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}"
            self.websocket = await websockets.connect(uri)

            # Send initial connection message
            connection_message = {
                "user_id": self.user_id,
                "session_id": self.session_id
            }
            await self.websocket.send(json.dumps(connection_message))

            # Wait for confirmation
            response = await self.websocket.recv()
            data = json.loads(response)

            if data.get("type") == "connection_established":
                self.running = True
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False

    async def listen(self) -> None:
        """Listen for WebSocket messages."""
        try:
            while self.running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosedError:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket listen error: {e}")
        finally:
            self.running = False

    async def handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket messages."""
        message_type = data.get("type")

        if message_type == "status_update":
            st.session_state.processing_status = data.get("data")
        elif message_type == "collaboration_message":
            msg_data = data.get("data", {})
            if msg_data.get("type") == "user_joined":
                st.session_state.connected_users.add(msg_data.get("user_id"))
            elif msg_data.get("type") == "user_left":
                st.session_state.connected_users.discard(msg_data.get("user_id"))
            else:
                st.session_state.collaboration_messages.append(msg_data)

    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message through WebSocket."""
        if self.websocket and self.running:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()


def init_websocket_server():
    """Initialize WebSocket server in a separate thread."""
    def run_server():
        try:
            start_websocket_server(WEBSOCKET_HOST, WEBSOCKET_PORT)
            asyncio.get_event_loop().run_forever()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")

    if not hasattr(st.session_state, 'websocket_server_started'):
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        st.session_state.websocket_server_started = True
        time.sleep(1)  # Give server time to start


def create_websocket_client():
    """Create and connect WebSocket client."""
    if st.session_state.websocket_connection is None:
        client = WebSocketClientManager()

        async def connect_and_listen():
            if await client.connect():
                st.session_state.websocket_connection = client
                await client.listen()

        # Run connection in a separate thread
        def run_client():
            asyncio.new_event_loop().run_until_complete(connect_and_listen())

        client_thread = threading.Thread(target=run_client, daemon=True)
        client_thread.start()


def display_processing_status():
    """Display real-time processing status."""
    if st.session_state.processing_status:
        status = st.session_state.processing_status

        with st.container():
            st.subheader("📊 Processing Status")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", status.get("status", "Unknown").title())
            with col2:
                st.metric("Progress", f"{status.get('progress', 0):.1f}%")
            with col3:
                if status.get("clauses_found"):
                    st.metric("Clauses Found", status.get("clauses_found", 0))

            # Progress bar
            progress = status.get("progress", 0) / 100.0
            st.progress(progress)

            # Current operation
            st.text(f"🔄 {status.get('current_operation', 'Processing...')}")

            # Processing time
            if status.get("start_time"):
                elapsed = time.time() - status.get("start_time", 0)
                st.text(f"⏱️ Processing time: {elapsed:.1f}s")


def display_collaboration_panel():
    """Display collaboration features."""
    with st.sidebar:
        st.subheader("👥 Collaboration")

        # Connected users
        user_count = len(st.session_state.connected_users) + 1  # +1 for current user
        st.metric("Connected Users", user_count)

        # Session info
        st.text(f"Session ID: {st.session_state.session_id[:8]}...")
        st.text(f"Your ID: {st.session_state.user_id[:8]}...")

        # Recent messages
        if st.session_state.collaboration_messages:
            st.subheader("💬 Recent Activity")
            for msg in st.session_state.collaboration_messages[-5:]:  # Show last 5 messages
                msg_type = msg.get("type", "")
                user_id = msg.get("user_id", "")[:8]
                timestamp = msg.get("timestamp", 0)
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))

                if msg_type == "comment":
                    st.text(f"💬 {time_str} - {user_id}: {msg.get('data', {}).get('text', '')}")
                elif msg_type == "clause_review":
                    action = msg.get('data', {}).get('action', '')
                    st.text(f"✅ {time_str} - {user_id}: {action} clause")


def enhanced_clause_display(clauses: List[Dict[str, Any]]):
    """Enhanced clause display with collaboration features."""
    st.subheader("📋 Extracted Clauses")

    for i, clause in enumerate(clauses):
        with st.expander(f"{clause['type'].replace('_', ' ').title()} (Page {clause['page']})"):
            # Clause content
            st.text_area("Content", clause['text'], height=100, key=f"clause_text_{i}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence", f"{clause.get('confidence', 0):.2f}")
            with col2:
                if clause.get('legal_significance'):
                    significance_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    significance = clause.get('legal_significance', 'low')
                    st.metric("Legal Significance",
                             f"{significance_colors.get(significance, '⚪')} {significance.title()}")
            with col3:
                if clause.get('advanced_confidence'):
                    st.metric("Advanced Confidence", f"{clause.get('advanced_confidence', 0):.3f}")

            # Key terms
            if clause.get('key_terms'):
                st.write("**Key Terms:**")
                st.write(", ".join(clause['key_terms']))

            # Contract types relevance
            if clause.get('contract_types'):
                st.write("**Relevant Contract Types:**")
                st.write(", ".join(clause['contract_types']))

            # Collaboration features
            st.subheader("🤝 Collaboration")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve", key=f"approve_{i}"):
                    send_clause_review(clause['id'], "approved", "")
            with col2:
                if st.button("❌ Reject", key=f"reject_{i}"):
                    send_clause_review(clause['id'], "rejected", "")
            with col3:
                if st.button("📝 Comment", key=f"comment_{i}"):
                    st.session_state[f"show_comment_{i}"] = True

            # Comment input
            if st.session_state.get(f"show_comment_{i}"):
                comment = st.text_input("Add comment:", key=f"comment_input_{i}")
                if st.button("Send Comment", key=f"send_comment_{i}"):
                    if comment:
                        send_comment(comment, clause['id'], clause['page'])
                        st.session_state[f"show_comment_{i}"] = False
                        st.rerun()


def send_comment(text: str, clause_id: str, page: int):
    """Send a comment through WebSocket."""
    if st.session_state.websocket_connection:
        message = {
            "type": "comment",
            "text": text,
            "clause_id": clause_id,
            "page": page
        }
        # Note: In a real implementation, you would need to handle async/await properly
        # This is a simplified version for demonstration
        asyncio.create_task(st.session_state.websocket_connection.send_message(message))


def send_clause_review(clause_id: str, action: str, comment: str):
    """Send clause review through WebSocket."""
    if st.session_state.websocket_connection:
        message = {
            "type": "clause_review",
            "clause_id": clause_id,
            "action": action,
            "comment": comment
        }
        asyncio.create_task(st.session_state.websocket_connection.send_message(message))


async def process_document_with_tracking(uploaded_file, language_code,
                                      enable_advanced, enable_adaptive):
    """Process document with real-time progress tracking."""
    from web_app import TempFileManager

    # Create progress tracker
    tracker = ProcessingProgressTracker(
        st.session_state.session_id,
        uploaded_file.name
    )

    try:
        await tracker.update_progress(10, "Preparing document...")

        with TempFileManager(uploaded_file) as tmp_path:
            await tracker.update_progress(20, "Starting extraction...")

            # Perform document extraction
            extraction_result = extract_from_document(
                tmp_path,
                language_code=language_code,
                enable_advanced_classification=enable_advanced,
                enable_adaptive_processing=enable_adaptive
            )

            await tracker.update_progress(90, "Finalizing results...")

            clauses_found = len(extraction_result.get("clauses", []))
            total_pages = extraction_result.get("document_info", {}).get("pages", 0)
            processing_method = extraction_result.get("metadata", {}).get("processing_method", "")

            await tracker.set_completed(clauses_found, total_pages, processing_method)

            return extraction_result

    except Exception as e:
        await tracker.set_error(str(e))
        raise


def main():
    """Enhanced main Streamlit application."""
    st.set_page_config(
        page_title="Contract Extractor - Enhanced",
        page_icon="📄",
        layout="wide"
    )

    # Initialize WebSocket server and client
    init_websocket_server()
    create_websocket_client()

    st.title("📄 Multimodal Contract Extractor - Enhanced")
    st.markdown("**Real-time collaboration and advanced processing**")

    # Display collaboration panel
    display_collaboration_panel()

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # File upload
        uploaded_file = st.file_uploader(
            "Upload contract document",
            type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
            help="Supported formats: PDF, PNG, JPEG, TIFF, BMP"
        )

        if uploaded_file is None:
            st.info("👆 Please upload a document to begin processing.")
            return

        # Processing options
        with st.expander("⚙️ Processing Options", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                # Language selection
                supported_langs = get_supported_languages()
                lang_options = {
                    "Auto-detect": None,
                    **{config.name: code for code, config in supported_langs.items()}
                }
                selected_lang = st.selectbox("Document Language", options=list(lang_options.keys()))
                language_code = lang_options[selected_lang]

            with col2:
                enable_advanced = st.checkbox("Advanced Classification", value=True,
                                           help="Enable advanced clause classification for specialized contracts")
                enable_adaptive = st.checkbox("Adaptive Processing", value=True,
                                           help="Enable adaptive processing for low-confidence extractions")

        # Process button
        if st.button("🚀 Process Document", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    # Process with async tracking
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    extraction_result = loop.run_until_complete(
                        process_document_with_tracking(
                            uploaded_file, language_code, enable_advanced, enable_adaptive
                        )
                    )

                    st.session_state.extraction_result = extraction_result
                    st.success("✅ Document processed successfully!")

                except Exception as e:
                    st.error(f"❌ Error processing document: {e}")
                    logger.exception("Document processing failed")

    with col2:
        # Display processing status
        display_processing_status()

    # Display results
    if hasattr(st.session_state, 'extraction_result'):
        result = st.session_state.extraction_result

        # Document summary
        doc_info = result.get("document_info", {})
        st.subheader("📊 Document Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pages", doc_info.get("pages", 0))
        with col2:
            st.metric("Processing Time", f"{doc_info.get('processing_time', 0):.1f}s")
        with col3:
            st.metric("Overall Confidence", f"{doc_info.get('overall_confidence', 0):.2f}")
        with col4:
            st.metric("Document Type", doc_info.get("document_type", "Unknown").replace("_", " ").title())

        # Contract type scores (if available)
        if "contract_type_scores" in doc_info:
            st.subheader("🎯 Contract Type Analysis")
            scores = doc_info["contract_type_scores"]

            # Create a bar chart of contract type scores
            import pandas as pd
            df = pd.DataFrame(list(scores.items()), columns=['Contract Type', 'Confidence'])
            df['Contract Type'] = df['Contract Type'].str.replace('_', ' ').str.title()
            st.bar_chart(df.set_index('Contract Type'))

        # Enhanced clause display
        clauses = result.get("clauses", [])
        enhanced_clause_display(clauses)

        # Export options
        st.subheader("📥 Export Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Download JSON"):
                json_data = serialize_to_json(
                    ExtractionResult(
                        document_info=DocumentInfo(
                            filename=doc_info["filename"],
                            pages=doc_info["pages"],
                            processing_time=doc_info["processing_time"],
                            confidence=doc_info["overall_confidence"],
                        ),
                        clauses=[
                            Clause(
                                type=clause["type"],
                                text=clause["text"],
                                page=clause["page"],
                                coordinates=clause["coordinates"],
                            )
                            for clause in clauses
                        ]
                    ),
                    pretty=True
                )
                st.download_button(
                    "Download JSON",
                    json_data,
                    file_name=f"{uploaded_file.name}_extraction.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()
