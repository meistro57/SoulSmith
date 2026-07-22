"""
SoulSmith Canonical Database Engine (SQLite-first storage abstraction).
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_symbols (
            id TEXT PRIMARY KEY,
            symbol_name TEXT NOT NULL,
            world_id TEXT NOT NULL,
            description TEXT NOT NULL,
            significance_score INTEGER DEFAULT 1,
            contributing_souls_json TEXT NOT NULL DEFAULT '[]',
            canon_status TEXT NOT NULL DEFAULT 'opt_in_shared',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS convergence_gatherings (
            id TEXT PRIMARY KEY,
            room_id TEXT NOT NULL,
            phenomenon_name TEXT NOT NULL,
            target_resonance INTEGER DEFAULT 10,
            current_resonance INTEGER DEFAULT 0,
            roles_json TEXT NOT NULL DEFAULT '{}',
            contributions_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'active',
            outcome_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_preferences (
            soul_id TEXT PRIMARY KEY,
            narrative_intensity TEXT NOT NULL DEFAULT 'balanced',
            spiritual_framing TEXT NOT NULL DEFAULT 'secular_mythology',
            reduced_motion INTEGER DEFAULT 0,
            high_contrast INTEGER DEFAULT 0,
            allow_ai_indexing_default INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reflection_sessions (
            id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            prompt_question TEXT NOT NULL,
            player_reflection TEXT NOT NULL,
            share_with_ai INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS private_notes (
            id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            allow_ai_indexing INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avatar_identities (
            soul_id TEXT PRIMARY KEY,
            face TEXT NOT NULL,
            hair TEXT NOT NULL,
            body TEXT NOT NULL,
            species TEXT NOT NULL,
            eyes TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS story_marks (
            id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            mark_type TEXT NOT NULL,
            location TEXT NOT NULL,
            origin_event_id TEXT NOT NULL,
            acquired_at TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'prominent',
            status TEXT NOT NULL DEFAULT 'permanent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_appearances (
            soul_id TEXT PRIMARY KEY,
            armor TEXT NOT NULL,
            clothing TEXT NOT NULL,
            weapons_json TEXT NOT NULL DEFAULT '[]',
            relics_json TEXT NOT NULL DEFAULT '[]',
            backpacks_cloaks TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portrait_versions (
            version_id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            label TEXT NOT NULL,
            image_url TEXT NOT NULL,
            story_marks_snapshot_json TEXT NOT NULL DEFAULT '[]',
            equipment_snapshot_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visual_consent_settings (
            soul_id TEXT PRIMARY KEY,
            allow_shared_gallery INTEGER DEFAULT 1,
            allow_character_tagging INTEGER DEFAULT 1,
            allow_real_person_tagging INTEGER DEFAULT 0,
            real_person_photo_url TEXT,
            real_person_display_name TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_objects (
            id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            event_title TEXT NOT NULL,
            participants_json TEXT NOT NULL DEFAULT '[]',
            location_environment TEXT NOT NULL,
            relics_involved_json TEXT NOT NULL DEFAULT '[]',
            emotional_tone TEXT NOT NULL,
            action_composition TEXT NOT NULL,
            lasting_consequence TEXT NOT NULL,
            privacy_consent_scope TEXT NOT NULL DEFAULT 'public_canon',
            visual_generation_status TEXT NOT NULL DEFAULT 'compiled',
            painting_image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portrait_generation_candidates (
            candidate_id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            source_portrait_version_id TEXT,
            generation_type TEXT NOT NULL DEFAULT 'initial',
            compiled_prompt TEXT NOT NULL,
            negative_prompt TEXT,
            provider TEXT NOT NULL DEFAULT 'mock',
            provider_model TEXT NOT NULL DEFAULT 'soulsmith-mock-v1',
            provider_request_id TEXT,
            generation_seed INTEGER,
            reference_image_url TEXT,
            generated_image_url TEXT,
            canonical_identity_snapshot_json TEXT NOT NULL,
            story_marks_snapshot_json TEXT NOT NULL DEFAULT '[]',
            equipment_snapshot_json TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            failure_reason TEXT,
            resulting_portrait_version_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP
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
                json.dumps(
                    ["Memory of the Erased Sun", "The Unbroken Promise of Cinder"]
                ),
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
    cursor.execute(
        "SELECT * FROM aspects WHERE constellation_id = ?", (constellation_id,)
    )
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
    cursor.execute(
        "SELECT * FROM constellation_anchors WHERE constellation_id = ?",
        (constellation_id,),
    )
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
    cursor.execute(
        "SELECT * FROM cross_aspect_bonds WHERE constellation_id = ?",
        (constellation_id,),
    )
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
        (
            bond_id,
            constellation_id,
            source_aspect_id,
            target_aspect_id,
            bond_type,
            description,
        ),
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


def update_awakening_stage_record(
    *, constellation_id: str, target_stage: Optional[str] = None
) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    if target_stage:
        new_stage = target_stage
    else:
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM aspects WHERE constellation_id = ?",
            (constellation_id,),
        )
        aspect_count = cursor.fetchone()["cnt"]

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM cross_aspect_bonds WHERE constellation_id = ?",
            (constellation_id,),
        )
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
        (
            user_id,
            email.lower().strip(),
            username.lower().strip(),
            password_hash,
            display_name.strip(),
        ),
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
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (username.lower().strip(),)
    )
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


def get_or_create_relics_records(
    soul_id: str = "Kaelen the Star-Watcher",
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM relics WHERE soul_id = ? OR soul_id = 'Unbound Soul'",
        (soul_id,),
    )
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
    cursor.execute(
        "SELECT * FROM relic_events WHERE relic_id = ? ORDER BY created_at DESC",
        (relic_id,),
    )
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
            "cross_aspect_forms": _json_or_none(updated_row["cross_aspect_forms_json"])
            or {},
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
            json.dumps(
                {"Ancient Era": "Astro-Chronometer", "Future Era": "Resonance Dial"}
            ),
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


# Convergence & Community Mythology Helpers


def get_community_symbols_records() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM community_symbols")
    if cursor.fetchone()["cnt"] == 0:
        _seed_default_community_symbols(conn)

    cursor.execute(
        "SELECT * FROM community_symbols ORDER BY significance_score DESC, created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "symbol_name": r["symbol_name"],
            "world_id": r["world_id"],
            "description": r["description"],
            "significance_score": r["significance_score"],
            "contributing_souls": _json_or_none(r["contributing_souls_json"]) or [],
            "canon_status": r["canon_status"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def create_community_symbol_record(
    *,
    symbol_name: str,
    world_id: str = "world_starforge_01",
    description: str,
    contributing_souls: List[str],
    canon_status: str = "opt_in_shared",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    symbol_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO community_symbols (
            id, symbol_name, world_id, description, significance_score,
            contributing_souls_json, canon_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            symbol_id,
            symbol_name,
            world_id,
            description,
            len(contributing_souls),
            json.dumps(contributing_souls),
            canon_status,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "id": symbol_id,
        "symbol_name": symbol_name,
        "world_id": world_id,
        "description": description,
        "significance_score": len(contributing_souls),
        "contributing_souls": contributing_souls,
        "canon_status": canon_status,
    }


def get_or_create_gathering_session(
    room_id: str = "convergence_alpha",
    phenomenon_name: str = "Awakening of the Salt Spire",
    target_resonance: int = 10,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM convergence_gatherings WHERE room_id = ? AND status = 'active' ORDER BY created_at DESC",
        (room_id,),
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "id": row["id"],
            "room_id": row["room_id"],
            "phenomenon_name": row["phenomenon_name"],
            "target_resonance": row["target_resonance"],
            "current_resonance": row["current_resonance"],
            "roles": _json_or_none(row["roles_json"]) or {},
            "contributions": _json_or_none(row["contributions_json"]) or [],
            "status": row["status"],
            "outcome_summary": row["outcome_summary"],
            "created_at": row["created_at"],
        }

    gathering_id = str(uuid.uuid4())
    default_roles = {
        "Focus": "Kaelen the Star-Watcher",
        "Anchor": "Archivist Vael",
        "Witness": "Mira the Seeker",
        "Tempest": "Ember Vanguard",
    }
    cursor.execute(
        """
        INSERT INTO convergence_gatherings (
            id, room_id, phenomenon_name, target_resonance, current_resonance,
            roles_json, contributions_json, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            gathering_id,
            room_id,
            phenomenon_name,
            target_resonance,
            0,
            json.dumps(default_roles),
            json.dumps([]),
            "active",
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": gathering_id,
        "room_id": room_id,
        "phenomenon_name": phenomenon_name,
        "target_resonance": target_resonance,
        "current_resonance": 0,
        "roles": default_roles,
        "contributions": [],
        "status": "active",
        "outcome_summary": None,
    }


def add_gathering_contribution(
    *,
    gathering_id: str,
    contributor_soul: str,
    role: str,
    resonance_amount: int,
    notes: str,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM convergence_gatherings WHERE id = ?", (gathering_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Gathering session not found")

    current_res = row["current_resonance"] + resonance_amount
    target_res = row["target_resonance"]
    contributions = _json_or_none(row["contributions_json"]) or []

    contrib_id = str(uuid.uuid4())
    new_contrib = {
        "id": contrib_id,
        "contributor_soul": contributor_soul,
        "role": role,
        "resonance_amount": resonance_amount,
        "notes": notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    contributions.append(new_contrib)

    status_val = "reconciled" if current_res >= target_res else "active"
    outcome = (
        f"The collective resonance reached {current_res}/{target_res}! Phenomenon '{row['phenomenon_name']}' awakened."
        if status_val == "reconciled"
        else None
    )

    cursor.execute(
        """
        UPDATE convergence_gatherings
        SET current_resonance = ?, contributions_json = ?, status = ?, outcome_summary = ?
        WHERE id = ?
    """,
        (current_res, json.dumps(contributions), status_val, outcome, gathering_id),
    )

    conn.commit()

    cursor.execute("SELECT * FROM convergence_gatherings WHERE id = ?", (gathering_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return {
        "gathering": {
            "id": updated_row["id"],
            "room_id": updated_row["room_id"],
            "phenomenon_name": updated_row["phenomenon_name"],
            "target_resonance": updated_row["target_resonance"],
            "current_resonance": updated_row["current_resonance"],
            "roles": _json_or_none(updated_row["roles_json"]) or {},
            "contributions": _json_or_none(updated_row["contributions_json"]) or [],
            "status": updated_row["status"],
            "outcome_summary": updated_row["outcome_summary"],
        },
        "latest_contribution": new_contrib,
    }


def _seed_default_community_symbols(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    seeds = [
        (
            "sym_01",
            "The Starforge Emblem",
            "world_starforge_01",
            "A celestial anvil bound by five starlight chains, symbolizing shared convergence.",
            5,
            json.dumps(
                ["Kaelen the Star-Watcher", "Archivist Vael", "Mira the Seeker"]
            ),
            "public_canon",
        ),
        (
            "sym_02",
            "Salt Spire Covenant",
            "world_starforge_01",
            "A salt-crusted bell that rings when three Souls share a memory across eras.",
            3,
            json.dumps(["Kaelen the Star-Watcher", "Ember Vanguard"]),
            "opt_in_shared",
        ),
        (
            "sym_03",
            "Veil of Frost Lantern",
            "world_starforge_01",
            "A blue lantern lit during the Winter Lantern Gathering in Frost Hollow.",
            4,
            json.dumps(["Rowan", "Mira", "Elira"]),
            "public_canon",
        ),
    ]

    for item in seeds:
        cursor.execute(
            """
            INSERT INTO community_symbols (
                id, symbol_name, world_id, description, significance_score,
                contributing_souls_json, canon_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            item,
        )
    conn.commit()


# Reflection & Accessibility Database Helpers


def get_or_create_preferences_record(
    soul_id: str = "Kaelen the Star-Watcher",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM player_preferences WHERE soul_id = ?", (soul_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "soul_id": row["soul_id"],
            "narrative_intensity": row["narrative_intensity"],
            "spiritual_framing": row["spiritual_framing"],
            "reduced_motion": bool(row["reduced_motion"]),
            "high_contrast": bool(row["high_contrast"]),
            "allow_ai_indexing_default": bool(row["allow_ai_indexing_default"]),
            "updated_at": row["updated_at"],
        }

    cursor.execute(
        """
        INSERT INTO player_preferences (
            soul_id, narrative_intensity, spiritual_framing, reduced_motion,
            high_contrast, allow_ai_indexing_default
        ) VALUES (?, 'balanced', 'secular_mythology', 0, 0, 0)
    """,
        (soul_id,),
    )
    conn.commit()
    conn.close()

    return {
        "soul_id": soul_id,
        "narrative_intensity": "balanced",
        "spiritual_framing": "secular_mythology",
        "reduced_motion": False,
        "high_contrast": False,
        "allow_ai_indexing_default": False,
    }


def update_preferences_record(
    soul_id: str,
    *,
    narrative_intensity: str,
    spiritual_framing: str,
    reduced_motion: bool,
    high_contrast: bool,
    allow_ai_indexing_default: bool,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO player_preferences (
            soul_id, narrative_intensity, spiritual_framing, reduced_motion,
            high_contrast, allow_ai_indexing_default, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(soul_id) DO UPDATE SET
            narrative_intensity = excluded.narrative_intensity,
            spiritual_framing = excluded.spiritual_framing,
            reduced_motion = excluded.reduced_motion,
            high_contrast = excluded.high_contrast,
            allow_ai_indexing_default = excluded.allow_ai_indexing_default,
            updated_at = CURRENT_TIMESTAMP
    """,
        (
            soul_id,
            narrative_intensity,
            spiritual_framing,
            1 if reduced_motion else 0,
            1 if high_contrast else 0,
            1 if allow_ai_indexing_default else 0,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "soul_id": soul_id,
        "narrative_intensity": narrative_intensity,
        "spiritual_framing": spiritual_framing,
        "reduced_motion": reduced_motion,
        "high_contrast": high_contrast,
        "allow_ai_indexing_default": allow_ai_indexing_default,
    }


def create_reflection_record(
    *,
    soul_id: str,
    prompt_question: str,
    player_reflection: str,
    share_with_ai: bool = False,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    ref_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO reflection_sessions (
            id, soul_id, prompt_question, player_reflection, share_with_ai
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (
            ref_id,
            soul_id,
            prompt_question,
            player_reflection,
            1 if share_with_ai else 0,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": ref_id,
        "soul_id": soul_id,
        "prompt_question": prompt_question,
        "player_reflection": player_reflection,
        "share_with_ai": share_with_ai,
    }


def get_reflections_records(soul_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reflection_sessions WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "soul_id": r["soul_id"],
            "prompt_question": r["prompt_question"],
            "player_reflection": r["player_reflection"],
            "share_with_ai": bool(r["share_with_ai"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def create_private_note_record(
    *,
    soul_id: str,
    title: str,
    content: str,
    allow_ai_indexing: bool = False,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    note_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO private_notes (
            id, soul_id, title, content, allow_ai_indexing
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (note_id, soul_id, title, content, 1 if allow_ai_indexing else 0),
    )
    conn.commit()
    conn.close()

    return {
        "id": note_id,
        "soul_id": soul_id,
        "title": title,
        "content": content,
        "allow_ai_indexing": allow_ai_indexing,
    }


def get_private_notes_records(soul_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM private_notes WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "soul_id": r["soul_id"],
            "title": r["title"],
            "content": r["content"],
            "allow_ai_indexing": bool(r["allow_ai_indexing"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


# Phase 9: Visual Identity Foundation & Memory Objects DB Helpers


def get_or_create_avatar_identity_record(
    soul_id: str = "Kaelen the Star-Watcher",
    face: str = "Defined features, sharp jawline, observant expression",
    hair: str = "Dark raven hair worn tied back",
    body: str = "Athletic build worn by travel",
    species: str = "Human Aspect",
    eyes: str = "Deep amber eyes reflecting starlight",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM avatar_identities WHERE soul_id = ?", (soul_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "soul_id": row["soul_id"],
            "face": row["face"],
            "hair": row["hair"],
            "body": row["body"],
            "species": row["species"],
            "eyes": row["eyes"],
        }

    cursor.execute(
        """
        INSERT INTO avatar_identities (soul_id, face, hair, body, species, eyes)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (soul_id, face, hair, body, species, eyes),
    )
    conn.commit()
    conn.close()

    return {
        "soul_id": soul_id,
        "face": face,
        "hair": hair,
        "body": body,
        "species": species,
        "eyes": eyes,
    }


def add_story_mark_record(
    *,
    soul_id: str,
    mark_type: str,
    location: str,
    origin_event_id: str,
    acquired_at: str,
    visibility: str = "prominent",
    status: str = "permanent",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    mark_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO story_marks (
            id, soul_id, mark_type, location, origin_event_id, acquired_at, visibility, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            mark_id,
            soul_id,
            mark_type,
            location,
            origin_event_id,
            acquired_at,
            visibility,
            status,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": mark_id,
        "soul_id": soul_id,
        "mark_type": mark_type,
        "location": location,
        "origin_event_id": origin_event_id,
        "acquired_at": acquired_at,
        "visibility": visibility,
        "status": status,
    }


def get_story_marks_records(soul_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM story_marks WHERE soul_id = ? ORDER BY created_at ASC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "soul_id": r["soul_id"],
            "mark_type": r["mark_type"],
            "location": r["location"],
            "origin_event_id": r["origin_event_id"],
            "acquired_at": r["acquired_at"],
            "visibility": r["visibility"],
            "status": r["status"],
        }
        for r in rows
    ]


def get_or_create_equipment_appearance_record(
    soul_id: str = "Kaelen the Star-Watcher",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipment_appearances WHERE soul_id = ?", (soul_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "soul_id": row["soul_id"],
            "armor": row["armor"],
            "clothing": row["clothing"],
            "weapons": _json_or_none(row["weapons_json"]) or ["Seer's Starlight Blade"],
            "relics": _json_or_none(row["relics_json"]) or ["Dormant Salt Bell"],
            "backpacks_cloaks": row["backpacks_cloaks"],
        }

    default_equip = {
        "soul_id": soul_id,
        "armor": "Weathered iron pauldrons and salt-crusted leather doublet",
        "clothing": "Ash-colored travel cloak with silver thread embroidery",
        "weapons": ["Seer's Starlight Blade", "Etched Runic Dagger"],
        "relics": ["Dormant Salt Bell"],
        "backpacks_cloaks": "Heavy wool cloak with raven brooch",
    }
    cursor.execute(
        """
        INSERT INTO equipment_appearances (
            soul_id, armor, clothing, weapons_json, relics_json, backpacks_cloaks
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            soul_id,
            default_equip["armor"],
            default_equip["clothing"],
            json.dumps(default_equip["weapons"]),
            json.dumps(default_equip["relics"]),
            default_equip["backpacks_cloaks"],
        ),
    )
    conn.commit()
    conn.close()

    return default_equip


def create_portrait_version_record(
    *,
    soul_id: str,
    label: str,
    image_url: str,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current story marks and equipment
    cursor.execute(
        "SELECT * FROM story_marks WHERE soul_id = ? ORDER BY created_at ASC",
        (soul_id,),
    )
    marks_rows = cursor.fetchall()
    marks_snapshot = [
        {
            "id": r["id"],
            "soul_id": r["soul_id"],
            "mark_type": r["mark_type"],
            "location": r["location"],
            "origin_event_id": r["origin_event_id"],
            "acquired_at": r["acquired_at"],
            "visibility": r["visibility"],
            "status": r["status"],
        }
        for r in marks_rows
    ]

    cursor.execute("SELECT * FROM equipment_appearances WHERE soul_id = ?", (soul_id,))
    eq_row = cursor.fetchone()
    eq_snapshot = None
    if eq_row:
        eq_snapshot = {
            "soul_id": eq_row["soul_id"],
            "armor": eq_row["armor"],
            "clothing": eq_row["clothing"],
            "weapons": _json_or_none(eq_row["weapons_json"]) or [],
            "relics": _json_or_none(eq_row["relics_json"]) or [],
            "backpacks_cloaks": eq_row["backpacks_cloaks"],
        }

    cursor.execute(
        "SELECT COUNT(*) as count FROM portrait_versions WHERE soul_id = ?", (soul_id,)
    )
    version_num = (cursor.fetchone()["count"] or 0) + 1
    version_id = f"pv_{version_num}_{str(uuid.uuid4())[:8]}"

    cursor.execute(
        """
        INSERT INTO portrait_versions (
            version_id, soul_id, version_number, label, image_url,
            story_marks_snapshot_json, equipment_snapshot_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            version_id,
            soul_id,
            version_num,
            label,
            image_url,
            json.dumps(marks_snapshot),
            json.dumps(eq_snapshot) if eq_snapshot else None,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "version_id": version_id,
        "soul_id": soul_id,
        "version_number": version_num,
        "label": label,
        "image_url": image_url,
        "story_marks_snapshot": marks_snapshot,
        "equipment_snapshot": eq_snapshot,
    }


def get_portrait_versions_records(soul_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM portrait_versions WHERE soul_id = ? ORDER BY version_number ASC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        # Seed default initial portrait version (v1 - original pre-scar)
        v1 = create_portrait_version_record(
            soul_id=soul_id,
            label="Original Identity (v1)",
            image_url="/assets/portraits/kaelen_original.png",
        )
        return [v1]

    return [
        {
            "version_id": r["version_id"],
            "soul_id": r["soul_id"],
            "version_number": r["version_number"],
            "label": r["label"],
            "image_url": r["image_url"],
            "story_marks_snapshot": _json_or_none(r["story_marks_snapshot_json"]) or [],
            "equipment_snapshot": _json_or_none(r["equipment_snapshot_json"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def get_or_create_visual_consent_record(
    soul_id: str = "Kaelen the Star-Watcher",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_consent_settings WHERE soul_id = ?", (soul_id,)
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "soul_id": row["soul_id"],
            "allow_shared_gallery": bool(row["allow_shared_gallery"]),
            "allow_character_tagging": bool(row["allow_character_tagging"]),
            "allow_real_person_tagging": bool(row["allow_real_person_tagging"]),
            "real_person_photo_url": row["real_person_photo_url"],
            "real_person_display_name": row["real_person_display_name"],
        }

    cursor.execute(
        """
        INSERT INTO visual_consent_settings (
            soul_id, allow_shared_gallery, allow_character_tagging, allow_real_person_tagging
        ) VALUES (?, 1, 1, 0)
    """,
        (soul_id,),
    )
    conn.commit()
    conn.close()

    return {
        "soul_id": soul_id,
        "allow_shared_gallery": True,
        "allow_character_tagging": True,
        "allow_real_person_tagging": False,
        "real_person_photo_url": None,
        "real_person_display_name": None,
    }


def compile_memory_object_record(
    *,
    event_id: str,
    event_title: str,
    participants: List[Dict[str, Any]],
    location_environment: str,
    relics_involved: List[str],
    emotional_tone: str,
    action_composition: str,
    lasting_consequence: str,
    privacy_consent_scope: str = "public_canon",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    mem_id = f"mem_{str(uuid.uuid4())[:8]}"

    cursor.execute(
        """
        INSERT INTO memory_objects (
            id, event_id, event_title, participants_json, location_environment,
            relics_involved_json, emotional_tone, action_composition, lasting_consequence,
            privacy_consent_scope, visual_generation_status, painting_image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'compiled', ?)
    """,
        (
            mem_id,
            event_id,
            event_title,
            json.dumps(participants),
            location_environment,
            json.dumps(relics_involved),
            emotional_tone,
            action_composition,
            lasting_consequence,
            privacy_consent_scope,
            f"/assets/paintings/{event_id}_painting.png",
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": mem_id,
        "event_id": event_id,
        "event_title": event_title,
        "participants": participants,
        "location_environment": location_environment,
        "relics_involved": relics_involved,
        "emotional_tone": emotional_tone,
        "action_composition": action_composition,
        "lasting_consequence": lasting_consequence,
        "privacy_consent_scope": privacy_consent_scope,
        "visual_generation_status": "compiled",
        "painting_image_url": f"/assets/paintings/{event_id}_painting.png",
    }


def get_memory_objects_records() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory_objects ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "event_id": r["event_id"],
            "event_title": r["event_title"],
            "participants": _json_or_none(r["participants_json"]) or [],
            "location_environment": r["location_environment"],
            "relics_involved": _json_or_none(r["relics_involved_json"]) or [],
            "emotional_tone": r["emotional_tone"],
            "action_composition": r["action_composition"],
            "lasting_consequence": r["lasting_consequence"],
            "privacy_consent_scope": r["privacy_consent_scope"],
            "visual_generation_status": r["visual_generation_status"],
            "painting_image_url": r["painting_image_url"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


# Phase 10: Candidate & Continuity DB Helpers


def _map_candidate_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "candidate_id": row["candidate_id"],
        "soul_id": row["soul_id"],
        "source_portrait_version_id": row["source_portrait_version_id"],
        "generation_type": row["generation_type"],
        "compiled_prompt": row["compiled_prompt"],
        "negative_prompt": row["negative_prompt"],
        "provider": row["provider"],
        "provider_model": row["provider_model"],
        "provider_request_id": row["provider_request_id"],
        "generation_seed": row["generation_seed"],
        "reference_image_url": row["reference_image_url"],
        "generated_image_url": row["generated_image_url"],
        "canonical_identity_snapshot": _json_or_none(
            row["canonical_identity_snapshot_json"]
        )
        or {},
        "story_marks_snapshot": _json_or_none(row["story_marks_snapshot_json"]) or [],
        "equipment_snapshot": _json_or_none(row["equipment_snapshot_json"]),
        "status": row["status"],
        "failure_reason": row["failure_reason"],
        "resulting_portrait_version_id": row["resulting_portrait_version_id"],
        "created_at": row["created_at"],
        "reviewed_at": row["reviewed_at"],
    }


def create_portrait_candidate_record(
    *,
    soul_id: str,
    generation_type: str,
    compiled_prompt: str,
    canonical_identity_snapshot: Dict[str, Any],
    story_marks_snapshot: List[Dict[str, Any]],
    equipment_snapshot: Optional[Dict[str, Any]] = None,
    source_portrait_version_id: Optional[str] = None,
    reference_image_url: Optional[str] = None,
    negative_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cand_id = f"cand_{str(uuid.uuid4())[:8]}"

    cursor.execute(
        """
        INSERT INTO portrait_generation_candidates (
            candidate_id, soul_id, source_portrait_version_id, generation_type,
            compiled_prompt, negative_prompt, reference_image_url,
            canonical_identity_snapshot_json, story_marks_snapshot_json, equipment_snapshot_json,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """,
        (
            cand_id,
            soul_id,
            source_portrait_version_id,
            generation_type,
            compiled_prompt,
            negative_prompt,
            reference_image_url,
            json.dumps(canonical_identity_snapshot),
            json.dumps(story_marks_snapshot),
            json.dumps(equipment_snapshot) if equipment_snapshot else None,
        ),
    )
    conn.commit()

    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE candidate_id = ?",
        (cand_id,),
    )
    row = cursor.fetchone()
    conn.close()

    return _map_candidate_row(row)


def update_candidate_generation_result(
    candidate_id: str,
    *,
    status: str,
    generated_image_url: Optional[str] = None,
    provider: str = "mock",
    provider_model: str = "soulsmith-mock-v1",
    provider_request_id: Optional[str] = None,
    generation_seed: Optional[int] = None,
    failure_reason: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE portrait_generation_candidates
        SET status = ?,
            generated_image_url = ?,
            provider = ?,
            provider_model = ?,
            provider_request_id = ?,
            generation_seed = ?,
            failure_reason = ?
        WHERE candidate_id = ?
    """,
        (
            status,
            generated_image_url,
            provider,
            provider_model,
            provider_request_id,
            generation_seed,
            failure_reason,
            candidate_id,
        ),
    )
    conn.commit()

    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE candidate_id = ?",
        (candidate_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Candidate {candidate_id} not found")

    return _map_candidate_row(row)


def approve_portrait_candidate_transaction(
    candidate_id: str,
    soul_id: str,
    custom_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transactionally approves a generated candidate into a permanent PortraitVersion.
    Uses the exact identity, marks, and equipment snapshots stored on the candidate.
    Is idempotent.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM portrait_generation_candidates WHERE candidate_id = ?",
            (candidate_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Candidate '{candidate_id}' not found")

        if row["soul_id"] != soul_id:
            conn.close()
            raise ValueError(
                f"Candidate '{candidate_id}' does not belong to soul '{soul_id}'"
            )

        # Idempotency check: if already approved, return existing portrait version
        if row["status"] == "approved" and row["resulting_portrait_version_id"]:
            res_pv_id = row["resulting_portrait_version_id"]
            cursor.execute(
                "SELECT * FROM portrait_versions WHERE version_id = ?", (res_pv_id,)
            )
            pv_row = cursor.fetchone()
            conn.close()
            if pv_row:
                return {
                    "version_id": pv_row["version_id"],
                    "soul_id": pv_row["soul_id"],
                    "version_number": pv_row["version_number"],
                    "label": pv_row["label"],
                    "image_url": pv_row["image_url"],
                    "story_marks_snapshot": _json_or_none(
                        pv_row["story_marks_snapshot_json"]
                    )
                    or [],
                    "equipment_snapshot": _json_or_none(
                        pv_row["equipment_snapshot_json"]
                    ),
                    "created_at": pv_row["created_at"],
                }

        if row["status"] != "generated":
            conn.close()
            raise ValueError(
                f"Cannot approve candidate '{candidate_id}' in status '{row['status']}'. Must be in 'generated' state."
            )

        if not row["generated_image_url"]:
            conn.close()
            raise ValueError(f"Candidate '{candidate_id}' has no generated_image_url.")

        # Determine version number
        cursor.execute(
            "SELECT COUNT(*) as count FROM portrait_versions WHERE soul_id = ?",
            (soul_id,),
        )
        version_num = (cursor.fetchone()["count"] or 0) + 1
        version_id = f"pv_{version_num}_{str(uuid.uuid4())[:8]}"

        gen_type = row["generation_type"]
        label = (
            custom_label
            or f"Portrait v{version_num} ({gen_type.replace('_', ' ').title()})"
        )

        # Insert exact snapshots stored on candidate
        cursor.execute(
            """
            INSERT INTO portrait_versions (
                version_id, soul_id, version_number, label, image_url,
                story_marks_snapshot_json, equipment_snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                version_id,
                soul_id,
                version_num,
                label,
                row["generated_image_url"],
                row["story_marks_snapshot_json"],
                row["equipment_snapshot_json"],
            ),
        )

        # Update candidate status to approved
        cursor.execute(
            """
            UPDATE portrait_generation_candidates
            SET status = 'approved',
                resulting_portrait_version_id = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE candidate_id = ?
        """,
            (version_id, candidate_id),
        )

        conn.commit()

        # Fetch created portrait version
        cursor.execute(
            "SELECT * FROM portrait_versions WHERE version_id = ?", (version_id,)
        )
        pv_row = cursor.fetchone()
        conn.close()

        return {
            "version_id": pv_row["version_id"],
            "soul_id": pv_row["soul_id"],
            "version_number": pv_row["version_number"],
            "label": pv_row["label"],
            "image_url": pv_row["image_url"],
            "story_marks_snapshot": _json_or_none(pv_row["story_marks_snapshot_json"])
            or [],
            "equipment_snapshot": _json_or_none(pv_row["equipment_snapshot_json"]),
            "created_at": pv_row["created_at"],
        }
    except Exception:
        conn.rollback()
        conn.close()
        raise


def reject_portrait_candidate_record(candidate_id: str, soul_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE candidate_id = ?",
        (candidate_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Candidate '{candidate_id}' not found")

    if row["soul_id"] != soul_id:
        conn.close()
        raise ValueError(
            f"Candidate '{candidate_id}' does not belong to soul '{soul_id}'"
        )

    if row["status"] == "approved":
        conn.close()
        raise ValueError(
            f"Candidate '{candidate_id}' has already been approved and cannot be rejected."
        )

    cursor.execute(
        """
        UPDATE portrait_generation_candidates
        SET status = 'rejected',
            reviewed_at = CURRENT_TIMESTAMP
        WHERE candidate_id = ?
    """,
        (candidate_id,),
    )
    conn.commit()

    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE candidate_id = ?",
        (candidate_id,),
    )
    updated_row = cursor.fetchone()
    conn.close()

    return _map_candidate_row(updated_row)


def get_portrait_candidate_record(candidate_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE candidate_id = ?",
        (candidate_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _map_candidate_row(row)


def get_portrait_candidates_records(soul_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_candidate_row(r) for r in rows]


def get_portrait_version_record(version_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM portrait_versions WHERE version_id = ?", (version_id,)
    )
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "version_id": r["version_id"],
        "soul_id": r["soul_id"],
        "version_number": r["version_number"],
        "label": r["label"],
        "image_url": r["image_url"],
        "story_marks_snapshot": _json_or_none(r["story_marks_snapshot_json"]) or [],
        "equipment_snapshot": _json_or_none(r["equipment_snapshot_json"]),
        "created_at": r["created_at"],
    }
