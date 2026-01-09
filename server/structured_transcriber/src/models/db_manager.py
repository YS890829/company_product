"""
SQLite Database Manager

This module provides database operations for meeting transcriptions.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatabaseManager:
    """Manager for SQLite database operations"""

    def __init__(self, db_path: str = "transcriptions.db"):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None

        if not Path(db_path).exists():
            raise ValueError(f"Database not found at {db_path}")

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        print(f"✅ SQLite DB connected: {db_path}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_all_meetings(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all meetings with summary information

        Args:
            limit: Maximum number of meetings to return
            offset: Number of meetings to skip

        Returns:
            List of meeting dictionaries
        """
        cursor = self.conn.cursor()

        # Get meetings (simplified query based on actual schema)
        query = """
        SELECT
            meeting_id,
            structured_file_path as file_name,
            created_at,
            0 as total_segments,
            0 as total_speakers,
            NULL as duration_minutes
        FROM meetings
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """

        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get meeting metadata

        Args:
            meeting_id: Meeting ID to retrieve

        Returns:
            Meeting dictionary or None if not found
        """
        cursor = self.conn.cursor()

        query = """
        SELECT
            meeting_id,
            structured_file_path as file_name,
            created_at
        FROM meetings
        WHERE meeting_id = ?
        """

        cursor.execute(query, (meeting_id,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def get_meeting_segments(self, meeting_id: str) -> List[Dict[str, Any]]:
        """
        Get all segments for a meeting

        Note: This loads the structured JSON file directly
        since segments are not stored in the database

        Args:
            meeting_id: Meeting ID

        Returns:
            List of segment dictionaries
        """
        import json

        # Get meeting file path
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return []

        file_path = meeting.get('file_name')
        if not file_path or not Path(file_path).exists():
            return []

        # Load segments from JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            segments = data.get('segments', [])

            # Format segments
            formatted_segments = []
            for i, seg in enumerate(segments):
                formatted_segments.append({
                    'segment_id': f"{meeting_id}_seg_{i}",
                    'speaker': seg.get('speaker', 'unknown'),
                    'text': seg.get('text', ''),
                    'timestamp': seg.get('timestamp'),
                    'created_at': meeting.get('created_at')
                })

            return formatted_segments
        except Exception as e:
            print(f"Error loading segments: {e}")
            return []

    def get_meeting_participants(self, meeting_id: str) -> List[Dict[str, Any]]:
        """
        Get all participants for a meeting

        Args:
            meeting_id: Meeting ID

        Returns:
            List of participant dictionaries
        """
        cursor = self.conn.cursor()

        query = """
        SELECT
            p.participant_name as name
        FROM participant_meetings pm
        JOIN participants p ON pm.participant_id = p.participant_id
        WHERE pm.meeting_id = ?
        """

        cursor.execute(query, (meeting_id,))
        rows = cursor.fetchall()

        # If no results, extract from segments
        if not rows:
            segments = self.get_meeting_segments(meeting_id)
            unique_speakers = set(seg['speaker'] for seg in segments)
            return [{'name': speaker} for speaker in unique_speakers]

        return [dict(row) for row in rows]
