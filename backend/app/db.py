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
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS constellations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            unresolved_pattern TEXT NOT NULL,
            awakening_stage TEXT NOT NULL DEFAULT 'veiled',
            deep_threads_json TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aspects (
            id TEXT PRIMARY KEY,
            constellation_id TEXT NOT NULL,
            aspect_name TEXT NOT NULL,
            calling TEXT NOT NULL,
            origin TEXT NOT NULL,
            era_or_world TEXT NOT NULL,
            sheet_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS constellation_anchors (
            id TEXT PRIMARY KEY,
            constellation_id TEXT NOT NULL,
            anchor_name TEXT NOT NULL,
            relic_id TEXT,
            connected_aspect_ids_json TEXT NOT NULL DEFAULT '[]',
            relic_form TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'dormant',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cross_aspect_bonds (
            id TEXT PRIMARY KEY,
            constellation_id TEXT NOT NULL,
            source_aspect_id TEXT NOT NULL,
            target_aspect_id TEXT NOT NULL,
            bond_type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS probable_paths (
            id TEXT PRIMARY KEY,
            event_id TEXT,
            soul_id TEXT NOT NULL,
            path_title TEXT NOT NULL,
            chosen_path TEXT NOT NULL,
            unchosen_approach TEXT NOT NULL,
            potential_outcome_class TEXT NOT NULL,
            manifestation_type TEXT NOT NULL DEFAULT 'dream',
            status TEXT NOT NULL DEFAULT 'dormant',
            provenance_summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relics (
            id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            constellation_id TEXT,
            name TEXT NOT NULL,
            stage TEXT NOT NULL DEFAULT 'Dormant',
            effect TEXT NOT NULL,
            overdraw_consequence TEXT NOT NULL,
            evocative_question TEXT NOT NULL,
            required_thread_type TEXT,
            cross_aspect_forms_json TEXT NOT NULL DEFAULT '{}',
            is_anchor INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relic_events (
            id TEXT PRIMARY KEY,
            relic_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            action TEXT NOT NULL,
            previous_stage TEXT NOT NULL,
            new_stage TEXT NOT NULL,
            narrative_condition_met TEXT NOT NULL,
            chronicle_evidence_summary TEXT NOT NULL,
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


# Constellation & Aspect Database Helpers


def get_or_create_primary_constellation() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM constellations ORDER BY created_at ASC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        const_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO constellations (id, name, unresolved_pattern, awakening_stage, deep_threads_json)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                const_id,
                "Constellation of the Weeping Star",
                "The mystery of why the Starforge erased its own name across eras.",
                "echoing",
                json.dumps([
                    "Memory of the Erased Sun",
                    "The Unbroken Promise of Cinder"
                ]),
            ),
        )

        # Add initial Aspects
        aspect1_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO aspects (id, constellation_id, aspect_name, calling, origin, era_or_world)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                aspect1_id,
                const_id,
                "Kaelen the Star-Watcher",
                "Keeper of the Salt Compass",
                "Flooded Archives of Cinder",
                "Present Era (Age of Echoes)",
            ),
        )

        aspect2_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO aspects (id, constellation_id, aspect_name, calling, origin, era_or_world)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                aspect2_id,
                const_id,
                "Archivist Vael",
                "Forge-Maiden of the Celestial Ring",
                "Spire of Sunken Memory",
                "Ancient Era (Age of Starforge)",
            ),
        )

        # Add initial Anchors
        anchor_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO constellation_anchors (id, constellation_id, anchor_name, relic_id, connected_aspect_ids_json, relic_form, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                anchor_id,
                const_id,
                "Compass of Better Questions",
                "relic_compass_01",
                json.dumps([aspect1_id, aspect2_id]),
                "Astro-Chronometer",
                "awakened",
            ),
        )

        # Add initial Cross-Aspect Bond
        bond_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO cross_aspect_bonds (id, constellation_id, source_aspect_id, target_aspect_id, bond_type, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                bond_id,
                const_id,
                aspect1_id,
                aspect2_id,
                "memory_echo",
                "Both Aspects remember the exact moment the Salt Bell tolled backwards.",
            ),
        )
        conn.commit()
        cursor.execute("SELECT * FROM constellations WHERE id = ?", (const_id,))
        row = cursor.fetchone()

    constellation_id = row["id"]

    # Fetch aspects
    cursor.execute("SELECT * FROM aspects WHERE constellation_id = ?", (constellation_id,))
    aspect_rows = cursor.fetchall()
    aspects = [
        {
            "id": r["id"],
            "constellation_id": r["constellation_id"],
            "aspect_name": r["aspect_name"],
            "calling": r["calling"],
            "origin": r["origin"],
            "era_or_world": r["era_or_world"],
            "sheet": _json_or_none(r["sheet_json"]) or {},
            "created_at": r["created_at"],
        }
        for r in aspect_rows
    ]

    # Fetch anchors
    cursor.execute("SELECT * FROM constellation_anchors WHERE constellation_id = ?", (constellation_id,))
    anchor_rows = cursor.fetchall()
    anchors = [
        {
            "id": r["id"],
            "constellation_id": r["constellation_id"],
            "anchor_name": r["anchor_name"],
            "relic_id": r["relic_id"],
            "connected_aspect_ids": _json_or_none(r["connected_aspect_ids_json"]) or [],
            "relic_form": r["relic_form"],
            "status": r["status"],
            "created_at": r["created_at"],
        }
        for r in anchor_rows
    ]

    # Fetch bonds
    cursor.execute("SELECT * FROM cross_aspect_bonds WHERE constellation_id = ?", (constellation_id,))
    bond_rows = cursor.fetchall()
    bonds = [
        {
            "id": r["id"],
            "constellation_id": r["constellation_id"],
            "source_aspect_id": r["source_aspect_id"],
            "target_aspect_id": r["target_aspect_id"],
            "bond_type": r["bond_type"],
            "description": r["description"],
            "created_at": r["created_at"],
        }
        for r in bond_rows
    ]

    conn.close()

    return {
        "id": row["id"],
        "name": row["name"],
        "unresolved_pattern": row["unresolved_pattern"],
        "awakening_stage": row["awakening_stage"],
        "deep_threads": _json_or_none(row["deep_threads_json"]) or [],
        "aspects": aspects,
        "anchors": anchors,
        "bonds": bonds,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_aspect_record(
    *,
    constellation_id: str,
    aspect_name: str,
    calling: str,
    origin: str,
    era_or_world: str,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    aspect_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO aspects (id, constellation_id, aspect_name, calling, origin, era_or_world)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (aspect_id, constellation_id, aspect_name, calling, origin, era_or_world),
    )
    conn.commit()
    conn.close()

    # Re-evaluate awakening stage
    update_awakening_stage_record(constellation_id=constellation_id)

    return {
        "id": aspect_id,
        "constellation_id": constellation_id,
        "aspect_name": aspect_name,
        "calling": calling,
        "origin": origin,
        "era_or_world": era_or_world,
    }


def create_cross_aspect_bond_record(
    *,
    constellation_id: str,
    source_aspect_id: str,
    target_aspect_id: str,
    bond_type: str,
    description: str,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    bond_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO cross_aspect_bonds (id, constellation_id, source_aspect_id, target_aspect_id, bond_type, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (bond_id, constellation_id, source_aspect_id, target_aspect_id, bond_type, description),
    )
    conn.commit()
    conn.close()

    # Re-evaluate awakening stage
    update_awakening_stage_record(constellation_id=constellation_id)

    return {
        "id": bond_id,
        "constellation_id": constellation_id,
        "source_aspect_id": source_aspect_id,
        "target_aspect_id": target_aspect_id,
        "bond_type": bond_type,
        "description": description,
    }


def update_awakening_stage_record(*, constellation_id: str, target_stage: Optional[str] = None) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    if target_stage:
        new_stage = target_stage
    else:
        cursor.execute("SELECT COUNT(*) as cnt FROM aspects WHERE constellation_id = ?", (constellation_id,))
        aspect_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM cross_aspect_bonds WHERE constellation_id = ?", (constellation_id,))
        bond_count = cursor.fetchone()["cnt"]

        if aspect_count <= 1:
            new_stage = "veiled"
        elif aspect_count == 2 and bond_count == 0:
            new_stage = "echoing"
        elif aspect_count >= 2 and bond_count >= 1 and bond_count < 3:
            new_stage = "recognizing"
        elif aspect_count >= 3 or bond_count >= 3:
            new_stage = "resonant"
        elif bond_count >= 5:
            new_stage = "woven"
        else:
            new_stage = "echoing"

    cursor.execute(
        "UPDATE constellations SET awakening_stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_stage, constellation_id),
    )
    conn.commit()
    conn.close()
    return new_stage


# Probable Paths Database Helpers


def log_probable_path_record(
    *,
    soul_id: str,
    path_title: str,
    chosen_path: str,
    unchosen_approach: str,
    potential_outcome_class: str,
    event_id: Optional[str] = None,
    manifestation_type: str = "dream",
    provenance_summary: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    path_id = str(uuid.uuid4())
    prov = provenance_summary or (
        f"Forked from choice '{chosen_path}'. Unchosen approach '{unchosen_approach}' "
        f"remains narratively potent as a {manifestation_type}."
    )

    cursor.execute(
        """
        INSERT INTO probable_paths (
            id, event_id, soul_id, path_title, chosen_path, unchosen_approach,
            potential_outcome_class, manifestation_type, status, provenance_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            path_id,
            event_id,
            soul_id,
            path_title,
            chosen_path,
            unchosen_approach,
            potential_outcome_class,
            manifestation_type,
            "dormant",
            prov,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": path_id,
        "event_id": event_id,
        "soul_id": soul_id,
        "path_title": path_title,
        "chosen_path": chosen_path,
        "unchosen_approach": unchosen_approach,
        "potential_outcome_class": potential_outcome_class,
        "manifestation_type": manifestation_type,
        "status": "dormant",
        "provenance_summary": prov,
    }


def get_probable_paths_records(soul_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Seed defaults if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM probable_paths")
    if cursor.fetchone()["cnt"] == 0:
        _seed_default_probable_paths(conn, soul_id or "Kaelen the Star-Watcher")

    if soul_id:
        cursor.execute(
            "SELECT * FROM probable_paths WHERE soul_id = ? OR soul_id = 'Unbound Soul' ORDER BY created_at DESC",
            (soul_id,),
        )
    else:
        cursor.execute("SELECT * FROM probable_paths ORDER BY created_at DESC")

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "event_id": r["event_id"],
            "soul_id": r["soul_id"],
            "path_title": r["path_title"],
            "chosen_path": r["chosen_path"],
            "unchosen_approach": r["unchosen_approach"],
            "potential_outcome_class": r["potential_outcome_class"],
            "manifestation_type": r["manifestation_type"],
            "status": r["status"],
            "provenance_summary": r["provenance_summary"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def update_probable_path_manifestation(
    *, path_id: str, manifestation_type: str, status: str = "echoing"
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE probable_paths SET manifestation_type = ?, status = ? WHERE id = ?",
        (manifestation_type, status, path_id),
    )
    conn.commit()
    cursor.execute("SELECT * FROM probable_paths WHERE id = ?", (path_id,))
    r = cursor.fetchone()
    conn.close()

    if not r:
        raise ValueError("Probable path not found")

    return {
        "id": r["id"],
        "event_id": r["event_id"],
        "soul_id": r["soul_id"],
        "path_title": r["path_title"],
        "chosen_path": r["chosen_path"],
        "unchosen_approach": r["unchosen_approach"],
        "potential_outcome_class": r["potential_outcome_class"],
        "manifestation_type": r["manifestation_type"],
        "status": r["status"],
        "provenance_summary": r["provenance_summary"],
        "created_at": r["created_at"],
    }


def _seed_default_probable_paths(conn: sqlite3.Connection, soul_id: str) -> None:
    cursor = conn.cursor()
    seeds = [
        (
            str(uuid.uuid4()),
            None,
            soul_id,
            "The Silent Archive Confrontation",
            "Resolved via Guile & Negotiation",
            "Direct Confrontation with Ember Dragon",
            "ascendancy",
            "dream",
            "echoing",
            "Dream of the flames that would have burned the salt bell if sword met scale.",
        ),
        (
            str(uuid.uuid4()),
            None,
            soul_id,
            "The Weeping Door Threshold",
            "Entered with Token of Light",
            "Releasing the Secret Key into the Abyss",
            "revelatory_failure",
            "rumor",
            "dormant",
            "Rumors among salt miners of a key floating unbroken in the lower abyss.",
        ),
        (
            str(uuid.uuid4()),
            None,
            soul_id,
            "The Starforge Memory Key",
            "Claimed for the Present Aspect",
            "Surrendered to Archivist Vael",
            "marked_success",
            "alternate_scene",
            "manifested",
            "An alternate scene branch where the Starforge memory belonged to the Ancient Spire.",
        ),
    ]

    for item in seeds:
        cursor.execute(
            """
            INSERT INTO probable_paths (
                id, event_id, soul_id, path_title, chosen_path, unchosen_approach,
                potential_outcome_class, manifestation_type, status, provenance_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            item,
        )
    conn.commit()


# User Database Helpers


def create_user_record(
    *, email: str, username: str, password_hash: str, display_name: str
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO users (id, email, username, password_hash, display_name)
        VALUES (?, ?, ?, ?, ?)
    """,
        (user_id, email.lower().strip(), username.lower().strip(), password_hash, display_name.strip()),
    )
    conn.commit()
    conn.close()
    return {
        "id": user_id,
        "email": email.lower().strip(),
        "username": username.lower().strip(),
        "display_name": display_name.strip(),
    }


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "display_name": row["display_name"],
        "created_at": row["created_at"],
    }


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "display_name": row["display_name"],
        "created_at": row["created_at"],
    }


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "password_hash": row["password_hash"],
        "display_name": row["display_name"],
        "created_at": row["created_at"],
    }


# Relic Recognition Database Helpers


def get_or_create_relics_records(soul_id: str = "Kaelen the Star-Watcher") -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM relics WHERE soul_id = ? OR soul_id = 'Unbound Soul'", (soul_id,))
    if cursor.fetchone()["cnt"] == 0:
        _seed_default_relics(conn, soul_id)

    cursor.execute(
        "SELECT * FROM relics WHERE soul_id = ? OR soul_id = 'Unbound Soul' ORDER BY created_at ASC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "soul_id": r["soul_id"],
            "constellation_id": r["constellation_id"],
            "name": r["name"],
            "stage": r["stage"],
            "effect": r["effect"],
            "overdraw_consequence": r["overdraw_consequence"],
            "evocative_question": r["evocative_question"],
            "required_thread_type": r["required_thread_type"],
            "cross_aspect_forms": _json_or_none(r["cross_aspect_forms_json"]) or {},
            "is_anchor": bool(r["is_anchor"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


def get_relic_history_records(relic_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM relic_events WHERE relic_id = ? ORDER BY created_at DESC", (relic_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "relic_id": r["relic_id"],
            "soul_id": r["soul_id"],
            "action": r["action"],
            "previous_stage": r["previous_stage"],
            "new_stage": r["new_stage"],
            "narrative_condition_met": r["narrative_condition_met"],
            "chronicle_evidence_summary": r["chronicle_evidence_summary"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def update_relic_stage_record(
    *,
    relic_id: str,
    soul_id: str,
    action: str,
    new_stage: str,
    narrative_condition_met: str,
    chronicle_evidence_summary: str,
    new_effect: Optional[str] = None,
    is_anchor: Optional[bool] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM relics WHERE id = ?", (relic_id,))
    relic_row = cursor.fetchone()
    if not relic_row:
        conn.close()
        raise ValueError("Relic not found")

    previous_stage = relic_row["stage"]

    if new_effect:
        cursor.execute(
            "UPDATE relics SET stage = ?, effect = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_stage, new_effect, relic_id),
        )
    else:
        cursor.execute(
            "UPDATE relics SET stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_stage, relic_id),
        )

    if is_anchor is not None:
        cursor.execute(
            "UPDATE relics SET is_anchor = ? WHERE id = ?",
            (1 if is_anchor else 0, relic_id),
        )

    event_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO relic_events (
            id, relic_id, soul_id, action, previous_stage, new_stage,
            narrative_condition_met, chronicle_evidence_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            event_id,
            relic_id,
            soul_id,
            action,
            previous_stage,
            new_stage,
            narrative_condition_met,
            chronicle_evidence_summary,
        ),
    )

    conn.commit()

    cursor.execute("SELECT * FROM relics WHERE id = ?", (relic_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return {
        "relic": {
            "id": updated_row["id"],
            "soul_id": updated_row["soul_id"],
            "constellation_id": updated_row["constellation_id"],
            "name": updated_row["name"],
            "stage": updated_row["stage"],
            "effect": updated_row["effect"],
            "overdraw_consequence": updated_row["overdraw_consequence"],
            "evocative_question": updated_row["evocative_question"],
            "required_thread_type": updated_row["required_thread_type"],
            "cross_aspect_forms": _json_or_none(updated_row["cross_aspect_forms_json"]) or {},
            "is_anchor": bool(updated_row["is_anchor"]),
            "created_at": updated_row["created_at"],
            "updated_at": updated_row["updated_at"],
        },
        "relic_event": {
            "id": event_id,
            "relic_id": relic_id,
            "soul_id": soul_id,
            "action": action,
            "previous_stage": previous_stage,
            "new_stage": new_stage,
            "narrative_condition_met": narrative_condition_met,
            "chronicle_evidence_summary": chronicle_evidence_summary,
        },
    }


def _seed_default_relics(conn: sqlite3.Connection, soul_id: str) -> None:
    cursor = conn.cursor()
    soul_slug = soul_id.lower().replace(" ", "_").replace("-", "_")
    seeds = [
        (
            f"relic_compass_{soul_slug}",
            soul_id,
            "const_01",
            "Compass of Better Questions",
            "Awakened",
            "Allows shifting one Domain face to Omen once per session.",
            "Reveals an unwanted secret to the Foe.",
            "What question must be asked before the Weeping Door will yield?",
            "Memory",
            json.dumps({"Ancient Era": "Astro-Chronometer", "Future Era": "Resonance Dial"}),
            1,
        ),
        (
            f"relic_bell_{soul_slug}",
            soul_id,
            "const_01",
            "Salt Bell of Cinder",
            "Remembered",
            "Resonates when an Echo Thread is within three steps.",
            "Summons the memory of the Flooded Archives.",
            "Who tolled the bell backwards when the Starforge fell?",
            "Bond",
            json.dumps({"Ancient Era": "Sun-Chime", "Future Era": "Frequency Anchor"}),
            0,
        ),
        (
            f"relic_lantern_{soul_slug}",
            soul_id,
            None,
            "Lantern of Forgotten Suns",
            "Dormant",
            "Illuminates hidden Veils and reveals unseen motives.",
            "Blinds the bearer's vision to physical surroundings for one beat.",
            "What light burned when the King Without a Reflection crossed the threshold?",
            "Mark",
            json.dumps({"Ancient Era": "Sol Prism", "Future Era": "Starlight Beacon"}),
            0,
        ),
    ]

    for item in seeds:
        cursor.execute(
            """
            INSERT INTO relics (
                id, soul_id, constellation_id, name, stage, effect,
                overdraw_consequence, evocative_question, required_thread_type,
                cross_aspect_forms_json, is_anchor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            item,
        )
        # Add initial event
        cursor.execute(
            """
            INSERT INTO relic_events (
                id, relic_id, soul_id, action, previous_stage, new_stage,
                narrative_condition_met, chronicle_evidence_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                item[0],
                soul_id,
                "attune",
                "Dormant",
                item[4],
                "Initial mythic discovery in the chronicle.",
                f"Relic '{item[3]}' discovered during expedition.",
            ),
        )

    conn.commit()




