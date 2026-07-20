"""
SoulSmith Canonical Database Engine (SQLite-first storage abstraction).
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

DB_FILE = os.environ.get(
    "SOULSMITH_DB_FILE",
    os.path.join(os.path.dirname(__file__), "..", "soulsmith_canonical.db"),
)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _column_names(cursor: sqlite3.Cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _add_column_if_missing(
    cursor: sqlite3.Cursor, table: str, column: str, ddl: str
) -> None:
    if column not in _column_names(cursor, table):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def init_database() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS worlds (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tone TEXT NOT NULL,
            canon_version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
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

    # Backwards-compatible migration: preserve legacy dice_read_json while adding canonical columns.
    _add_column_if_missing(
        cursor, "scene_events", "raw_roll_json", "raw_roll_json TEXT"
    )
    _add_column_if_missing(
        cursor, "scene_events", "interpreted_roll_json", "interpreted_roll_json TEXT"
    )
    _add_column_if_missing(
        cursor, "scene_events", "grammar_version", "grammar_version TEXT"
    )
    _add_column_if_missing(
        cursor, "scene_events", "player_intent", "player_intent TEXT"
    )
    _add_column_if_missing(
        cursor, "scene_events", "chosen_approach", "chosen_approach TEXT"
    )
    _add_column_if_missing(
        cursor,
        "scene_events",
        "resource_investment_json",
        "resource_investment_json TEXT",
    )
    _add_column_if_missing(
        cursor,
        "scene_events",
        "deterministic_outcome_json",
        "deterministic_outcome_json TEXT",
    )

    cursor.execute("SELECT COUNT(*) as count FROM worlds")
    if cursor.fetchone()["count"] == 0:
        cursor.execute(
            "INSERT INTO worlds (id, title, tone) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), "Mythic Sanctuary World", "Mystical, Hushed, Resonant"),
        )
    conn.commit()
    conn.close()


def log_canonical_event(
    *,
    soul_name: str,
    outcome_class: str,
    dice_read: dict[str, Any],
    narration: dict[str, Any],
    canon_facts: List[str],
    player_intent: str,
    chosen_approach: str,
    resource_investment: dict[str, Any],
    deterministic_outcome: dict[str, Any],
) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM worlds LIMIT 1")
    world_row = cursor.fetchone()
    world_id = world_row["id"] if world_row else str(uuid.uuid4())

    event_id = str(uuid.uuid4())
    raw_roll = dice_read.get("raw", {})
    interpreted_roll = dice_read.get("interpretation", {})
    grammar_version = dice_read.get("grammar_version")
    cursor.execute(
        """
        INSERT INTO scene_events (
            id, world_id, soul_id, event_type, outcome_class, dice_read_json, narration_json,
            canon_facts_json, raw_roll_json, interpreted_roll_json, grammar_version,
            player_intent, chosen_approach, resource_investment_json, deterministic_outcome_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            event_id,
            world_id,
            soul_name,
            "encounter_resolution",
            outcome_class,
            json.dumps(dice_read),
            json.dumps(narration),
            json.dumps(canon_facts),
            json.dumps(raw_roll),
            json.dumps(interpreted_roll),
            grammar_version,
            player_intent,
            chosen_approach,
            json.dumps(resource_investment),
            json.dumps(deterministic_outcome),
        ),
    )
    conn.commit()
    conn.close()
    return event_id


def _json_or_none(value: Optional[str]) -> Any:
    return json.loads(value) if value else None


def get_all_canonical_events() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scene_events ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "soul_name": row["soul_id"],
            "outcome_class": row["outcome_class"],
            "dice_read": _json_or_none(row["dice_read_json"]),
            "raw_roll": _json_or_none(row["raw_roll_json"]),
            "interpreted_roll": _json_or_none(row["interpreted_roll_json"]),
            "grammar_version": row["grammar_version"],
            "player_intent": row["player_intent"],
            "chosen_approach": row["chosen_approach"],
            "resource_investment": _json_or_none(row["resource_investment_json"]),
            "deterministic_outcome": _json_or_none(row["deterministic_outcome_json"]),
            "narration": _json_or_none(row["narration_json"]),
            "canon_facts": _json_or_none(row["canon_facts_json"]) or [],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
