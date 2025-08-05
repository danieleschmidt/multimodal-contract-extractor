"""WebSocket server for real-time collaboration and status updates."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatus:
    """Status of document processing."""

    session_id: str
    document_name: str
    status: str  # 'pending', 'processing', 'completed', 'error'
    progress: float  # 0.0 to 100.0
    current_operation: str
    start_time: float
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    clauses_found: int = 0
    total_pages: int = 0
    processing_method: str = ""


@dataclass
class CollaborationMessage:
    """Message for collaboration features."""

    type: str  # 'status_update', 'clause_review', 'user_joined', 'user_left', 'comment'
    session_id: str
    user_id: str
    timestamp: float
    data: Dict[str, Any]


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.session_users: Dict[str, Set[str]] = {}  # session_id -> set of user_ids
        self.processing_statuses: Dict[str, ProcessingStatus] = {}
        self.session_messages: Dict[str, List[CollaborationMessage]] = {}

    async def register_connection(self, websocket: websockets.WebSocketServerProtocol,
                                user_id: str, session_id: str) -> None:
        """Register a new WebSocket connection."""
        connection_id = f"{user_id}_{session_id}_{int(time.time())}"
        self.connections[connection_id] = websocket

        # Track user-session mapping
        self.user_sessions[user_id] = session_id

        if session_id not in self.session_users:
            self.session_users[session_id] = set()
        self.session_users[session_id].add(user_id)

        if session_id not in self.session_messages:
            self.session_messages[session_id] = []

        logger.info(f"User {user_id} joined session {session_id}")

        # Notify other users in the session
        await self.broadcast_to_session(session_id, CollaborationMessage(
            type="user_joined",
            session_id=session_id,
            user_id=user_id,
            timestamp=time.time(),
            data={"user_count": len(self.session_users[session_id])}
        ), exclude_user=user_id)

        # Send current status to new user
        if session_id in self.processing_statuses:
            await self.send_to_user(user_id, {
                "type": "status_update",
                "data": asdict(self.processing_statuses[session_id])
            })

        # Send recent messages to new user
        recent_messages = self.session_messages[session_id][-10:]  # Last 10 messages
        for message in recent_messages:
            await self.send_to_user(user_id, {
                "type": "collaboration_message",
                "data": asdict(message)
            })

    async def unregister_connection(self, user_id: str, session_id: str) -> None:
        """Unregister a WebSocket connection."""
        # Remove from connections
        connection_id = next((cid for cid, _ in self.connections.items()
                            if cid.startswith(f"{user_id}_{session_id}")), None)
        if connection_id:
            del self.connections[connection_id]

        # Remove from session tracking
        if session_id in self.session_users and user_id in self.session_users[session_id]:
            self.session_users[session_id].remove(user_id)

            # Clean up empty sessions
            if not self.session_users[session_id]:
                del self.session_users[session_id]
                if session_id in self.session_messages:
                    del self.session_messages[session_id]
                if session_id in self.processing_statuses:
                    del self.processing_statuses[session_id]

        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

        logger.info(f"User {user_id} left session {session_id}")

        # Notify other users in the session
        if session_id in self.session_users:
            await self.broadcast_to_session(session_id, CollaborationMessage(
                type="user_left",
                session_id=session_id,
                user_id=user_id,
                timestamp=time.time(),
                data={"user_count": len(self.session_users[session_id])}
            ))

    async def update_processing_status(self, session_id: str, status: ProcessingStatus) -> None:
        """Update processing status for a session."""
        self.processing_statuses[session_id] = status

        # Broadcast status to all users in the session
        await self.broadcast_to_session(session_id, CollaborationMessage(
            type="status_update",
            session_id=session_id,
            user_id="system",
            timestamp=time.time(),
            data=asdict(status)
        ))

    async def add_collaboration_message(self, message: CollaborationMessage) -> None:
        """Add a collaboration message and broadcast it."""
        session_id = message.session_id

        if session_id not in self.session_messages:
            self.session_messages[session_id] = []

        self.session_messages[session_id].append(message)

        # Keep only last 100 messages to prevent memory issues
        if len(self.session_messages[session_id]) > 100:
            self.session_messages[session_id] = self.session_messages[session_id][-100:]

        # Broadcast to all users in the session
        await self.broadcast_to_session(session_id, message)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific user."""
        if user_id not in self.user_sessions:
            return

        session_id = self.user_sessions[user_id]
        connection_id = next((cid for cid in self.connections.keys()
                            if cid.startswith(f"{user_id}_{session_id}")), None)

        if connection_id and connection_id in self.connections:
            try:
                await self.connections[connection_id].send(json.dumps(message))
            except (ConnectionClosedError, ConnectionClosedOK):
                # Connection closed, clean up
                await self.unregister_connection(user_id, session_id)

    async def broadcast_to_session(self, session_id: str, message: CollaborationMessage,
                                 exclude_user: Optional[str] = None) -> None:
        """Broadcast a message to all users in a session."""
        if session_id not in self.session_users:
            return

        message_data = {
            "type": "collaboration_message",
            "data": asdict(message)
        }

        for user_id in self.session_users[session_id]:
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, message_data)

    def get_session_status(self, session_id: str) -> Optional[ProcessingStatus]:
        """Get current processing status for a session."""
        return self.processing_statuses.get(session_id)

    def get_session_users(self, session_id: str) -> Set[str]:
        """Get list of users in a session."""
        return self.session_users.get(session_id, set())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def websocket_handler(websocket: websockets.WebSocketServerProtocol, path: str) -> None:
    """Handle WebSocket connections."""
    user_id = None
    session_id = None

    try:
        # Wait for initial connection message
        initial_message = await websocket.recv()
        connection_data = json.loads(initial_message)

        user_id = connection_data.get("user_id")
        session_id = connection_data.get("session_id")

        if not user_id or not session_id:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing user_id or session_id"
            }))
            return

        # Register the connection
        await websocket_manager.register_connection(websocket, user_id, session_id)

        # Send connection confirmation
        await websocket.send(json.dumps({
            "type": "connection_established",
            "user_id": user_id,
            "session_id": session_id
        }))

        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                await process_websocket_message(data, user_id, session_id)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {user_id}: {message}")
            except Exception as e:
                logger.exception(f"Error processing message from {user_id}: {e}")

    except (ConnectionClosedError, ConnectionClosedOK):
        logger.info(f"WebSocket connection closed for user {user_id}")
    except Exception as e:
        logger.exception(f"WebSocket handler error: {e}")
    finally:
        if user_id and session_id:
            await websocket_manager.unregister_connection(user_id, session_id)


async def process_websocket_message(data: Dict[str, Any], user_id: str, session_id: str) -> None:
    """Process incoming WebSocket messages."""
    message_type = data.get("type")

    if message_type == "comment":
        # Handle user comments/collaboration
        comment_message = CollaborationMessage(
            type="comment",
            session_id=session_id,
            user_id=user_id,
            timestamp=time.time(),
            data={
                "text": data.get("text", ""),
                "clause_id": data.get("clause_id"),
                "page": data.get("page")
            }
        )
        await websocket_manager.add_collaboration_message(comment_message)

    elif message_type == "clause_review":
        # Handle clause review/approval
        review_message = CollaborationMessage(
            type="clause_review",
            session_id=session_id,
            user_id=user_id,
            timestamp=time.time(),
            data={
                "clause_id": data.get("clause_id"),
                "action": data.get("action"),  # 'approved', 'rejected', 'modified'
                "comment": data.get("comment", "")
            }
        )
        await websocket_manager.add_collaboration_message(review_message)

    elif message_type == "request_status":
        # Send current status to user
        status = websocket_manager.get_session_status(session_id)
        if status:
            await websocket_manager.send_to_user(user_id, {
                "type": "status_update",
                "data": asdict(status)
            })


class ProcessingProgressTracker:
    """Tracks processing progress and sends real-time updates."""

    def __init__(self, session_id: str, document_name: str):
        self.session_id = session_id
        self.document_name = document_name
        self.start_time = time.time()

        # Initialize status
        self.status = ProcessingStatus(
            session_id=session_id,
            document_name=document_name,
            status="pending",
            progress=0.0,
            current_operation="Initializing...",
            start_time=self.start_time
        )

    async def update_progress(self, progress: float, operation: str) -> None:
        """Update processing progress."""
        self.status.progress = progress
        self.status.current_operation = operation
        self.status.status = "processing"

        await websocket_manager.update_processing_status(self.session_id, self.status)

    async def set_completed(self, clauses_found: int, total_pages: int,
                          processing_method: str) -> None:
        """Mark processing as completed."""
        self.status.status = "completed"
        self.status.progress = 100.0
        self.status.current_operation = "Completed"
        self.status.end_time = time.time()
        self.status.clauses_found = clauses_found
        self.status.total_pages = total_pages
        self.status.processing_method = processing_method

        await websocket_manager.update_processing_status(self.session_id, self.status)

    async def set_error(self, error_message: str) -> None:
        """Mark processing as failed."""
        self.status.status = "error"
        self.status.current_operation = f"Error: {error_message}"
        self.status.end_time = time.time()
        self.status.error_message = error_message

        await websocket_manager.update_processing_status(self.session_id, self.status)


def start_websocket_server(host: str = "localhost", port: int = 8765) -> None:
    """Start the WebSocket server."""
    logger.info(f"Starting WebSocket server on {host}:{port}")

    start_server = websockets.serve(websocket_handler, host, port)
    asyncio.get_event_loop().run_until_complete(start_server)
    logger.info("WebSocket server started")


async def send_processing_update(session_id: str, progress: float, operation: str) -> None:
    """Send a processing update (convenience function)."""
    if session_id in websocket_manager.processing_statuses:
        status = websocket_manager.processing_statuses[session_id]
        status.progress = progress
        status.current_operation = operation
        status.status = "processing"
        await websocket_manager.update_processing_status(session_id, status)


# Export functions for easy access
__all__ = [
    "WebSocketManager",
    "ProcessingStatus",
    "CollaborationMessage",
    "ProcessingProgressTracker",
    "websocket_manager",
    "start_websocket_server",
    "send_processing_update",
]
