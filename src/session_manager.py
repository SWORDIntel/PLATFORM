#!/usr/bin/env python3
"""
Session Management for Self-Coding Agent
Handles session persistence, resume, and extended context management.
"""

import os
import json
import pickle
import zstandard as zstd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


@dataclass
class SessionMetadata:
    """Metadata for a coding session."""
    session_id: str
    created_at: float
    last_active: float
    workspace_path: str
    task_count: int
    file_count: int
    context_size_tokens: int
    action_count: int
    conversation_length: int
    model_name: str


class SessionManager:
    """
    Manages coding session persistence and resume.

    Features:
    - Auto-save sessions every N minutes
    - Resume from last session
    - Session compression for storage efficiency
    - Extended context via disk buffering
    - Knowledge graph persistence
    """

    def __init__(self, save_directory: str = "/tmp/sword_sessions",
                 auto_save_interval: int = 300,
                 max_sessions: int = 10):
        self.save_directory = Path(save_directory)
        self.auto_save_interval = auto_save_interval
        self.max_sessions = max_sessions

        # Create directory
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def generate_session_id(self, workspace_path: str) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().isoformat()
        unique_str = f"{workspace_path}_{timestamp}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def save_session(self, agent, compress: bool = True) -> str:
        """
        Save current agent session.

        Args:
            agent: SelfCodingAgent instance
            compress: Whether to compress session data

        Returns:
            Session ID
        """
        # Generate session ID
        session_id = self.generate_session_id(agent.workspace_root)

        # Collect session data
        session_data = {
            "conversation": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in agent.conversation
            ],
            "tasks": [
                {
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority,
                    "result": task.result,
                    "error": task.error,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at
                }
                for task in agent.tasks
            ],
            "action_history": [
                {
                    "action_type": action.action_type,
                    "parameters": action.parameters,
                    "result": action.result,
                    "timestamp": action.timestamp,
                    "reasoning": action.reasoning
                }
                for action in agent.action_history
            ],
            "context_memory": agent.context_memory,
            "workspace_root": agent.workspace_root,
            "model_name": agent.model_name
        }

        # Create metadata
        metadata = SessionMetadata(
            session_id=session_id,
            created_at=datetime.now().timestamp(),
            last_active=datetime.now().timestamp(),
            workspace_path=agent.workspace_root,
            task_count=len(agent.tasks),
            file_count=0,  # Could track open files
            context_size_tokens=len(str(session_data)),  # Approximate
            action_count=len(agent.action_history),
            conversation_length=len(agent.conversation),
            model_name=agent.model_name
        )

        # Save metadata
        metadata_path = self.save_directory / f"{session_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)

        # Save session data
        data_path = self.save_directory / f"{session_id}_data.pkl"

        if compress:
            # Compress with zstandard
            pickled = pickle.dumps(session_data)
            compressed = zstd.ZstdCompressor(level=3).compress(pickled)

            with open(data_path, 'wb') as f:
                f.write(compressed)
        else:
            with open(data_path, 'wb') as f:
                pickle.dump(session_data, f)

        # Clean up old sessions
        self._cleanup_old_sessions()

        return session_id

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data.

        Args:
            session_id: Session ID to load

        Returns:
            Session data dict or None if not found
        """
        data_path = self.save_directory / f"{session_id}_data.pkl"

        if not data_path.exists():
            return None

        try:
            with open(data_path, 'rb') as f:
                data = f.read()

            # Try decompression
            try:
                decompressed = zstd.ZstdDecompressor().decompress(data)
                session_data = pickle.loads(decompressed)
            except:
                # Not compressed
                session_data = pickle.loads(data)

            return session_data

        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def list_sessions(self, limit: int = None) -> List[SessionMetadata]:
        """
        List available sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of SessionMetadata objects, sorted by last_active
        """
        sessions = []

        for metadata_file in self.save_directory.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                    metadata = SessionMetadata(**metadata_dict)
                    sessions.append(metadata)
            except Exception as e:
                print(f"Error loading metadata {metadata_file}: {e}")

        # Sort by last_active (most recent first)
        sessions.sort(key=lambda s: s.last_active, reverse=True)

        if limit:
            sessions = sessions[:limit]

        return sessions

    def restore_session(self, agent, session_id: str) -> bool:
        """
        Restore session to agent.

        Args:
            agent: SelfCodingAgent instance
            session_id: Session ID to restore

        Returns:
            True if successful
        """
        session_data = self.load_session(session_id)

        if not session_data:
            return False

        try:
            # Restore conversation
            from .self_coder import ConversationMessage
            agent.conversation = [
                ConversationMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg["timestamp"]
                )
                for msg in session_data.get("conversation", [])
            ]

            # Restore tasks
            from .self_coder import CodingTask, TaskStatus
            agent.tasks = [
                CodingTask(
                    description=task["description"],
                    status=TaskStatus(task["status"]),
                    priority=task["priority"],
                    result=task.get("result"),
                    error=task.get("error"),
                    created_at=task["created_at"],
                    completed_at=task.get("completed_at")
                )
                for task in session_data.get("tasks", [])
            ]

            # Restore action history
            from .self_coder import AgentAction
            agent.action_history = [
                AgentAction(
                    action_type=action["action_type"],
                    parameters=action["parameters"],
                    result=action.get("result"),
                    timestamp=action["timestamp"],
                    reasoning=action.get("reasoning", "")
                )
                for action in session_data.get("action_history", [])
            ]

            # Restore context memory
            agent.context_memory = session_data.get("context_memory", {})

            return True

        except Exception as e:
            print(f"Error restoring session: {e}")
            return False

    def _cleanup_old_sessions(self):
        """Remove old sessions beyond max_sessions limit."""
        sessions = self.list_sessions()

        if len(sessions) > self.max_sessions:
            # Remove oldest sessions
            sessions_to_remove = sessions[self.max_sessions:]

            for session in sessions_to_remove:
                data_path = self.save_directory / f"{session.session_id}_data.pkl"
                metadata_path = self.save_directory / f"{session.session_id}_metadata.json"

                try:
                    data_path.unlink(missing_ok=True)
                    metadata_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Error removing old session {session.session_id}: {e}")

    def get_session_size(self, session_id: str) -> int:
        """Get session file size in bytes."""
        data_path = self.save_directory / f"{session_id}_data.pkl"
        if data_path.exists():
            return data_path.stat().st_size
        return 0

    def export_session(self, session_id: str, export_path: str):
        """Export session to external file."""
        session_data = self.load_session(session_id)

        if session_data:
            with open(export_path, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)

    def import_session(self, import_path: str) -> Optional[str]:
        """Import session from external file."""
        try:
            with open(import_path, 'r') as f:
                session_data = json.load(f)

            # Generate new session ID
            session_id = self.generate_session_id(
                session_data.get("workspace_root", "unknown")
            )

            # Save as new session
            data_path = self.save_directory / f"{session_id}_data.pkl"
            compressed = zstd.ZstdCompressor(level=3).compress(
                pickle.dumps(session_data)
            )

            with open(data_path, 'wb') as f:
                f.write(compressed)

            # Create metadata
            metadata = SessionMetadata(
                session_id=session_id,
                created_at=datetime.now().timestamp(),
                last_active=datetime.now().timestamp(),
                workspace_path=session_data.get("workspace_root", ""),
                task_count=len(session_data.get("tasks", [])),
                file_count=0,
                context_size_tokens=len(str(session_data)),
                action_count=len(session_data.get("action_history", [])),
                conversation_length=len(session_data.get("conversation", [])),
                model_name=session_data.get("model_name", "unknown")
            )

            metadata_path = self.save_directory / f"{session_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)

            return session_id

        except Exception as e:
            print(f"Error importing session: {e}")
            return None
