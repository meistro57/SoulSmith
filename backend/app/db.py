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


_initialized_files: set[str] = set()


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    if DB_FILE not in _initialized_files:
        _initialized_files.add(DB_FILE)
        _run_init_schema(conn)
    return conn


def _column_names(cursor: sqlite3.Cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _add_column_if_missing(
    cursor: sqlite3.Cursor, table: str, column: str, ddl: str
) -> None:
    if column not in _column_names(cursor, table):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def _run_init_schema(conn: sqlite3.Connection) -> None:
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seeds (
            id TEXT PRIMARY KEY,
            world_id TEXT NOT NULL,
            soul_id TEXT,
            symbol TEXT NOT NULL,
            thread_type TEXT NOT NULL,
            stage TEXT NOT NULL DEFAULT 'planted',
            echo_count INTEGER DEFAULT 1,
            narrative_context TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS open_questions (
            id TEXT PRIMARY KEY,
            seed_id TEXT,
            question_text TEXT NOT NULL,
            stakes TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            evidence_event_ids_json TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_threads (
            id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            name TEXT NOT NULL,
            thread_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            evidence_count INTEGER DEFAULT 1,
            evidence_summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_events (
            id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            choice_made TEXT NOT NULL,
            relic_awakened_id TEXT,
            transformation_summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) as count FROM worlds")
    if cursor.fetchone()["count"] == 0:
        cursor.execute(
            "INSERT INTO worlds (id, title, tone) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), "Mythic Sanctuary World", "Mystical, Hushed, Resonant"),
        )
    conn.commit()


def init_database() -> None:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    _run_init_schema(conn)
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


# Curiosity & Thread Database Helpers


def plant_or_echo_seed(
    *,
    symbol: str,
    thread_type: str,
    narrative_context: str,
    soul_id: Optional[str] = "Unbound Soul",
    initial_question: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM worlds LIMIT 1")
    world_row = cursor.fetchone()
    world_id = world_row["id"] if world_row else "default"

    cursor.execute(
        "SELECT * FROM seeds WHERE symbol = ? AND stage != 'retired'", (symbol,)
    )
    existing = cursor.fetchone()

    if existing:
        new_count = existing["echo_count"] + 1
        new_stage = (
            "recognized"
            if new_count >= 3
            else ("echoed" if new_count >= 2 else existing["stage"])
        )
        cursor.execute(
            """
            UPDATE seeds
            SET echo_count = ?, stage = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (new_count, new_stage, existing["id"]),
        )
        seed_id = existing["id"]
    else:
        seed_id = str(uuid.uuid4())
        new_stage = "planted"
        new_count = 1
        cursor.execute(
            """
            INSERT INTO seeds (id, world_id, soul_id, symbol, thread_type, stage, echo_count, narrative_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                seed_id,
                world_id,
                soul_id,
                symbol,
                thread_type,
                new_stage,
                new_count,
                narrative_context,
            ),
        )

    # If an initial question is provided, insert an open question
    if initial_question:
        q_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO open_questions (id, seed_id, question_text, stakes, status, evidence_event_ids_json)
            VALUES (?, ?, ?, ?, 'open', '[]')
        """,
            (
                q_id,
                seed_id,
                initial_question,
                f"Tied to recurring symbol '{symbol}'",
            ),
        )

    # Upsert local thread
    cursor.execute(
        "SELECT * FROM local_threads WHERE soul_id = ? AND thread_type = ? AND status != 'integrated'",
        (soul_id, thread_type),
    )
    thread_row = cursor.fetchone()
    if thread_row:
        ev_count = thread_row["evidence_count"] + 1
        th_status = "pattern_recognized" if ev_count >= 3 else thread_row["status"]
        cursor.execute(
            """
            UPDATE local_threads
            SET evidence_count = ?, status = ?, evidence_summary = ?
            WHERE id = ?
        """,
            (
                ev_count,
                th_status,
                f"Accumulated {ev_count} events under {thread_type} Thread",
                thread_row["id"],
            ),
        )
    else:
        th_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO local_threads (id, soul_id, name, thread_type, status, evidence_count, evidence_summary)
            VALUES (?, ?, ?, ?, 'active', 1, ?)
        """,
            (
                th_id,
                soul_id,
                f"{thread_type} of the {symbol}",
                thread_type,
                f"Seed '{symbol}' planted as first evidence",
            ),
        )

    conn.commit()
    conn.close()

    return {
        "seed_id": seed_id,
        "symbol": symbol,
        "thread_type": thread_type,
        "stage": new_stage,
        "echo_count": new_count,
    }


def get_all_seeds() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seeds ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "world_id": row["world_id"],
            "soul_id": row["soul_id"],
            "symbol": row["symbol"],
            "thread_type": row["thread_type"],
            "stage": row["stage"],
            "echo_count": row["echo_count"],
            "narrative_context": row["narrative_context"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def get_all_open_questions() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM open_questions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "seed_id": row["seed_id"],
            "question_text": row["question_text"],
            "stakes": row["stakes"],
            "status": row["status"],
            "evidence_event_ids": _json_or_none(row["evidence_event_ids_json"]) or [],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def resolve_open_question(
    question_id: str, resolution_notes: str, status: str = "resolved"
) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE open_questions SET status = ?, stakes = ? WHERE id = ?",
        (status, f"Resolved: {resolution_notes}", question_id),
    )
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0


def get_all_local_threads(soul_id: str = "Unbound Soul") -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM local_threads WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "soul_id": row["soul_id"],
            "name": row["name"],
            "thread_type": row["thread_type"],
            "status": row["status"],
            "evidence_count": row["evidence_count"],
            "evidence_summary": row["evidence_summary"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def execute_integration_event(
    *,
    thread_id: str,
    soul_id: str,
    choice_made: str,
    target_relic_id: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM local_threads WHERE id = ?", (thread_id,))
    thread = cursor.fetchone()
    if not thread:
        conn.close()
        raise ValueError("Thread not found")

    integration_id = str(uuid.uuid4())
    transformation = (
        f"Thread '{thread['name']}' ({thread['thread_type']}) integrated via choice: '{choice_made}'. "
        f"Transformed pattern into durable narrative progression."
    )

    cursor.execute(
        """
        INSERT INTO integration_events (id, soul_id, thread_id, choice_made, relic_awakened_id, transformation_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            integration_id,
            soul_id,
            thread_id,
            choice_made,
            target_relic_id,
            transformation,
        ),
    )

    cursor.execute(
        "UPDATE local_threads SET status = 'integrated' WHERE id = ?", (thread_id,)
    )

    conn.commit()
    conn.close()

    return {
        "integration_id": integration_id,
        "soul_id": soul_id,
        "thread_id": thread_id,
        "thread_name": thread["name"],
        "choice_made": choice_made,
        "relic_awakened_id": target_relic_id,
        "transformation_summary": transformation,
    }
