"""
SoulSmith Canonical Database Engine (SQLite / PostgreSQL abstraction)
Stores worlds, souls, scene events, and immutable chronicle facts.
"""

import sqlite3
import json
import uuid
import os
from typing import Dict, List, Optional
from pydantic import BaseModel

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "soulsmith_canonical.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create worlds table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS worlds (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tone TEXT NOT NULL,
            canon_version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create souls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS souls (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL,
            soul_name TEXT NOT NULL,
            calling TEXT NOT NULL,
            origin TEXT NOT NULL,
            sheet_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create scene_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scene_events (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL,
            soul_id TEXT,
            event_type TEXT NOT NULL,
            outcome_class TEXT NOT NULL,
            dice_read_json TEXT NOT NULL,
            narration_json TEXT NOT NULL,
            canon_facts_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create default world if none exists
    cursor.execute("SELECT COUNT(*) as count FROM worlds")
    if cursor.fetchone()["count"] == 0:
        world_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO worlds (id, title, tone) VALUES (?, ?, ?)",
            (world_id, "Mythic Sanctuary World", "Mystical, Hushed, Resonant")
        )

    conn.commit()
    conn.close()

def log_canonical_event(soul_name: str, outcome_class: str, dice_read: dict, narration: dict, canon_facts: List[str]) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM worlds LIMIT 1")
    world_row = cursor.fetchone()
    world_id = world_row["id"] if world_row else str(uuid.uuid4())

    event_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO scene_events (id, world_id, soul_id, event_type, outcome_class, dice_read_json, narration_json, canon_facts_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        world_id,
        soul_name,
        "encounter_resolution",
        outcome_class,
        json.dumps(dice_read),
        json.dumps(narration),
        json.dumps(canon_facts)
    ))

    conn.commit()
    conn.close()
    return event_id

def get_all_canonical_events() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scene_events ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        events.append({
            "id": row["id"],
            "soul_name": row["soul_id"],
            "outcome_class": row["outcome_class"],
            "dice_read": json.loads(row["dice_read_json"]),
            "narration": json.loads(row["narration_json"]),
            "canon_facts": json.loads(row["canon_facts_json"]),
            "created_at": row["created_at"]
        })
    return events
