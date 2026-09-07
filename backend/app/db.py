"""
SoulSmith Canonical Database Engine (SQLite-first storage abstraction).
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

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
            importance_tier TEXT NOT NULL DEFAULT 'personal',
            importance_score INTEGER NOT NULL DEFAULT 5,
            is_painting_eligible INTEGER NOT NULL DEFAULT 1,
            importance_rationale TEXT,
            visual_generation_status TEXT NOT NULL DEFAULT 'compiled',
            painting_image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _add_column_if_missing(
        cursor,
        "memory_objects",
        "importance_tier",
        "importance_tier TEXT NOT NULL DEFAULT 'personal'",
    )
    _add_column_if_missing(
        cursor,
        "memory_objects",
        "importance_score",
        "importance_score INTEGER NOT NULL DEFAULT 5",
    )
    _add_column_if_missing(
        cursor,
        "memory_objects",
        "is_painting_eligible",
        "is_painting_eligible INTEGER NOT NULL DEFAULT 1",
    )
    _add_column_if_missing(
        cursor, "memory_objects", "importance_rationale", "importance_rationale TEXT"
    )
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visual_entity_versions (
            version_id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            label TEXT NOT NULL,
            canonical_snapshot_json TEXT NOT NULL DEFAULT '{}',
            image_url TEXT NOT NULL,
            source_version_id TEXT,
            provider TEXT DEFAULT 'comfyui',
            provider_model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_visual_candidates (
            candidate_id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            source_visual_version_id TEXT,
            generation_type TEXT NOT NULL DEFAULT 'initial',
            canonical_snapshot_json TEXT NOT NULL DEFAULT '{}',
            canonical_delta_json TEXT NOT NULL DEFAULT '{}',
            compiled_prompt TEXT NOT NULL,
            negative_prompt TEXT,
            reference_image_url TEXT,
            workflow_role TEXT,
            provider TEXT NOT NULL DEFAULT 'mock',
            provider_model TEXT,
            provider_request_id TEXT,
            generation_seed INTEGER,
            generated_image_url TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            failure_reason TEXT,
            resulting_visual_version_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chronicle_paintings (
            painting_id TEXT PRIMARY KEY,
            memory_object_id TEXT NOT NULL,
            source_painting_id TEXT,
            generation_type TEXT NOT NULL DEFAULT 'initial',
            status TEXT NOT NULL DEFAULT 'candidate',
            guardian_status TEXT NOT NULL DEFAULT 'pending',
            compiler_version TEXT NOT NULL DEFAULT '1.0.0',
            scene_spec_json TEXT NOT NULL DEFAULT '{}',
            composition TEXT NOT NULL DEFAULT 'environmental',
            historical_participant_refs_json TEXT NOT NULL DEFAULT '[]',
            compiled_prompt TEXT NOT NULL,
            negative_prompt TEXT,
            provider TEXT NOT NULL DEFAULT 'mock',
            provider_model TEXT,
            provider_request_id TEXT,
            generation_seed INTEGER,
            quarantined_image_url TEXT,
            image_url TEXT,
            guardian_report_json TEXT,
            failure_reason TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            approved_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chronicle_painting_guardian_reports (
            report_id TEXT PRIMARY KEY,
            painting_id TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.0,
            violations_json TEXT NOT NULL DEFAULT '[]',
            correction_instructions_json TEXT NOT NULL DEFAULT '[]',
            inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_memories (
            group_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            group_significance TEXT NOT NULL DEFAULT 'personal',
            group_significance_score INTEGER NOT NULL DEFAULT 5,
            group_significance_rationale TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_memory_members (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            memory_object_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            role_in_event TEXT,
            portrait_version_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, memory_object_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_memory_tags (
            tag_id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            tag_type TEXT NOT NULL,
            value TEXT NOT NULL,
            anchor_kind TEXT,
            anchor_id TEXT,
            is_descriptor INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_memory_anchors (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            anchor_type TEXT NOT NULL,
            anchor_ref TEXT NOT NULL,
            entity_id TEXT,
            entity_type TEXT,
            label TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, anchor_type, anchor_ref)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biography_versions (
            biography_id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            title TEXT NOT NULL,
            current_chapter TEXT,
            scope_type TEXT NOT NULL DEFAULT 'full_life',
            scope_ref TEXT,
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            source_snapshot_json TEXT NOT NULL DEFAULT '{}',
            provider TEXT NOT NULL DEFAULT 'mock',
            provider_model TEXT,
            compiler_version TEXT NOT NULL DEFAULT '1.0.0',
            guardian_status TEXT NOT NULL DEFAULT 'pending',
            guardian_report_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biography_sections (
            section_id TEXT PRIMARY KEY,
            biography_id TEXT NOT NULL,
            section_type TEXT NOT NULL,
            position INTEGER NOT NULL,
            title TEXT NOT NULL,
            narrative TEXT NOT NULL,
            claim_kind TEXT NOT NULL DEFAULT 'narrative_connective',
            perspective_of TEXT,
            visual_reference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biography_provenance (
            provenance_id TEXT PRIMARY KEY,
            section_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            claim_kind TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 15: Art Direction Profiles & World Gallery. Profiles store stylistic
    # treatment only; canonical facts never live inside a style profile.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS art_direction_profiles (
            profile_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            current_version_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS art_direction_profile_versions (
            version_id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            medium_style TEXT NOT NULL DEFAULT '',
            palette_guidance TEXT NOT NULL DEFAULT '',
            lighting_guidance TEXT NOT NULL DEFAULT '',
            atmosphere TEXT NOT NULL DEFAULT '',
            texture_material TEXT NOT NULL DEFAULT '',
            camera_framing TEXT NOT NULL DEFAULT '',
            composition_guidance TEXT NOT NULL DEFAULT '',
            portrait_treatment TEXT NOT NULL DEFAULT '',
            environment_treatment TEXT NOT NULL DEFAULT '',
            relic_treatment TEXT NOT NULL DEFAULT '',
            phenomenon_treatment TEXT NOT NULL DEFAULT '',
            chronicle_treatment TEXT NOT NULL DEFAULT '',
            negative_guidance TEXT NOT NULL DEFAULT '',
            provider_hints_json TEXT NOT NULL DEFAULT '{}',
            accessibility_notes TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gallery_collections (
            collection_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            curator_soul_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gallery_collection_items (
            item_id TEXT PRIMARY KEY,
            collection_id TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            artifact_ref TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            caption TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 16: Legendary Figures & World Memory. Derived cultural memory; never
    # authoritative over canonical history. Provenance, deviations, and memory
    # state are relational, never an opaque JSON graph.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_memories (
            memory_id TEXT PRIMARY KEY,
            subject_entity_type TEXT NOT NULL,
            subject_entity_id TEXT NOT NULL,
            culture TEXT NOT NULL DEFAULT '',
            era_context TEXT NOT NULL DEFAULT '',
            memory_form TEXT NOT NULL,
            interpretation_type TEXT NOT NULL,
            title TEXT NOT NULL,
            narrative TEXT NOT NULL DEFAULT '',
            memory_state TEXT NOT NULL DEFAULT 'widely_remembered',
            remembrance_scale TEXT NOT NULL DEFAULT 'local',
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            perspective TEXT NOT NULL DEFAULT 'omniscient_narrator',
            status TEXT NOT NULL DEFAULT 'draft',
            guardian_status TEXT NOT NULL DEFAULT 'pending',
            guardian_report_json TEXT,
            version_number INTEGER NOT NULL DEFAULT 1,
            compiler_version TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'mock',
            provider_model TEXT,
            significance_rationale TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_memory_source_links (
            link_id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            claim_kind TEXT NOT NULL DEFAULT 'canonical_fact',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_memory_deviations (
            deviation_id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            deviation_kind TEXT NOT NULL,
            canon_supports TEXT NOT NULL DEFAULT '',
            legend_claims TEXT NOT NULL DEFAULT '',
            entry_note TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legendary_figures (
            figure_id TEXT PRIMARY KEY,
            subject_soul_id TEXT,
            subject_entity_type TEXT NOT NULL,
            subject_entity_id TEXT NOT NULL,
            figure_title TEXT NOT NULL,
            later_cultural_titles_json TEXT NOT NULL DEFAULT '[]',
            remembrance_scale TEXT NOT NULL DEFAULT 'regional',
            memory_state TEXT NOT NULL DEFAULT 'widely_remembered',
            eligibility_rationale TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legendary_figure_links (
            link_id TEXT PRIMARY KEY,
            figure_id TEXT NOT NULL,
            link_type TEXT NOT NULL,
            link_ref TEXT NOT NULL,
            link_label TEXT NOT NULL DEFAULT '',
            is_canonical INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_memory_placements (
            placement_id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            placement_type TEXT NOT NULL,
            placement_ref TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_memory_state_history (
            state_id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            previous_state TEXT NOT NULL,
            new_state TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 17: Campaign Orchestrator. Session/opportunity/transition state is
    # orchestrator bookkeeping, never canonical history. It coordinates existing
    # systems and records auditable reactions without duplicating their rules.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_sessions (
            session_id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            constellation_id TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            current_opportunity_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_opportunities (
            opportunity_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            opportunity_type TEXT NOT NULL,
            eligibility_rule TEXT NOT NULL,
            source_evidence_json TEXT NOT NULL DEFAULT '[]',
            involved_entities_json TEXT NOT NULL DEFAULT '[]',
            visibility_scope TEXT NOT NULL DEFAULT 'public_canon',
            urgency_class TEXT NOT NULL DEFAULT 'normal',
            participation TEXT NOT NULL DEFAULT 'optional',
            lifecycle_state TEXT NOT NULL DEFAULT 'eligible',
            cooldown_key TEXT,
            cooldown_until TEXT,
            domain_action TEXT NOT NULL DEFAULT 'none',
            domain_action_payload_json TEXT NOT NULL DEFAULT '{}',
            reasoning_json TEXT NOT NULL DEFAULT '{}',
            narration TEXT,
            narration_source TEXT NOT NULL DEFAULT 'deterministic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_transitions (
            transition_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            opportunity_id TEXT,
            canonical_event_id TEXT,
            transition_type TEXT NOT NULL,
            systems_invoked_json TEXT NOT NULL DEFAULT '[]',
            outcomes_json TEXT NOT NULL DEFAULT '[]',
            canonical_change INTEGER NOT NULL DEFAULT 0,
            provider_failure TEXT,
            rejected_invalid_transition INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_reactions (
            reaction_id TEXT PRIMARY KEY,
            transition_id TEXT NOT NULL,
            system_name TEXT NOT NULL,
            result_kind TEXT NOT NULL,
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Phase 18: Soulkeeper narrative engine. Generation metadata is bookkeeping,
    # never canonical history. It records provider/model/template/validation so
    # generated prose is auditable and template changes never rewrite canon.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS narrative_generations (
            generation_id TEXT PRIMARY KEY,
            session_id TEXT,
            opportunity_id TEXT,
            transition_id TEXT,
            provider TEXT NOT NULL,
            provider_model TEXT NOT NULL,
            template_version TEXT NOT NULL,
            generation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            retry_count INTEGER NOT NULL DEFAULT 0,
            validation_outcome TEXT NOT NULL DEFAULT 'pass',
            latency_ms INTEGER,
            used_fallback INTEGER NOT NULL DEFAULT 0,
            context_stats_json TEXT NOT NULL DEFAULT '{}',
            output_json TEXT NOT NULL DEFAULT '{}',
            error TEXT
        )
    """)

    # Phase 19: Relationship & Promise Engine. Relationships are canonical
    # history between entities; promises are claims on the future. Both carry
    # normalized provenance and are never invented by narration.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            relationship_id TEXT PRIMARY KEY,
            kind_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'active',
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            creation_context TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationship_participants (
            participant_id TEXT PRIMARY KEY,
            relationship_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'participant',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(relationship_id, entity_type, entity_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationship_source_events (
            link_id TEXT PRIMARY KEY,
            relationship_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            claim_kind TEXT NOT NULL DEFAULT 'canonical_fact',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(relationship_id, source_type, source_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationship_events (
            event_id TEXT PRIMARY KEY,
            relationship_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationship_perspectives (
            perspective_id TEXT PRIMARY KEY,
            relationship_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            view TEXT NOT NULL DEFAULT '',
            is_canonical_interaction INTEGER NOT NULL DEFAULT 0,
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationship_entity_links (
            link_id TEXT PRIMARY KEY,
            relationship_id TEXT NOT NULL,
            link_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(relationship_id, link_type, entity_type, entity_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promises (
            promise_id TEXT PRIMARY KEY,
            promisor_entity_type TEXT NOT NULL,
            promisor_entity_id TEXT NOT NULL,
            promise_text TEXT NOT NULL,
            structured_meaning_json TEXT NOT NULL DEFAULT '{}',
            conditions_json TEXT NOT NULL DEFAULT '[]',
            scope TEXT NOT NULL DEFAULT 'personal',
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_authorization TEXT NOT NULL DEFAULT 'canonical_event',
            lifecycle_state TEXT NOT NULL DEFAULT 'made',
            inheritable INTEGER NOT NULL DEFAULT 0,
            transferable INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promise_participants (
            participant_id TEXT PRIMARY KEY,
            promise_id TEXT NOT NULL,
            participant_type TEXT NOT NULL DEFAULT 'recipient',
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(promise_id, participant_type, entity_type, entity_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promise_state_history (
            state_id TEXT PRIMARY KEY,
            promise_id TEXT NOT NULL,
            previous_state TEXT NOT NULL,
            new_state TEXT NOT NULL,
            evidence_type TEXT,
            evidence_id TEXT,
            reason TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promise_entity_links (
            link_id TEXT PRIMARY KEY,
            promise_id TEXT NOT NULL,
            link_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(promise_id, link_type, entity_type, entity_id)
        )
    """)

    # Track which Art Direction Profile/version produced a generated candidate.
    _add_column_if_missing(
        cursor,
        "portrait_generation_candidates",
        "art_direction_profile_id",
        "art_direction_profile_id TEXT",
    )
    _add_column_if_missing(
        cursor,
        "portrait_generation_candidates",
        "art_direction_profile_version_id",
        "art_direction_profile_version_id TEXT",
    )
    _add_column_if_missing(
        cursor,
        "world_visual_candidates",
        "art_direction_profile_id",
        "art_direction_profile_id TEXT",
    )
    _add_column_if_missing(
        cursor,
        "world_visual_candidates",
        "art_direction_profile_version_id",
        "art_direction_profile_version_id TEXT",
    )
    _add_column_if_missing(
        cursor,
        "chronicle_paintings",
        "art_direction_profile_id",
        "art_direction_profile_id TEXT",
    )
    _add_column_if_missing(
        cursor,
        "chronicle_paintings",
        "art_direction_profile_version_id",
        "art_direction_profile_version_id TEXT",
    )

    # Phase 20: multi-Aspect campaign sessions. A session is campaign-level;
    # ``soul_id`` records the default/owner Aspect while ``active_soul_id``
    # tracks the currently active playable Aspect (mutable via switching).
    _add_column_if_missing(
        cursor, "campaign_sessions", "active_soul_id", "active_soul_id TEXT"
    )

    # Phase 20: playable Aspects registered to a campaign. Each Aspect is an
    # independent structured viewpoint; registration is idempotent per
    # (campaign_id, soul_id).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_aspects (
            campaign_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            aspect_id TEXT,
            display_name TEXT NOT NULL,
            viewpoint_location TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (campaign_id, soul_id)
        )
    """)

    # Phase 20: Aspect-switch audit log. Bookkeeping only, never canonical
    # history. Idempotent switches are recorded with ``idempotent = 1``.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aspect_switches (
            switch_id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            from_soul_id TEXT NOT NULL,
            to_soul_id TEXT NOT NULL,
            idempotent INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 20: persistent place/location entities. Precise coordinates are
    # stored separately and only with consent; public representation uses a
    # reduced-precision region label.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            place_id TEXT PRIMARY KEY,
            place_name TEXT NOT NULL,
            place_kind TEXT NOT NULL DEFAULT 'interpretive',
            public_label TEXT,
            region_id TEXT,
            region_precision TEXT NOT NULL DEFAULT 'reduced',
            coordinate_latitude REAL,
            coordinate_longitude REAL,
            coordinate_precision_m TEXT NOT NULL DEFAULT 'coarse',
            consent_scope TEXT NOT NULL DEFAULT 'private',
            safety_status TEXT NOT NULL DEFAULT 'unknown',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_by_soul_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 20: a place accumulates history without owning it. Provenance links
    # to canonical records; visibility is consent-filtered at read time.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS place_history (
            history_id TEXT PRIMARY KEY,
            place_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_id TEXT NOT NULL,
            soul_id TEXT,
            provenance_source_type TEXT NOT NULL,
            provenance_source_id TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'public_canon',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 20: location consent is opt-in and per-soul, with a purpose and a
    # precision cap. No location sample is accepted without this grant.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS location_consent (
            soul_id TEXT PRIMARY KEY,
            location_access_granted INTEGER NOT NULL DEFAULT 0,
            purpose TEXT NOT NULL DEFAULT '',
            precision_level TEXT NOT NULL DEFAULT 'coarse',
            retention_days INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 20: authorized location samples. Stored precision is minimized and
    # the raw sample is never exposed publicly.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS location_samples (
            sample_id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            precision_m REAL NOT NULL,
            purpose TEXT NOT NULL,
            consent_scope TEXT NOT NULL DEFAULT 'private',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 20: wandering discoveries. A bounded deterministic record of what
    # nearby eligible content was surfaced to an Aspect; hidden canonical
    # details are never embedded here.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wandering_discoveries (
            discovery_id TEXT PRIMARY KEY,
            soul_id TEXT NOT NULL,
            place_id TEXT,
            opportunity_type TEXT NOT NULL,
            opportunity_id TEXT,
            hidden_details_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 21: Living Visual World. Art Moments record *what the Art Director
    # found worth painting*; VisualJobs record the auditable generation lifecycle.
    # Neither is canonical history: approved art is an interpretation, not evidence.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS art_moments (
            art_moment_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            visual_type TEXT NOT NULL,
            cooldown_key TEXT,
            eligibility_rule TEXT NOT NULL,
            source_entity_type TEXT,
            source_entity_id TEXT,
            title TEXT NOT NULL,
            source_evidence_json TEXT NOT NULL DEFAULT '[]',
            reference_asset_ids_json TEXT NOT NULL DEFAULT '[]',
            spec_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'eligible',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visual_jobs (
            job_id TEXT PRIMARY KEY,
            art_moment_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            visual_type TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'mock',
            provider_model TEXT,
            workflow_role TEXT,
            workflow_version TEXT NOT NULL DEFAULT '1.0.0',
            provider_request_id TEXT,
            generation_seed INTEGER,
            generation_state TEXT NOT NULL DEFAULT 'queued',
            retry_count INTEGER NOT NULL DEFAULT 0,
            spec_json TEXT NOT NULL DEFAULT '{}',
            reference_asset_ids_json TEXT NOT NULL DEFAULT '[]',
            quarantined_image_url TEXT,
            final_image_url TEXT,
            guardian_status TEXT NOT NULL DEFAULT 'pending',
            guardian_report_json TEXT,
            failure_reason TEXT,
            superseded_job_id TEXT,
            contributor_id TEXT,
            contributor_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visual_job_guardian_reports (
            report_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.0,
            violations_json TEXT NOT NULL DEFAULT '[]',
            correction_instructions_json TEXT NOT NULL DEFAULT '[]',
            inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visual_curations (
            curation_id TEXT PRIMARY KEY,
            art_moment_id TEXT NOT NULL,
            contributor_id TEXT NOT NULL,
            contributor_name TEXT,
            style_guidance TEXT NOT NULL DEFAULT '',
            composition TEXT NOT NULL DEFAULT '',
            mood TEXT NOT NULL DEFAULT '',
            motif TEXT NOT NULL DEFAULT '',
            symbolism TEXT NOT NULL DEFAULT '',
            provenance_note TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 22: Temporal Pacing & Living Time. Time authority columns are
    # appended lazily (after all tables exist) and never reorder canon.
    _add_column_if_missing(
        cursor, "campaign_sessions", "last_active_at", "last_active_at TIMESTAMP"
    )
    _add_column_if_missing(
        cursor, "seeds", "last_echo_at", "last_echo_at TIMESTAMP"
    )
    _add_column_if_missing(
        cursor, "promises", "deadline_iso", "deadline_iso TEXT"
    )
    _add_column_if_missing(
        cursor,
        "promises",
        "deadline_source_type",
        "deadline_source_type TEXT",
    )
    _add_column_if_missing(
        cursor,
        "promises",
        "deadline_source_id",
        "deadline_source_id TEXT",
    )
    _add_column_if_missing(
        cursor,
        "relationships",
        "last_interaction_at",
        "last_interaction_at TIMESTAMP",
    )
    _add_column_if_missing(
        cursor, "places", "last_visited_at", "last_visited_at TIMESTAMP"
    )

    # Phase 22: Temporal Pacing & Living Time. These are bookkeeping/eligibility
    # records, never canonical history. Time policy changes never reorder canon.

    # Campaign-level time authority: explicit policy + timezone + fictional clock.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_time_settings (
            campaign_id TEXT PRIMARY KEY,
            time_policy TEXT NOT NULL DEFAULT 'none',
            timezone TEXT NOT NULL DEFAULT 'UTC',
            real_time_ratio REAL,
            fictional_anchor_iso TEXT,
            fictional_now_iso TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Aspect-relative temporal state. Preserved across switches so each Aspect
    # keeps its own last-active time and deterministic event count.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aspect_temporal_state (
            campaign_id TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            last_active_at TIMESTAMP,
            deterministic_event_count INTEGER NOT NULL DEFAULT 0,
            fictional_now_iso TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (campaign_id, soul_id)
        )
    """)

    # Idempotent wall-clock cooldown ledger. Repeated evaluations at the same
    # effective time never duplicate opportunities.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temporal_cooldowns (
            cooldown_key TEXT PRIMARY KEY,
            last_offered_at TEXT,
            last_offered_event_count INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Provenance-backed delayed/scheduled consequences. Each references the
    # canonical event/rule that created it; the narrator cannot mint timers.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_consequences (
            consequence_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            rule TEXT NOT NULL,
            eligible_after_iso TEXT,
            min_elapsed_seconds REAL,
            min_events INTEGER,
            note TEXT NOT NULL DEFAULT '',
            lifecycle_state TEXT NOT NULL DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
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
    canon_facts: list[str],
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


def _json_or_none(value: str | None) -> Any:
    return json.loads(value) if value else None


def get_all_canonical_events() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scene_events ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_canonical_event_row(row) for row in rows]


def _map_canonical_event_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "soul_name": row["soul_id"],
        "soul_id": row["soul_id"],
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


def get_canonical_events_for_soul(soul_id: str) -> list[dict[str, Any]]:
    """Aspect-scoped Chronicle visibility. The campaign-level Chronicle is the
    canonical truth; an Aspect only sees events they participated in. This is the
    Phase 20 boundary between CANONICAL TRUTH and ASPECT KNOWLEDGE."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM scene_events WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_canonical_event_row(row) for row in rows]


# Curiosity & Thread Database Helpers


def plant_or_echo_seed(
    *,
    symbol: str,
    thread_type: str,
    narrative_context: str,
    soul_id: str | None = "Unbound Soul",
    initial_question: str | None = None,
) -> dict[str, Any]:
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
            SET echo_count = ?, stage = ?, updated_at = CURRENT_TIMESTAMP,
                last_echo_at = CURRENT_TIMESTAMP
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
            INSERT INTO seeds (id, world_id, soul_id, symbol, thread_type, stage, echo_count, narrative_context, last_echo_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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


def get_all_seeds() -> list[dict[str, Any]]:
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
            "last_echo_at": row["last_echo_at"]
            if "last_echo_at" in row.keys()
            else row["updated_at"],
        }
        for row in rows
    ]


def get_all_open_questions() -> list[dict[str, Any]]:
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


def get_seeds_for_soul(soul_id: str) -> list[dict[str, Any]]:
    """Aspect-scoped Seeds. A Seed belongs to the Aspect that planted it; an
    orphaned Seed (no soul_id) remains visible to every Aspect as legacy world
    texture. This is the Phase 20 knowledge boundary for Curiosity state."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM seeds WHERE soul_id = ? OR soul_id IS NULL ORDER BY updated_at DESC",
        (soul_id,),
    )
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
            "last_echo_at": row["last_echo_at"]
            if "last_echo_at" in row.keys()
            else row["updated_at"],
        }
        for row in rows
    ]


def get_open_questions_for_soul(soul_id: str) -> list[dict[str, Any]]:
    """Aspect-scoped open questions, joined through their owning Seed. A question
    whose Seed has no owner is legacy/global and stays visible."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT q.* FROM open_questions q
        LEFT JOIN seeds s ON s.id = q.seed_id
        WHERE s.soul_id IS NULL OR s.soul_id = ?
        ORDER BY q.created_at DESC
    """,
        (soul_id,),
    )
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


def get_all_local_threads(soul_id: str = "Unbound Soul") -> list[dict[str, Any]]:
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
    target_relic_id: str | None = None,
) -> dict[str, Any]:
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


def get_or_create_primary_constellation() -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
    *, constellation_id: str, target_stage: str | None = None
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
    event_id: str | None = None,
    manifestation_type: str = "dream",
    provenance_summary: str | None = None,
) -> dict[str, Any]:
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


def get_probable_paths_records(soul_id: str | None = None) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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


def get_user_by_email(email: str) -> dict[str, Any] | None:
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


def get_user_by_username(username: str) -> dict[str, Any] | None:
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


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
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
) -> list[dict[str, Any]]:
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


def get_relic_history_records(relic_id: str) -> list[dict[str, Any]]:
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
    new_effect: str | None = None,
    is_anchor: bool | None = None,
) -> dict[str, Any]:
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


def get_community_symbols_records() -> list[dict[str, Any]]:
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
    contributing_souls: list[str],
    canon_status: str = "opt_in_shared",
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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


def get_reflections_records(soul_id: str) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
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


def get_private_notes_records(soul_id: str) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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


def get_story_marks_records(soul_id: str) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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


def get_portrait_versions_records(soul_id: str) -> list[dict[str, Any]]:
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
) -> dict[str, Any]:
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
    participants: list[dict[str, Any]],
    location_environment: str,
    relics_involved: list[str],
    emotional_tone: str,
    action_composition: str,
    lasting_consequence: str,
    privacy_consent_scope: str = "public_canon",
    importance_tier: str = "personal",
    importance_score: int | None = None,
    importance_rationale: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    mem_id = f"mem_{str(uuid.uuid4())[:8]}"

    normalized_scope = privacy_consent_scope.strip().lower()
    redacted_real_person_tags: list[str] = []

    # Importance score logic
    if importance_score is None:
        if importance_tier == "world":
            score = 9
        elif importance_tier == "community":
            score = 7
        else:
            score = 5
    else:
        score = max(1, min(10, importance_score))

    is_eligible = 1 if score >= 4 else 0
    rationale = (
        importance_rationale
        or f"Compiled as {importance_tier} significance event with score {score}/10."
    )

    # Enrich participant historical appearance snapshots if available
    enriched_participants = []
    for p in participants:
        p_copy = dict(p)
        participant_soul_id = p_copy.get("soul_id")

        cursor.execute(
            "SELECT * FROM visual_consent_settings WHERE soul_id = ?",
            (participant_soul_id,),
        )
        consent_row = cursor.fetchone()
        allow_shared_gallery = (
            bool(consent_row["allow_shared_gallery"]) if consent_row else True
        )
        allow_real_person_tagging = (
            bool(consent_row["allow_real_person_tagging"]) if consent_row else False
        )

        if normalized_scope == "public_canon" and not allow_shared_gallery:
            conn.close()
            raise ValueError(
                f"Soul '{participant_soul_id}' has not consented to shared gallery publication."
            )

        if p_copy.get("real_person_tag_opt_in") and not allow_real_person_tagging:
            p_copy["real_person_tag_opt_in"] = False
            redacted_real_person_tags.append(participant_soul_id)

        pv_id = p.get("portrait_version_id")
        cursor.execute(
            "SELECT * FROM portrait_versions WHERE version_id = ?",
            (pv_id,),
        )
        pv_row = cursor.fetchone()
        if not pv_row:
            conn.close()
            raise ValueError(
                f"Participant '{participant_soul_id}' references unknown portrait version '{pv_id}'."
            )
        if pv_row["soul_id"] != participant_soul_id:
            conn.close()
            raise ValueError(
                f"Portrait version '{pv_id}' does not belong to soul '{participant_soul_id}'."
            )

        if (
            "historical_story_marks_snapshot" not in p_copy
            or not p_copy["historical_story_marks_snapshot"]
        ):
            p_copy["historical_story_marks_snapshot"] = (
                _json_or_none(pv_row["story_marks_snapshot_json"]) or []
            )
            p_copy["historical_equipment_snapshot"] = _json_or_none(
                pv_row["equipment_snapshot_json"]
            )
        enriched_participants.append(p_copy)

    if redacted_real_person_tags:
        redacted_list = ", ".join(redacted_real_person_tags)
        rationale = (
            f"{rationale} Real-person tagging removed for: {redacted_list} "
            "due to missing consent."
        )

    cursor.execute(
        """
        INSERT INTO memory_objects (
            id, event_id, event_title, participants_json, location_environment,
            relics_involved_json, emotional_tone, action_composition, lasting_consequence,
            privacy_consent_scope, importance_tier, importance_score, is_painting_eligible,
            importance_rationale, visual_generation_status, painting_image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'compiled', ?)
    """,
        (
            mem_id,
            event_id,
            event_title,
            json.dumps(enriched_participants),
            location_environment,
            json.dumps(relics_involved),
            emotional_tone,
            action_composition,
            lasting_consequence,
            privacy_consent_scope,
            importance_tier,
            score,
            is_eligible,
            rationale,
            f"/assets/paintings/{event_id}_painting.png",
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": mem_id,
        "event_id": event_id,
        "event_title": event_title,
        "participants": enriched_participants,
        "location_environment": location_environment,
        "relics_involved": relics_involved,
        "emotional_tone": emotional_tone,
        "action_composition": action_composition,
        "lasting_consequence": lasting_consequence,
        "privacy_consent_scope": privacy_consent_scope,
        "importance_tier": importance_tier,
        "importance_score": score,
        "is_painting_eligible": bool(is_eligible),
        "importance_rationale": rationale,
        "visual_generation_status": "compiled",
        "painting_image_url": f"/assets/paintings/{event_id}_painting.png",
    }


def get_memory_objects_records() -> list[dict[str, Any]]:
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
            "importance_tier": r["importance_tier"],
            "importance_score": r["importance_score"],
            "is_painting_eligible": bool(r["is_painting_eligible"]),
            "importance_rationale": r["importance_rationale"],
            "visual_generation_status": r["visual_generation_status"],
            "painting_image_url": r["painting_image_url"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def get_memory_object_record(mem_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory_objects WHERE id = ?", (mem_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {
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
        "importance_tier": r["importance_tier"],
        "importance_score": r["importance_score"],
        "is_painting_eligible": bool(r["is_painting_eligible"]),
        "importance_rationale": r["importance_rationale"],
        "visual_generation_status": r["visual_generation_status"],
        "painting_image_url": r["painting_image_url"],
        "created_at": r["created_at"],
    }


# Phase 10: Candidate & Continuity DB Helpers


def _map_candidate_row(row: sqlite3.Row) -> dict[str, Any]:
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
        "art_direction_profile_id": row["art_direction_profile_id"],
        "art_direction_profile_version_id": row["art_direction_profile_version_id"],
        "created_at": row["created_at"],
        "reviewed_at": row["reviewed_at"],
    }


def create_portrait_candidate_record(
    *,
    soul_id: str,
    generation_type: str,
    compiled_prompt: str,
    canonical_identity_snapshot: dict[str, Any],
    story_marks_snapshot: list[dict[str, Any]],
    equipment_snapshot: dict[str, Any] | None = None,
    source_portrait_version_id: str | None = None,
    reference_image_url: str | None = None,
    negative_prompt: str | None = None,
    art_direction_profile_id: str | None = None,
    art_direction_profile_version_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cand_id = f"cand_{str(uuid.uuid4())[:8]}"

    cursor.execute(
        """
        INSERT INTO portrait_generation_candidates (
            candidate_id, soul_id, source_portrait_version_id, generation_type,
            compiled_prompt, negative_prompt, reference_image_url,
            canonical_identity_snapshot_json, story_marks_snapshot_json, equipment_snapshot_json,
            art_direction_profile_id, art_direction_profile_version_id,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
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
            art_direction_profile_id,
            art_direction_profile_version_id,
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
    generated_image_url: str | None = None,
    provider: str = "mock",
    provider_model: str = "soulsmith-mock-v1",
    provider_request_id: str | None = None,
    generation_seed: int | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
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
    custom_label: str | None = None,
) -> dict[str, Any]:
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


def reject_portrait_candidate_record(candidate_id: str, soul_id: str) -> dict[str, Any]:
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


def get_portrait_candidate_record(candidate_id: str) -> dict[str, Any] | None:
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


def get_portrait_candidates_records(soul_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM portrait_generation_candidates WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_candidate_row(r) for r in rows]


def get_portrait_version_record(version_id: str) -> dict[str, Any] | None:
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


# Phase 4: Visual Worldsmith DB Helpers


def _map_visual_version_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "version_id": r["version_id"],
        "entity_id": r["entity_id"],
        "entity_type": r["entity_type"],
        "version_number": r["version_number"],
        "label": r["label"],
        "canonical_snapshot": _json_or_none(r["canonical_snapshot_json"]) or {},
        "image_url": r["image_url"],
        "source_version_id": r["source_version_id"],
        "provider": r["provider"],
        "provider_model": r["provider_model"],
        "created_at": r["created_at"],
    }


def _map_world_candidate_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "candidate_id": r["candidate_id"],
        "entity_id": r["entity_id"],
        "entity_type": r["entity_type"],
        "source_visual_version_id": r["source_visual_version_id"],
        "generation_type": r["generation_type"],
        "canonical_snapshot": _json_or_none(r["canonical_snapshot_json"]) or {},
        "canonical_delta": _json_or_none(r["canonical_delta_json"]) or {},
        "compiled_prompt": r["compiled_prompt"],
        "negative_prompt": r["negative_prompt"],
        "reference_image_url": r["reference_image_url"],
        "workflow_role": r["workflow_role"],
        "provider": r["provider"],
        "provider_model": r["provider_model"],
        "provider_request_id": r["provider_request_id"],
        "generation_seed": r["generation_seed"],
        "generated_image_url": r["generated_image_url"],
        "status": r["status"],
        "failure_reason": r["failure_reason"],
        "resulting_visual_version_id": r["resulting_visual_version_id"],
        "art_direction_profile_id": r["art_direction_profile_id"],
        "art_direction_profile_version_id": r["art_direction_profile_version_id"],
        "created_at": r["created_at"],
        "reviewed_at": r["reviewed_at"],
    }


def create_world_visual_candidate_record(
    *,
    entity_id: str,
    entity_type: str,
    generation_type: str,
    canonical_snapshot: dict[str, Any],
    canonical_delta: dict[str, Any],
    compiled_prompt: str,
    workflow_role: str,
    negative_prompt: str | None = None,
    source_visual_version_id: str | None = None,
    reference_image_url: str | None = None,
    art_direction_profile_id: str | None = None,
    art_direction_profile_version_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cand_id = f"wvc_{str(uuid.uuid4())[:8]}"

    cursor.execute(
        """
        INSERT INTO world_visual_candidates (
            candidate_id, entity_id, entity_type, source_visual_version_id,
            generation_type, canonical_snapshot_json, canonical_delta_json,
            compiled_prompt, negative_prompt, reference_image_url, workflow_role,
            art_direction_profile_id, art_direction_profile_version_id,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """,
        (
            cand_id,
            entity_id,
            entity_type,
            source_visual_version_id,
            generation_type,
            json.dumps(canonical_snapshot),
            json.dumps(canonical_delta),
            compiled_prompt,
            negative_prompt,
            reference_image_url,
            workflow_role,
            art_direction_profile_id,
            art_direction_profile_version_id,
        ),
    )
    conn.commit()

    cursor.execute(
        "SELECT * FROM world_visual_candidates WHERE candidate_id = ?", (cand_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_world_candidate_row(row)


def update_world_visual_candidate_result(
    candidate_id: str,
    *,
    status: str,
    generated_image_url: str | None = None,
    provider: str = "comfyui",
    provider_model: str | None = None,
    provider_request_id: str | None = None,
    generation_seed: int | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE world_visual_candidates
        SET status = ?, generated_image_url = ?, provider = ?, provider_model = ?,
            provider_request_id = ?, generation_seed = ?, failure_reason = ?
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
        "SELECT * FROM world_visual_candidates WHERE candidate_id = ?", (candidate_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Candidate {candidate_id} not found")
    return _map_world_candidate_row(row)


def approve_world_visual_candidate_transaction(
    candidate_id: str, label: str | None = None
) -> dict[str, Any]:
    """
    Transactionally approve a generated world candidate into an immutable
    VisualEntityVersion. Idempotent: repeated approval returns the existing version.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM world_visual_candidates WHERE candidate_id = ?",
            (candidate_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Candidate '{candidate_id}' not found")

        if row["status"] == "approved" and row["resulting_visual_version_id"]:
            version_id = row["resulting_visual_version_id"]
            cursor.execute(
                "SELECT * FROM visual_entity_versions WHERE version_id = ?",
                (version_id,),
            )
            version_row = cursor.fetchone()
            conn.close()
            if version_row:
                return _map_visual_version_row(version_row)

        if row["status"] != "generated":
            conn.close()
            raise ValueError(
                f"Cannot approve candidate '{candidate_id}' in status '{row['status']}'. Must be in 'generated' state."
            )
        if not row["generated_image_url"]:
            conn.close()
            raise ValueError(f"Candidate '{candidate_id}' has no generated_image_url.")

        cursor.execute(
            "SELECT COUNT(*) as count FROM visual_entity_versions WHERE entity_id = ? AND entity_type = ?",
            (row["entity_id"], row["entity_type"]),
        )
        version_num = (cursor.fetchone()["count"] or 0) + 1
        version_id = f"wvv_{version_num}_{str(uuid.uuid4())[:8]}"
        version_label = (
            label
            or f"{row['entity_type'].replace('_', ' ').title()} v{version_num} ({row['generation_type'].replace('_', ' ').title()})"
        )

        cursor.execute(
            """
            INSERT INTO visual_entity_versions (
                version_id, entity_id, entity_type, version_number, label,
                canonical_snapshot_json, image_url, source_version_id,
                provider, provider_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                version_id,
                row["entity_id"],
                row["entity_type"],
                version_num,
                version_label,
                row["canonical_snapshot_json"],
                row["generated_image_url"],
                row["source_visual_version_id"],
                row["provider"],
                row["provider_model"],
            ),
        )
        cursor.execute(
            """
            UPDATE world_visual_candidates
            SET status = 'approved', resulting_visual_version_id = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE candidate_id = ?
        """,
            (version_id, candidate_id),
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM visual_entity_versions WHERE version_id = ?", (version_id,)
        )
        version_row = cursor.fetchone()
        conn.close()
        return _map_visual_version_row(version_row)
    except Exception:
        conn.rollback()
        conn.close()
        raise


def reject_world_visual_candidate_record(candidate_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_visual_candidates WHERE candidate_id = ?", (candidate_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Candidate '{candidate_id}' not found")
    if row["status"] == "approved":
        conn.close()
        raise ValueError(
            f"Candidate '{candidate_id}' has already been approved and cannot be rejected."
        )
    cursor.execute(
        "UPDATE world_visual_candidates SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP WHERE candidate_id = ?",
        (candidate_id,),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM world_visual_candidates WHERE candidate_id = ?", (candidate_id,)
    )
    updated = cursor.fetchone()
    conn.close()
    return _map_world_candidate_row(updated)


def get_world_visual_candidate_record(candidate_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_visual_candidates WHERE candidate_id = ?", (candidate_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_world_candidate_row(row) if row else None


def get_world_visual_candidates_records(
    entity_type: str, entity_id: str
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_visual_candidates WHERE entity_type = ? AND entity_id = ? ORDER BY created_at ASC",
        (entity_type, entity_id),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_world_candidate_row(r) for r in rows]


def get_visual_entity_versions_records(
    entity_type: str, entity_id: str
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_entity_versions WHERE entity_type = ? AND entity_id = ? ORDER BY version_number ASC",
        (entity_type, entity_id),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_visual_version_row(r) for r in rows]


def get_visual_entity_version_record(version_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_entity_versions WHERE version_id = ?", (version_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_visual_version_row(row) if row else None


# Phase 12: Chronicle Paintings DB Helpers


def _map_chronicle_painting_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "painting_id": row["painting_id"],
        "memory_object_id": row["memory_object_id"],
        "source_painting_id": row["source_painting_id"],
        "generation_type": row["generation_type"],
        "status": row["status"],
        "guardian_status": row["guardian_status"],
        "compiler_version": row["compiler_version"],
        "scene_spec": _json_or_none(row["scene_spec_json"]) or {},
        "composition": row["composition"],
        "historical_participant_refs": _json_or_none(
            row["historical_participant_refs_json"]
        )
        or [],
        "compiled_prompt": row["compiled_prompt"],
        "negative_prompt": row["negative_prompt"],
        "provider": row["provider"],
        "provider_model": row["provider_model"],
        "provider_request_id": row["provider_request_id"],
        "generation_seed": row["generation_seed"],
        "quarantined_image_url": row["quarantined_image_url"],
        "image_url": row["image_url"],
        "guardian_report": _json_or_none(row["guardian_report_json"]),
        "failure_reason": row["failure_reason"],
        "retry_count": row["retry_count"],
        "art_direction_profile_id": row["art_direction_profile_id"],
        "art_direction_profile_version_id": row["art_direction_profile_version_id"],
        "created_at": row["created_at"],
        "reviewed_at": row["reviewed_at"],
        "approved_at": row["approved_at"],
    }


def _map_guardian_report_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "report_id": row["report_id"],
        "painting_id": row["painting_id"],
        "status": row["status"],
        "confidence": row["confidence"],
        "violations": _json_or_none(row["violations_json"]) or [],
        "correction_instructions": _json_or_none(row["correction_instructions_json"])
        or [],
        "inspected_at": row["inspected_at"],
    }


def create_chronicle_painting_record(
    *,
    memory_object_id: str,
    generation_type: str,
    compiled_prompt: str,
    scene_spec: dict[str, Any],
    composition: str,
    historical_participant_refs: list[dict[str, Any]],
    negative_prompt: str | None = None,
    source_painting_id: str | None = None,
    retry_count: int = 0,
    art_direction_profile_id: str | None = None,
    art_direction_profile_version_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    painting_id = f"pnt_{str(uuid.uuid4())[:8]}"

    cursor.execute(
        """
        INSERT INTO chronicle_paintings (
            painting_id, memory_object_id, source_painting_id, generation_type,
            status, guardian_status, compiler_version, scene_spec_json, composition,
            historical_participant_refs_json, compiled_prompt, negative_prompt,
            art_direction_profile_id, art_direction_profile_version_id,
            retry_count
        ) VALUES (?, ?, ?, ?, 'candidate', 'pending', '1.0.0', ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            painting_id,
            memory_object_id,
            source_painting_id,
            generation_type,
            json.dumps(scene_spec),
            composition,
            json.dumps(historical_participant_refs),
            compiled_prompt,
            negative_prompt,
            art_direction_profile_id,
            art_direction_profile_version_id,
            retry_count,
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_chronicle_painting_row(row)


def update_chronicle_painting_generation(
    painting_id: str,
    *,
    guardian_status: str,
    status: str | None = None,
    quarantined_image_url: str | None = None,
    provider: str | None = None,
    provider_model: str | None = None,
    provider_request_id: str | None = None,
    generation_seed: int | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE chronicle_paintings
        SET guardian_status = ?,
            status = COALESCE(?, status),
            quarantined_image_url = COALESCE(?, quarantined_image_url),
            provider = COALESCE(?, provider),
            provider_model = COALESCE(?, provider_model),
            provider_request_id = COALESCE(?, provider_request_id),
            generation_seed = COALESCE(?, generation_seed),
            failure_reason = ?,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE painting_id = ?
    """,
        (
            guardian_status,
            status,
            quarantined_image_url,
            provider,
            provider_model,
            provider_request_id,
            generation_seed,
            failure_reason,
            painting_id,
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Painting '{painting_id}' not found")
    return _map_chronicle_painting_row(row)


def update_chronicle_painting_promotion(
    painting_id: str,
    *,
    image_url: str,
    guardian_report: dict[str, Any],
    status: str = "candidate",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE chronicle_paintings
        SET image_url = ?,
            guardian_report_json = ?,
            guardian_status = 'passed',
            status = ?,
            failure_reason = NULL,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE painting_id = ?
    """,
        (image_url, json.dumps(guardian_report), status, painting_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Painting '{painting_id}' not found")
    return _map_chronicle_painting_row(row)


def record_chronicle_painting_guardian_report(
    painting_id: str, report: dict[str, Any]
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    report_id = f"vgr_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO chronicle_painting_guardian_reports (
            report_id, painting_id, status, confidence, violations_json,
            correction_instructions_json
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            report_id,
            painting_id,
            report.get("status"),
            report.get("confidence", 0.0),
            json.dumps(report.get("violations") or []),
            json.dumps(report.get("correction_instructions") or []),
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM chronicle_painting_guardian_reports WHERE report_id = ?",
        (report_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_guardian_report_row(row)


def get_chronicle_painting_guardian_reports(
    painting_id: str,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chronicle_painting_guardian_reports WHERE painting_id = ? "
        "ORDER BY inspected_at ASC",
        (painting_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_guardian_report_row(r) for r in rows]


def get_chronicle_painting_record(painting_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_chronicle_painting_row(row) if row else None


def get_chronicle_paintings_records(
    memory_object_id: str,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE memory_object_id = ? "
        "ORDER BY created_at ASC",
        (memory_object_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_chronicle_painting_row(r) for r in rows]


def get_approved_chronicle_paintings_records() -> list[dict[str, Any]]:
    """
    Gallery-ready query: only approved paintings with a promoted SoulSmith-owned
    image URL are returned, joined with useful memory metadata.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, m.event_id AS memory_event_id, m.event_title AS memory_event_title
        FROM chronicle_paintings p
        JOIN memory_objects m ON m.id = p.memory_object_id
        WHERE p.status = 'approved' AND p.image_url IS NOT NULL
          AND m.privacy_consent_scope = 'public_canon'
        ORDER BY p.approved_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        painting = _map_chronicle_painting_row(r)
        painting["memory_event_id"] = r["memory_event_id"]
        painting["memory_event_title"] = r["memory_event_title"]
        results.append(painting)
    return results


def approve_chronicle_painting_transaction(
    painting_id: str,
) -> dict[str, Any]:
    """
    Approve a Guardian-passed candidate as the preferred artistic interpretation
    of its Memory Object. Approving a replacement supersedes the previous
    approved painting without deleting historical candidates. Idempotent.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Painting '{painting_id}' not found")

        if row["status"] == "approved":
            conn.close()
            return _map_chronicle_painting_row(row)

        if row["status"] != "candidate":
            conn.close()
            raise ValueError(
                f"Cannot approve painting '{painting_id}' in status "
                f"'{row['status']}'. Must be a Guardian-passed candidate."
            )
        if not row["image_url"]:
            conn.close()
            raise ValueError(f"Painting '{painting_id}' has no promoted image URL.")
        if row["guardian_status"] != "passed":
            conn.close()
            raise ValueError(
                f"Painting '{painting_id}' has not passed the Visual Canon Guardian."
            )

        memory_object_id = row["memory_object_id"]

        # Supersede any previously approved painting for this memory object.
        cursor.execute(
            """
            UPDATE chronicle_paintings
            SET status = 'superseded'
            WHERE memory_object_id = ? AND status = 'approved'
        """,
            (memory_object_id,),
        )

        cursor.execute(
            """
            UPDATE chronicle_paintings
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE painting_id = ?
        """,
            (painting_id,),
        )

        # Point the Memory Object at the newly approved artistic interpretation.
        cursor.execute(
            """
            UPDATE memory_objects
            SET visual_generation_status = 'painting_approved',
                painting_image_url = ?
            WHERE id = ?
        """,
            (row["image_url"], memory_object_id),
        )

        conn.commit()

        cursor.execute(
            "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
        )
        approved_row = cursor.fetchone()
        conn.close()
        return _map_chronicle_painting_row(approved_row)
    except Exception:
        conn.rollback()
        conn.close()
        raise


def reject_chronicle_painting_record(painting_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Painting '{painting_id}' not found")
    if row["status"] == "approved":
        conn.close()
        raise ValueError(
            f"Painting '{painting_id}' has already been approved and cannot be rejected."
        )
    cursor.execute(
        """
        UPDATE chronicle_paintings
        SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP
        WHERE painting_id = ?
    """,
        (painting_id,),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM chronicle_paintings WHERE painting_id = ?", (painting_id,)
    )
    updated = cursor.fetchone()
    conn.close()
    return _map_chronicle_painting_row(updated)


# Phase 13: Group Memories & Tags DB Helpers


def _map_group_memory_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "group_id": row["group_id"],
        "event_id": row["event_id"],
        "title": row["title"],
        "summary": row["summary"],
        "visibility": row["visibility"],
        "group_significance": row["group_significance"],
        "group_significance_score": row["group_significance_score"],
        "group_significance_rationale": row["group_significance_rationale"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _map_group_member_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "group_id": row["group_id"],
        "memory_object_id": row["memory_object_id"],
        "soul_id": row["soul_id"],
        "role_in_event": row["role_in_event"],
        "portrait_version_id": row["portrait_version_id"],
        "created_at": row["created_at"],
    }


def _map_group_tag_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "tag_id": row["tag_id"],
        "group_id": row["group_id"],
        "tag_type": row["tag_type"],
        "value": row["value"],
        "anchor_kind": row["anchor_kind"],
        "anchor_id": row["anchor_id"],
        "is_descriptor": bool(row["is_descriptor"]),
        "created_at": row["created_at"],
    }


def _map_group_anchor_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "anchor_type": row["anchor_type"],
        "anchor_ref": row["anchor_ref"],
        "entity_id": row["entity_id"],
        "entity_type": row["entity_type"],
        "label": row["label"],
        "created_at": row["created_at"],
    }


def create_group_memory_record(
    *,
    event_id: str,
    visibility: str = "public_canon",
    title: str = "A Shared Event",
    summary: str = "The details of this shared event remain private.",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    group_id = f"grp_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO group_memories (
            group_id, event_id, title, summary, visibility
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (group_id, event_id, title, summary, visibility),
    )
    conn.commit()
    cursor.execute("SELECT * FROM group_memories WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_group_memory_row(row)


def update_group_memory_significance_record(
    group_id: str,
    *,
    significance: str,
    score: int,
    rationale: str | None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE group_memories
        SET group_significance = ?,
            group_significance_score = ?,
            group_significance_rationale = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE group_id = ?
    """,
        (significance, score, rationale, group_id),
    )
    conn.commit()
    cursor.execute("SELECT * FROM group_memories WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Group memory '{group_id}' not found")
    return _map_group_memory_row(row)


def get_group_memory_record(group_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_memories WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_group_memory_row(row) if row else None


def get_group_memory_by_event_record(event_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM group_memories WHERE event_id = ? ORDER BY created_at DESC "
        "LIMIT 1",
        (event_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_group_memory_row(row) if row else None


def list_group_memory_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_memories ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_group_memory_row(r) for r in rows]


def add_group_memory_member_record(
    *,
    group_id: str,
    memory_object_id: str,
    soul_id: str,
    role_in_event: str | None = None,
    portrait_version_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    member_id = f"gmm_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO group_memory_members (
            id, group_id, memory_object_id, soul_id, role_in_event, portrait_version_id
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            member_id,
            group_id,
            memory_object_id,
            soul_id,
            role_in_event,
            portrait_version_id,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM group_memory_members WHERE id = ?", (member_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_group_member_row(row)


def remove_group_memory_member_record(group_id: str, memory_object_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM group_memory_members WHERE group_id = ? AND memory_object_id = ?",
        (group_id, memory_object_id),
    )
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0


def get_group_memory_members_records(group_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM group_memory_members WHERE group_id = ? ORDER BY created_at ASC",
        (group_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_group_member_row(r) for r in rows]


def add_group_memory_tag_record(
    *,
    group_id: str,
    tag_type: str,
    value: str,
    anchor_kind: str | None = None,
    anchor_id: str | None = None,
    is_descriptor: bool = False,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    tag_id = f"tag_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO group_memory_tags (
            tag_id, group_id, tag_type, value, anchor_kind, anchor_id, is_descriptor
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            tag_id,
            group_id,
            tag_type,
            value,
            anchor_kind,
            anchor_id,
            1 if is_descriptor else 0,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM group_memory_tags WHERE tag_id = ?", (tag_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_group_tag_row(row)


def remove_group_memory_tag_record(group_id: str, tag_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM group_memory_tags WHERE group_id = ? AND tag_id = ?",
        (group_id, tag_id),
    )
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0


def get_group_memory_tags_records(group_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM group_memory_tags WHERE group_id = ? ORDER BY created_at ASC",
        (group_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_group_tag_row(r) for r in rows]


def add_group_memory_anchor_record(
    *,
    group_id: str,
    anchor_type: str,
    anchor_ref: str,
    entity_id: str | None = None,
    entity_type: str | None = None,
    label: str,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    anchor_row_id = f"gma_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO group_memory_anchors (
            id, group_id, anchor_type, anchor_ref, entity_id, entity_type, label
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            anchor_row_id,
            group_id,
            anchor_type,
            anchor_ref,
            entity_id,
            entity_type,
            label,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM group_memory_anchors WHERE id = ?", (anchor_row_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_group_anchor_row(row)


def get_group_memory_anchors_records(group_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM group_memory_anchors WHERE group_id = ? ORDER BY created_at ASC",
        (group_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_group_anchor_row(r) for r in rows]


def get_memory_objects_by_event_record(event_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM memory_objects WHERE event_id = ? ORDER BY created_at ASC",
        (event_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        record = {
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
            "importance_tier": r["importance_tier"],
            "importance_score": r["importance_score"],
        }
        results.append(record)
    return results


# Phase 14: Living Biography DB Helpers


def _map_biography_version_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "biography_id": row["biography_id"],
        "soul_id": row["soul_id"],
        "version_number": row["version_number"],
        "status": row["status"],
        "title": row["title"],
        "current_chapter": row["current_chapter"],
        "scope_type": row["scope_type"],
        "scope_ref": row["scope_ref"],
        "visibility": row["visibility"],
        "source_snapshot": _json_or_none(row["source_snapshot_json"]) or {},
        "provider": row["provider"],
        "provider_model": row["provider_model"],
        "compiler_version": row["compiler_version"],
        "guardian_status": row["guardian_status"],
        "guardian_report": _json_or_none(row["guardian_report_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _map_biography_section_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "section_id": row["section_id"],
        "biography_id": row["biography_id"],
        "section_type": row["section_type"],
        "position": row["position"],
        "title": row["title"],
        "narrative": row["narrative"],
        "claim_kind": row["claim_kind"],
        "perspective_of": row["perspective_of"],
        "visual_reference": row["visual_reference"],
        "created_at": row["created_at"],
    }


def _map_biography_provenance_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "provenance_id": row["provenance_id"],
        "section_id": row["section_id"],
        "source_type": row["source_type"],
        "source_id": row["source_id"],
        "claim_kind": row["claim_kind"],
        "note": row["note"],
        "created_at": row["created_at"],
    }


def create_biography_version_transaction(
    *,
    soul_id: str,
    status: str,
    title: str,
    current_chapter: str | None,
    scope_type: str,
    scope_ref: str | None,
    visibility: str,
    source_snapshot: dict[str, Any],
    provider: str,
    provider_model: str | None,
    compiler_version: str,
    guardian_status: str,
    guardian_report: dict[str, Any],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Atomically create an immutable biography version with its sections and
    provenance links. Regeneration always inserts a new version.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) as count FROM biography_versions WHERE soul_id = ?",
            (soul_id,),
        )
        version_number = (cursor.fetchone()["count"] or 0) + 1
        biography_id = f"bio_{version_number}_{str(uuid.uuid4())[:8]}"

        cursor.execute(
            """
            INSERT INTO biography_versions (
                biography_id, soul_id, version_number, status, title, current_chapter,
                scope_type, scope_ref, visibility, source_snapshot_json, provider,
                provider_model, compiler_version, guardian_status, guardian_report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                biography_id,
                soul_id,
                version_number,
                status,
                title,
                current_chapter,
                scope_type,
                scope_ref,
                visibility,
                json.dumps(source_snapshot),
                provider,
                provider_model,
                compiler_version,
                guardian_status,
                json.dumps(guardian_report),
            ),
        )

        for position, section in enumerate(sections):
            section_id = f"sec_{position}_{str(uuid.uuid4())[:8]}"
            cursor.execute(
                """
                INSERT INTO biography_sections (
                    section_id, biography_id, section_type, position, title,
                    narrative, claim_kind, perspective_of, visual_reference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    section_id,
                    biography_id,
                    section["section_type"],
                    position,
                    section["title"],
                    section["narrative"],
                    section.get("claim_kind", "narrative_connective"),
                    section.get("perspective_of"),
                    section.get("visual_reference"),
                ),
            )
            for ref in section.get("provenance", []):
                cursor.execute(
                    """
                    INSERT INTO biography_provenance (
                        provenance_id, section_id, source_type, source_id, claim_kind, note
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        f"prov_{str(uuid.uuid4())[:8]}",
                        section_id,
                        ref["source_type"],
                        ref["source_id"],
                        ref.get("claim_kind", "canonical_fact"),
                        ref.get("note"),
                    ),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise

    biography = get_biography_record(biography_id)
    conn.close()
    return biography


def get_biography_record(biography_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM biography_versions WHERE biography_id = ?", (biography_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    biography = _map_biography_version_row(row)
    biography["sections"] = _load_biography_sections(conn, biography_id)
    conn.close()
    return biography


def _load_biography_sections(
    conn: sqlite3.Connection, biography_id: str
) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM biography_sections WHERE biography_id = ? ORDER BY position ASC",
        (biography_id,),
    )
    rows = cursor.fetchall()
    sections: list[dict[str, Any]] = []
    for row in rows:
        section = _map_biography_section_row(row)
        cursor.execute(
            "SELECT * FROM biography_provenance WHERE section_id = ? ORDER BY created_at ASC",
            (section["section_id"],),
        )
        section["provenance"] = [
            {
                "source_type": p["source_type"],
                "source_id": p["source_id"],
                "claim_kind": p["claim_kind"],
                "note": p["note"],
            }
            for p in cursor.fetchall()
        ]
        sections.append(section)
    return sections


def list_biography_records(soul_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM biography_versions WHERE soul_id = ? ORDER BY version_number DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_biography_version_row(r) for r in rows]


def get_current_biography_record(soul_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM biography_versions WHERE soul_id = ? AND status = 'current' "
        "ORDER BY version_number DESC LIMIT 1",
        (soul_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    biography = _map_biography_version_row(row)
    biography["sections"] = _load_biography_sections(conn, row["biography_id"])
    conn.close()
    return biography


def approve_biography_transaction(biography_id: str, soul_id: str) -> dict[str, Any]:
    """Approve a Guardian-passed draft, superseding any previous current version."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM biography_versions WHERE biography_id = ?", (biography_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Biography '{biography_id}' not found")
        if row["soul_id"] != soul_id:
            conn.close()
            raise ValueError(
                f"Biography '{biography_id}' does not belong to soul '{soul_id}'"
            )
        if row["status"] == "current":
            conn.close()
            return get_biography_record(biography_id)
        if row["status"] != "draft":
            conn.close()
            raise ValueError(
                f"Cannot approve biography '{biography_id}' in status '{row['status']}'."
            )
        if row["guardian_status"] != "passed":
            conn.close()
            raise ValueError(
                f"Biography '{biography_id}' has not passed the Biography Guardian."
            )

        cursor.execute(
            """
            UPDATE biography_versions SET status = 'superseded', updated_at = CURRENT_TIMESTAMP
            WHERE soul_id = ? AND status = 'current'
        """,
            (soul_id,),
        )
        cursor.execute(
            """
            UPDATE biography_versions SET status = 'current', updated_at = CURRENT_TIMESTAMP
            WHERE biography_id = ?
        """,
            (biography_id,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise

    biography = get_biography_record(biography_id)
    conn.close()
    return biography


def reject_biography_record(biography_id: str, soul_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM biography_versions WHERE biography_id = ?", (biography_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Biography '{biography_id}' not found")
    if row["soul_id"] != soul_id:
        conn.close()
        raise ValueError(
            f"Biography '{biography_id}' does not belong to soul '{soul_id}'"
        )
    if row["status"] == "current":
        conn.close()
        raise ValueError(
            f"Biography '{biography_id}' is current and cannot be rejected."
        )
    cursor.execute(
        """
        UPDATE biography_versions SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
        WHERE biography_id = ?
    """,
        (biography_id,),
    )
    conn.commit()
    conn.close()
    return get_biography_record(biography_id)


def get_biography_provenance_records(section_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM biography_provenance WHERE section_id = ? ORDER BY created_at ASC",
        (section_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_biography_provenance_row(r) for r in rows]


def get_story_mark_record(mark_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM story_marks WHERE id = ?", (mark_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "soul_id": row["soul_id"],
        "mark_type": row["mark_type"],
        "location": row["location"],
        "origin_event_id": row["origin_event_id"],
        "acquired_at": row["acquired_at"],
        "visibility": row["visibility"],
        "status": row["status"],
    }


def get_probable_path_record(path_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM probable_paths WHERE id = ?", (path_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "soul_id": row["soul_id"],
        "path_title": row["path_title"],
        "chosen_path": row["chosen_path"],
        "unchosen_approach": row["unchosen_approach"],
        "potential_outcome_class": row["potential_outcome_class"],
        "manifestation_type": row["manifestation_type"],
        "status": row["status"],
        "provenance_summary": row["provenance_summary"],
        "created_at": row["created_at"],
    }


# Phase 15: Art Direction Profiles & World Gallery DB Helpers


def _map_art_direction_profile_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "profile_id": row["profile_id"],
        "name": row["name"],
        "description": row["description"],
        "status": row["status"],
        "current_version_id": row["current_version_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _map_art_direction_version_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "version_id": row["version_id"],
        "profile_id": row["profile_id"],
        "version_number": row["version_number"],
        "medium_style": row["medium_style"],
        "palette_guidance": row["palette_guidance"],
        "lighting_guidance": row["lighting_guidance"],
        "atmosphere": row["atmosphere"],
        "texture_material": row["texture_material"],
        "camera_framing": row["camera_framing"],
        "composition_guidance": row["composition_guidance"],
        "portrait_treatment": row["portrait_treatment"],
        "environment_treatment": row["environment_treatment"],
        "relic_treatment": row["relic_treatment"],
        "phenomenon_treatment": row["phenomenon_treatment"],
        "chronicle_treatment": row["chronicle_treatment"],
        "negative_guidance": row["negative_guidance"],
        "provider_hints": _json_or_none(row["provider_hints_json"]) or {},
        "accessibility_notes": row["accessibility_notes"],
        "created_at": row["created_at"],
    }


def create_art_direction_profile_record(
    *,
    name: str,
    description: str = "",
    status: str = "draft",
    medium_style: str = "",
    palette_guidance: str = "",
    lighting_guidance: str = "",
    atmosphere: str = "",
    texture_material: str = "",
    camera_framing: str = "",
    composition_guidance: str = "",
    portrait_treatment: str = "",
    environment_treatment: str = "",
    relic_treatment: str = "",
    phenomenon_treatment: str = "",
    chronicle_treatment: str = "",
    negative_guidance: str = "",
    provider_hints: dict[str, Any] | None = None,
    accessibility_notes: str = "",
) -> dict[str, Any]:
    """Create a profile with its first immutable version in one transaction."""
    conn = get_db_connection()
    cursor = conn.cursor()
    profile_id = f"adp_{str(uuid.uuid4())[:8]}"
    version_id = f"adpv_1_{str(uuid.uuid4())[:8]}"
    try:
        cursor.execute(
            """
            INSERT INTO art_direction_profiles (
                profile_id, name, description, status, current_version_id
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (profile_id, name, description, status, version_id),
        )
        cursor.execute(
            """
            INSERT INTO art_direction_profile_versions (
                version_id, profile_id, version_number, medium_style, palette_guidance,
                lighting_guidance, atmosphere, texture_material, camera_framing,
                composition_guidance, portrait_treatment, environment_treatment,
                relic_treatment, phenomenon_treatment, chronicle_treatment,
                negative_guidance, provider_hints_json, accessibility_notes
            ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                version_id,
                profile_id,
                medium_style,
                palette_guidance,
                lighting_guidance,
                atmosphere,
                texture_material,
                camera_framing,
                composition_guidance,
                portrait_treatment,
                environment_treatment,
                relic_treatment,
                phenomenon_treatment,
                chronicle_treatment,
                negative_guidance,
                json.dumps(provider_hints or {}),
                accessibility_notes,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    profile = get_art_direction_profile_record(profile_id)
    version = get_art_direction_profile_version_record(version_id)
    conn.close()
    return {"profile": profile, "version": version}


def create_art_direction_profile_version_record(
    *,
    profile_id: str,
    medium_style: str = "",
    palette_guidance: str = "",
    lighting_guidance: str = "",
    atmosphere: str = "",
    texture_material: str = "",
    camera_framing: str = "",
    composition_guidance: str = "",
    portrait_treatment: str = "",
    environment_treatment: str = "",
    relic_treatment: str = "",
    phenomenon_treatment: str = "",
    chronicle_treatment: str = "",
    negative_guidance: str = "",
    provider_hints: dict[str, Any] | None = None,
    accessibility_notes: str = "",
) -> dict[str, Any]:
    """Append a new immutable version and point the profile at it."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM art_direction_profile_versions WHERE profile_id = ?",
        (profile_id,),
    )
    version_number = (cursor.fetchone()["count"] or 0) + 1
    version_id = f"adpv_{version_number}_{str(uuid.uuid4())[:8]}"
    try:
        cursor.execute(
            """
            INSERT INTO art_direction_profile_versions (
                version_id, profile_id, version_number, medium_style, palette_guidance,
                lighting_guidance, atmosphere, texture_material, camera_framing,
                composition_guidance, portrait_treatment, environment_treatment,
                relic_treatment, phenomenon_treatment, chronicle_treatment,
                negative_guidance, provider_hints_json, accessibility_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                version_id,
                profile_id,
                version_number,
                medium_style,
                palette_guidance,
                lighting_guidance,
                atmosphere,
                texture_material,
                camera_framing,
                composition_guidance,
                portrait_treatment,
                environment_treatment,
                relic_treatment,
                phenomenon_treatment,
                chronicle_treatment,
                negative_guidance,
                json.dumps(provider_hints or {}),
                accessibility_notes,
            ),
        )
        cursor.execute(
            """
            UPDATE art_direction_profiles
            SET current_version_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE profile_id = ?
        """,
            (version_id, profile_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    version = get_art_direction_profile_version_record(version_id)
    conn.close()
    return version


def get_art_direction_profile_record(profile_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM art_direction_profiles WHERE profile_id = ?", (profile_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_direction_profile_row(row) if row else None


def get_art_direction_profile_version_record(version_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM art_direction_profile_versions WHERE version_id = ?",
        (version_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_direction_version_row(row) if row else None


def list_art_direction_profiles_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM art_direction_profiles ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_art_direction_profile_row(r) for r in rows]


def list_art_direction_profile_versions_records(
    profile_id: str,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM art_direction_profile_versions WHERE profile_id = ? "
        "ORDER BY version_number ASC",
        (profile_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_art_direction_version_row(r) for r in rows]


def get_current_art_direction_profile_record() -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM art_direction_profiles WHERE status = 'current' "
        "ORDER BY updated_at DESC LIMIT 1"
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_direction_profile_row(row) if row else None


def set_art_direction_profile_status_record(
    profile_id: str, status: str
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Only one profile may be "current" at a time.
    if status == "current":
        cursor.execute(
            "UPDATE art_direction_profiles SET status = 'superseded', "
            "updated_at = CURRENT_TIMESTAMP WHERE status = 'current'"
        )
    cursor.execute(
        "UPDATE art_direction_profiles SET status = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE profile_id = ?",
        (status, profile_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM art_direction_profiles WHERE profile_id = ?", (profile_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_direction_profile_row(row)


def _map_gallery_collection_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "collection_id": row["collection_id"],
        "title": row["title"],
        "description": row["description"],
        "visibility": row["visibility"],
        "curator_soul_id": row["curator_soul_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _map_gallery_collection_item_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "item_id": row["item_id"],
        "collection_id": row["collection_id"],
        "artifact_type": row["artifact_type"],
        "artifact_ref": row["artifact_ref"],
        "position": row["position"],
        "caption": row["caption"],
        "created_at": row["created_at"],
    }


def create_gallery_collection_record(
    *,
    title: str,
    description: str = "",
    visibility: str = "public_canon",
    curator_soul_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    collection_id = f"col_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO gallery_collections (
            collection_id, title, description, visibility, curator_soul_id
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (collection_id, title, description, visibility, curator_soul_id),
    )
    conn.commit()
    conn.close()
    return get_gallery_collection_record(collection_id)


def get_gallery_collection_record(collection_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM gallery_collections WHERE collection_id = ?", (collection_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    collection = _map_gallery_collection_row(row)
    cursor.execute(
        "SELECT * FROM gallery_collection_items WHERE collection_id = ? "
        "ORDER BY position ASC, created_at ASC",
        (collection_id,),
    )
    collection["items"] = [
        _map_gallery_collection_item_row(r) for r in cursor.fetchall()
    ]
    conn.close()
    return collection


def list_gallery_collections_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gallery_collections ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [get_gallery_collection_record(r["collection_id"]) for r in rows]


def update_gallery_collection_record(
    collection_id: str,
    *,
    title: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM gallery_collections WHERE collection_id = ?", (collection_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Collection '{collection_id}' not found")
    new_title = title if title is not None else row["title"]
    new_desc = description if description is not None else row["description"]
    new_vis = visibility if visibility is not None else row["visibility"]
    cursor.execute(
        """
        UPDATE gallery_collections
        SET title = ?, description = ?, visibility = ?, updated_at = CURRENT_TIMESTAMP
        WHERE collection_id = ?
    """,
        (new_title, new_desc, new_vis, collection_id),
    )
    conn.commit()
    conn.close()
    return get_gallery_collection_record(collection_id)


def add_gallery_collection_item_record(
    *,
    collection_id: str,
    artifact_type: str,
    artifact_ref: str,
    caption: str = "",
    position: int | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if position is None:
        cursor.execute(
            "SELECT COALESCE(MAX(position), -1) as max_pos FROM gallery_collection_items "
            "WHERE collection_id = ?",
            (collection_id,),
        )
        position = (cursor.fetchone()["max_pos"] or -1) + 1
    item_id = f"coli_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO gallery_collection_items (
            item_id, collection_id, artifact_type, artifact_ref, position, caption
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (item_id, collection_id, artifact_type, artifact_ref, position, caption),
    )
    conn.commit()
    conn.close()
    return _get_gallery_collection_item_record(item_id)


def _get_gallery_collection_item_record(item_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM gallery_collection_items WHERE item_id = ?", (item_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_gallery_collection_item_row(row)


def remove_gallery_collection_item_record(collection_id: str, item_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM gallery_collection_items WHERE collection_id = ? AND item_id = ?",
        (collection_id, item_id),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def reorder_gallery_collection_items_record(
    collection_id: str, ordered_item_ids: list[str]
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    for position, item_id in enumerate(ordered_item_ids):
        cursor.execute(
            """
            UPDATE gallery_collection_items SET position = ?
            WHERE collection_id = ? AND item_id = ?
        """,
            (position, collection_id, item_id),
        )
    conn.commit()
    conn.close()
    return get_gallery_collection_record(collection_id)


def list_all_portrait_versions_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM portrait_versions ORDER BY soul_id ASC, version_number ASC"
    )
    rows = cursor.fetchall()
    conn.close()
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


def list_all_visual_entity_versions_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_entity_versions "
        "ORDER BY entity_type ASC, entity_id ASC, version_number ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_visual_version_row(r) for r in rows]


# Phase 16: Legendary Figures & World Memory DB Helpers


def _map_world_memory_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "memory_id": row["memory_id"],
        "subject_entity_type": row["subject_entity_type"],
        "subject_entity_id": row["subject_entity_id"],
        "culture": row["culture"],
        "era_context": row["era_context"],
        "memory_form": row["memory_form"],
        "interpretation_type": row["interpretation_type"],
        "title": row["title"],
        "narrative": row["narrative"],
        "memory_state": row["memory_state"],
        "remembrance_scale": row["remembrance_scale"],
        "visibility": row["visibility"],
        "perspective": row["perspective"],
        "status": row["status"],
        "guardian_status": row["guardian_status"],
        "guardian_report": _json_or_none(row["guardian_report_json"]),
        "version_number": row["version_number"],
        "compiler_version": row["compiler_version"],
        "provider": row["provider"],
        "provider_model": row["provider_model"],
        "significance_rationale": row["significance_rationale"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _map_world_memory_deviation_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "deviation_id": row["deviation_id"],
        "memory_id": row["memory_id"],
        "deviation_kind": row["deviation_kind"],
        "canon_supports": row["canon_supports"],
        "legend_claims": row["legend_claims"],
        "entry_note": row["entry_note"],
        "created_at": row["created_at"],
    }


def _map_legendary_figure_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "figure_id": row["figure_id"],
        "subject_soul_id": row["subject_soul_id"],
        "subject_entity_type": row["subject_entity_type"],
        "subject_entity_id": row["subject_entity_id"],
        "figure_title": row["figure_title"],
        "later_cultural_titles": _json_or_none(row["later_cultural_titles_json"]) or [],
        "remembrance_scale": row["remembrance_scale"],
        "memory_state": row["memory_state"],
        "eligibility_rationale": row["eligibility_rationale"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _map_legendary_figure_link_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "link_id": row["link_id"],
        "figure_id": row["figure_id"],
        "link_type": row["link_type"],
        "link_ref": row["link_ref"],
        "link_label": row["link_label"],
        "is_canonical": bool(row["is_canonical"]),
        "created_at": row["created_at"],
    }


def create_world_memory_transaction(
    *,
    subject_entity_type: str,
    subject_entity_id: str,
    culture: str,
    era_context: str,
    memory_form: str,
    interpretation_type: str,
    title: str,
    narrative: str,
    memory_state: str,
    remembrance_scale: str,
    visibility: str,
    perspective: str,
    status: str,
    guardian_status: str,
    guardian_report: dict[str, Any],
    compiler_version: str,
    provider: str,
    provider_model: str | None,
    significance_rationale: str,
    source_refs: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Atomically create an immutable World Memory with its provenance links and
    declared deviations. World Memory is derived, never authoritative.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) as count FROM world_memories WHERE subject_entity_type = ? "
            "AND subject_entity_id = ? AND culture = ? AND memory_form = ?",
            (subject_entity_type, subject_entity_id, culture, memory_form),
        )
        version_number = (cursor.fetchone()["count"] or 0) + 1
        memory_id = f"wm_{str(uuid.uuid4())[:8]}"

        cursor.execute(
            """
            INSERT INTO world_memories (
                memory_id, subject_entity_type, subject_entity_id, culture, era_context,
                memory_form, interpretation_type, title, narrative, memory_state,
                remembrance_scale, visibility, perspective, status, guardian_status,
                guardian_report_json, version_number, compiler_version, provider,
                provider_model, significance_rationale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                memory_id,
                subject_entity_type,
                subject_entity_id,
                culture,
                era_context,
                memory_form,
                interpretation_type,
                title,
                narrative,
                memory_state,
                remembrance_scale,
                visibility,
                perspective,
                status,
                guardian_status,
                json.dumps(guardian_report),
                version_number,
                compiler_version,
                provider,
                provider_model,
                significance_rationale,
            ),
        )

        for ref in source_refs:
            cursor.execute(
                """
                INSERT INTO world_memory_source_links (
                    link_id, memory_id, source_type, source_id, claim_kind, note
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    f"wmsl_{str(uuid.uuid4())[:8]}",
                    memory_id,
                    ref["source_type"],
                    ref["source_id"],
                    ref.get("claim_kind", "canonical_fact"),
                    ref.get("note"),
                ),
            )

        for deviation in deviations:
            cursor.execute(
                """
                INSERT INTO world_memory_deviations (
                    deviation_id, memory_id, deviation_kind, canon_supports,
                    legend_claims, entry_note
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    f"wmd_{str(uuid.uuid4())[:8]}",
                    memory_id,
                    deviation["deviation_kind"],
                    deviation.get("canon_supports", ""),
                    deviation.get("legend_claims", ""),
                    deviation.get("entry_note", ""),
                ),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise

    memory = get_world_memory_record(memory_id)
    conn.close()
    return memory


def _load_world_memory_children(
    conn: sqlite3.Connection, memory_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_memory_source_links WHERE memory_id = ? ORDER BY created_at ASC",
        (memory_id,),
    )
    source_refs = [
        {
            "source_type": r["source_type"],
            "source_id": r["source_id"],
            "claim_kind": r["claim_kind"],
            "note": r["note"],
        }
        for r in cursor.fetchall()
    ]
    cursor.execute(
        "SELECT * FROM world_memory_deviations WHERE memory_id = ? ORDER BY created_at ASC",
        (memory_id,),
    )
    deviations = [_map_world_memory_deviation_row(r) for r in cursor.fetchall()]
    return source_refs, deviations


def get_world_memory_record(memory_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM world_memories WHERE memory_id = ?", (memory_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    memory = _map_world_memory_row(row)
    source_refs, deviations = _load_world_memory_children(conn, memory_id)
    conn.close()
    memory["source_refs"] = source_refs
    memory["deviations"] = deviations
    return memory


def list_world_memory_records(
    *,
    subject_entity_type: str | None = None,
    subject_entity_id: str | None = None,
    culture: str | None = None,
    era_context: str | None = None,
    memory_form: str | None = None,
    memory_state: str | None = None,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM world_memories WHERE 1=1"
    params: list[Any] = []
    if subject_entity_type:
        query += " AND subject_entity_type = ?"
        params.append(subject_entity_type)
    if subject_entity_id:
        query += " AND subject_entity_id = ?"
        params.append(subject_entity_id)
    if culture:
        query += " AND culture = ?"
        params.append(culture)
    if era_context:
        query += " AND era_context = ?"
        params.append(era_context)
    if memory_form:
        query += " AND memory_form = ?"
        params.append(memory_form)
    if memory_state:
        query += " AND memory_state = ?"
        params.append(memory_state)
    query += " ORDER BY version_number DESC, created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        memory = _map_world_memory_row(row)
        source_refs, deviations = _load_world_memory_children(conn, row["memory_id"])
        memory["source_refs"] = source_refs
        memory["deviations"] = deviations
        results.append(memory)
    conn.close()
    return results


def list_world_memory_versions_records(
    subject_entity_type: str, subject_entity_id: str, culture: str, memory_form: str
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_memories WHERE subject_entity_type = ? AND "
        "subject_entity_id = ? AND culture = ? AND memory_form = ? "
        "ORDER BY version_number DESC",
        (subject_entity_type, subject_entity_id, culture, memory_form),
    )
    rows = cursor.fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        memory = _map_world_memory_row(row)
        source_refs, deviations = _load_world_memory_children(conn, row["memory_id"])
        memory["source_refs"] = source_refs
        memory["deviations"] = deviations
        results.append(memory)
    conn.close()
    return results


def approve_world_memory_record(memory_id: str) -> dict[str, Any]:
    """Approve a Guardian-passed draft, superseding any prior current version."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM world_memories WHERE memory_id = ?", (memory_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"World memory '{memory_id}' not found")
    if row["status"] == "current":
        conn.close()
        return get_world_memory_record(memory_id)
    if row["status"] != "draft":
        conn.close()
        raise ValueError(
            f"Cannot approve world memory '{memory_id}' in status '{row['status']}'."
        )
    if row["guardian_status"] != "passed":
        conn.close()
        raise ValueError(
            f"World memory '{memory_id}' has not passed the World Memory Guardian."
        )
    cursor.execute(
        """
        UPDATE world_memories SET status = 'superseded', updated_at = CURRENT_TIMESTAMP
        WHERE subject_entity_type = ? AND subject_entity_id = ? AND culture = ?
        AND memory_form = ? AND status = 'current'
    """,
        (
            row["subject_entity_type"],
            row["subject_entity_id"],
            row["culture"],
            row["memory_form"],
        ),
    )
    cursor.execute(
        "UPDATE world_memories SET status = 'current', updated_at = CURRENT_TIMESTAMP "
        "WHERE memory_id = ?",
        (memory_id,),
    )
    conn.commit()
    conn.close()
    return get_world_memory_record(memory_id)


def reject_world_memory_record(memory_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM world_memories WHERE memory_id = ?", (memory_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"World memory '{memory_id}' not found")
    if row["status"] == "current":
        conn.close()
        raise ValueError(
            f"World memory '{memory_id}' is current and cannot be rejected."
        )
    cursor.execute(
        "UPDATE world_memories SET status = 'rejected', updated_at = CURRENT_TIMESTAMP "
        "WHERE memory_id = ?",
        (memory_id,),
    )
    conn.commit()
    conn.close()
    return get_world_memory_record(memory_id)


def mark_world_memory_state_record(
    memory_id: str, new_state: str, reason: str
) -> dict[str, Any]:
    """Record a memory-state transition without deleting canonical history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM world_memories WHERE memory_id = ?", (memory_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"World memory '{memory_id}' not found")
    previous_state = row["memory_state"]
    state_id = f"wms_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO world_memory_state_history (
            state_id, memory_id, previous_state, new_state, reason
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (state_id, memory_id, previous_state, new_state, reason),
    )
    cursor.execute(
        "UPDATE world_memories SET memory_state = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE memory_id = ?",
        (new_state, memory_id),
    )
    conn.commit()
    conn.close()
    return get_world_memory_record(memory_id)


def get_world_memory_state_history_records(memory_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_memory_state_history WHERE memory_id = ? "
        "ORDER BY created_at ASC",
        (memory_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "state_id": r["state_id"],
            "memory_id": r["memory_id"],
            "previous_state": r["previous_state"],
            "new_state": r["new_state"],
            "reason": r["reason"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def create_legendary_figure_record(
    *,
    subject_soul_id: str | None,
    subject_entity_type: str,
    subject_entity_id: str,
    figure_title: str,
    later_cultural_titles: list[str],
    remembrance_scale: str,
    memory_state: str,
    eligibility_rationale: str,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    figure_id = f"lgf_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO legendary_figures (
            figure_id, subject_soul_id, subject_entity_type, subject_entity_id,
            figure_title, later_cultural_titles_json, remembrance_scale,
            memory_state, eligibility_rationale, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """,
        (
            figure_id,
            subject_soul_id,
            subject_entity_type,
            subject_entity_id,
            figure_title,
            json.dumps(later_cultural_titles),
            remembrance_scale,
            memory_state,
            eligibility_rationale,
        ),
    )
    conn.commit()
    conn.close()
    return get_legendary_figure_record(figure_id)


def add_legendary_figure_link_record(
    *,
    figure_id: str,
    link_type: str,
    link_ref: str,
    link_label: str = "",
    is_canonical: bool = True,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    link_id = f"lgfl_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO legendary_figure_links (
            link_id, figure_id, link_type, link_ref, link_label, is_canonical
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (link_id, figure_id, link_type, link_ref, link_label, 1 if is_canonical else 0),
    )
    conn.commit()
    conn.close()
    return _get_legendary_figure_link_record(link_id)


def _get_legendary_figure_link_record(link_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM legendary_figure_links WHERE link_id = ?", (link_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_legendary_figure_link_row(row)


def get_legendary_figure_record(figure_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM legendary_figures WHERE figure_id = ?", (figure_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    figure = _map_legendary_figure_row(row)
    cursor.execute(
        "SELECT * FROM legendary_figure_links WHERE figure_id = ? ORDER BY created_at ASC",
        (figure_id,),
    )
    figure["links"] = [_map_legendary_figure_link_row(r) for r in cursor.fetchall()]
    conn.close()
    return figure


def list_legendary_figures_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM legendary_figures ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [get_legendary_figure_record(r["figure_id"]) for r in rows]


def create_world_memory_placement_record(
    *,
    memory_id: str,
    placement_type: str,
    placement_ref: str,
    visibility: str = "public_canon",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    placement_id = f"wmp_{str(uuid.uuid4())[:8]}"
    cursor.execute(
        """
        INSERT INTO world_memory_placements (
            placement_id, memory_id, placement_type, placement_ref, visibility
        ) VALUES (?, ?, ?, ?, ?)
    """,
        (placement_id, memory_id, placement_type, placement_ref, visibility),
    )
    conn.commit()
    conn.close()
    return _get_world_memory_placement_record(placement_id)


def _get_world_memory_placement_record(placement_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_memory_placements WHERE placement_id = ?", (placement_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return {
        "placement_id": row["placement_id"],
        "memory_id": row["memory_id"],
        "placement_type": row["placement_type"],
        "placement_ref": row["placement_ref"],
        "visibility": row["visibility"],
        "created_at": row["created_at"],
    }


def list_world_memory_placements_records(memory_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM world_memory_placements WHERE memory_id = ? ORDER BY created_at ASC",
        (memory_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "placement_id": r["placement_id"],
            "memory_id": r["memory_id"],
            "placement_type": r["placement_type"],
            "placement_ref": r["placement_ref"],
            "visibility": r["visibility"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


# Phase 17: Campaign Orchestrator persistence helpers.


def _map_campaign_session_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "session_id": r["session_id"],
        "campaign_id": r["campaign_id"],
        "soul_id": r["soul_id"],
        "active_soul_id": r["active_soul_id"]
        if "active_soul_id" in r.keys()
        else r["soul_id"],
        "constellation_id": r["constellation_id"],
        "status": r["status"],
        "current_opportunity_id": r["current_opportunity_id"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
        "last_active_at": r["last_active_at"]
        if "last_active_at" in r.keys()
        else r["updated_at"],
    }


def _map_campaign_opportunity_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "opportunity_id": r["opportunity_id"],
        "session_id": r["session_id"],
        "opportunity_type": r["opportunity_type"],
        "eligibility_rule": r["eligibility_rule"],
        "source_evidence": _json_or_none(r["source_evidence_json"]) or [],
        "involved_entities": _json_or_none(r["involved_entities_json"]) or [],
        "visibility_scope": r["visibility_scope"],
        "urgency_class": r["urgency_class"],
        "participation": r["participation"],
        "lifecycle_state": r["lifecycle_state"],
        "cooldown_key": r["cooldown_key"],
        "cooldown_until": r["cooldown_until"],
        "domain_action": r["domain_action"],
        "domain_action_payload": _json_or_none(r["domain_action_payload_json"]) or {},
        "reasoning": _json_or_none(r["reasoning_json"]) or {},
        "narration": r["narration"],
        "narration_source": r["narration_source"],
        "created_at": r["created_at"],
        "resolved_at": r["resolved_at"],
    }


def _map_campaign_reaction_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "reaction_id": r["reaction_id"],
        "transition_id": r["transition_id"],
        "system_name": r["system_name"],
        "result_kind": r["result_kind"],
        "details": _json_or_none(r["details_json"]) or {},
        "created_at": r["created_at"],
    }


def _map_campaign_transition_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "transition_id": r["transition_id"],
        "session_id": r["session_id"],
        "opportunity_id": r["opportunity_id"],
        "canonical_event_id": r["canonical_event_id"],
        "transition_type": r["transition_type"],
        "systems_invoked": _json_or_none(r["systems_invoked_json"]) or [],
        "outcomes": _json_or_none(r["outcomes_json"]) or [],
        "canonical_change": bool(r["canonical_change"]),
        "provider_failure": r["provider_failure"],
        "rejected_invalid_transition": bool(r["rejected_invalid_transition"]),
        "created_at": r["created_at"],
    }


def create_campaign_session_record(
    *,
    campaign_id: str,
    soul_id: str,
    constellation_id: str | None = None,
    active_soul_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    active_soul_id = active_soul_id or soul_id
    cursor.execute(
        """
        INSERT INTO campaign_sessions (session_id, campaign_id, soul_id, constellation_id, active_soul_id)
        VALUES (?, ?, ?, ?, ?)
    """,
        (session_id, campaign_id, soul_id, constellation_id, active_soul_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_sessions WHERE session_id = ?", (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_session_row(row)


def get_campaign_session_record(session_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_sessions WHERE session_id = ?", (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_session_row(row) if row else None


def get_active_campaign_session_record(
    campaign_id: str, soul_id: str
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM campaign_sessions
        WHERE campaign_id = ? AND soul_id = ? AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    """,
        (campaign_id, soul_id),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_session_row(row) if row else None


def set_campaign_session_current_opportunity(
    session_id: str, opportunity_id: str | None
) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE campaign_sessions SET current_opportunity_id = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
        (opportunity_id, session_id),
    )
    conn.commit()
    conn.close()


def create_campaign_opportunity_record(
    *,
    session_id: str,
    opportunity_type: str,
    eligibility_rule: str,
    source_evidence: list[dict[str, Any]],
    involved_entities: list[dict[str, Any]],
    visibility_scope: str,
    urgency_class: str,
    participation: str,
    cooldown_key: str | None,
    domain_action: str,
    domain_action_payload: dict[str, Any],
    reasoning: dict[str, Any],
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    opportunity_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO campaign_opportunities (
            opportunity_id, session_id, opportunity_type, eligibility_rule,
            source_evidence_json, involved_entities_json, visibility_scope,
            urgency_class, participation, lifecycle_state, cooldown_key,
            domain_action, domain_action_payload_json, reasoning_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'eligible', ?, ?, ?, ?)
    """,
        (
            opportunity_id,
            session_id,
            opportunity_type,
            eligibility_rule,
            json.dumps(source_evidence),
            json.dumps(involved_entities),
            visibility_scope,
            urgency_class,
            participation,
            cooldown_key,
            domain_action,
            json.dumps(domain_action_payload),
            json.dumps(reasoning),
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_opportunities WHERE opportunity_id = ?",
        (opportunity_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_opportunity_row(row)


def get_campaign_opportunity_record(opportunity_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_opportunities WHERE opportunity_id = ?",
        (opportunity_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_opportunity_row(row) if row else None


def list_campaign_opportunities_records(
    session_id: str, lifecycle_state: str | None = None
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if lifecycle_state:
        cursor.execute(
            "SELECT * FROM campaign_opportunities WHERE session_id = ? AND lifecycle_state = ? ORDER BY created_at ASC",
            (session_id, lifecycle_state),
        )
    else:
        cursor.execute(
            "SELECT * FROM campaign_opportunities WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [_map_campaign_opportunity_row(r) for r in rows]


def update_campaign_opportunity_state_record(
    opportunity_id: str,
    lifecycle_state: str,
    narration: str | None = None,
    narration_source: str = "deterministic",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if narration is not None:
        cursor.execute(
            """
            UPDATE campaign_opportunities
            SET lifecycle_state = ?, narration = ?, narration_source = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE opportunity_id = ?
        """,
            (lifecycle_state, narration, narration_source, opportunity_id),
        )
    else:
        cursor.execute(
            """
            UPDATE campaign_opportunities
            SET lifecycle_state = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE opportunity_id = ?
        """,
            (lifecycle_state, opportunity_id),
        )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_opportunities WHERE opportunity_id = ?",
        (opportunity_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_opportunity_row(row) if row else None


def create_campaign_transaction_record(
    *,
    transition_id: str,
    session_id: str,
    opportunity_id: str | None,
    canonical_event_id: str | None,
    transition_type: str,
    systems_invoked: list[str],
    outcomes: list[dict[str, Any]],
    canonical_change: bool,
    provider_failure: str | None,
    rejected_invalid_transition: bool,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO campaign_transitions (
            transition_id, session_id, opportunity_id, canonical_event_id,
            transition_type, systems_invoked_json, outcomes_json,
            canonical_change, provider_failure, rejected_invalid_transition
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            transition_id,
            session_id,
            opportunity_id,
            canonical_event_id,
            transition_type,
            json.dumps(systems_invoked),
            json.dumps(outcomes),
            1 if canonical_change else 0,
            provider_failure,
            1 if rejected_invalid_transition else 0,
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_transitions WHERE transition_id = ?", (transition_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_transition_row(row)


def create_campaign_reaction_record(
    *, transition_id: str, system_name: str, result_kind: str, details: dict[str, Any]
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    reaction_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO campaign_reactions (reaction_id, transition_id, system_name, result_kind, details_json)
        VALUES (?, ?, ?, ?, ?)
    """,
        (reaction_id, transition_id, system_name, result_kind, json.dumps(details)),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_reactions WHERE reaction_id = ?", (reaction_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_reaction_row(row)


def get_campaign_transition_record(transition_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_transitions WHERE transition_id = ?", (transition_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    transition = _map_campaign_transition_row(row)
    cursor.execute(
        "SELECT * FROM campaign_reactions WHERE transition_id = ? ORDER BY created_at ASC",
        (transition_id,),
    )
    reactions = [_map_campaign_reaction_row(r) for r in cursor.fetchall()]
    conn.close()
    transition["reactions"] = reactions
    return transition


def list_campaign_transitions_records(session_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_transitions WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = cursor.fetchall()
    transitions = [_map_campaign_transition_row(r) for r in rows]
    for transition in transitions:
        cursor.execute(
            "SELECT * FROM campaign_reactions WHERE transition_id = ? ORDER BY created_at ASC",
            (transition["transition_id"],),
        )
        transition["reactions"] = [
            _map_campaign_reaction_row(r) for r in cursor.fetchall()
        ]
    conn.close()
    return transitions


def get_campaign_transition_by_event_record(
    session_id: str, event_id: str
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM campaign_transitions
        WHERE session_id = ? AND canonical_event_id = ?
        ORDER BY created_at ASC LIMIT 1
    """,
        (session_id, event_id),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_transition_row(row) if row else None


def get_recent_campaign_cooldown_keys(session_id: str, limit: int) -> list[str]:
    """Cooldown keys of the most recently resolved/rejected/postponed/hidden
    opportunities in this session. Used by count-based pacing (not wall-clock)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT cooldown_key FROM campaign_opportunities
        WHERE session_id = ?
          AND lifecycle_state IN ('resolved', 'rejected', 'postponed', 'hidden')
          AND cooldown_key IS NOT NULL
        ORDER BY resolved_at DESC, created_at DESC
        LIMIT ?
    """,
        (session_id, limit),
    )
    keys = [r["cooldown_key"] for r in cursor.fetchall()]
    conn.close()
    return keys


def _map_narrative_generation_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "generation_id": r["generation_id"],
        "session_id": r["session_id"],
        "opportunity_id": r["opportunity_id"],
        "transition_id": r["transition_id"],
        "provider": r["provider"],
        "provider_model": r["provider_model"],
        "template_version": r["template_version"],
        "generation_timestamp": r["generation_timestamp"],
        "retry_count": r["retry_count"],
        "validation_outcome": r["validation_outcome"],
        "latency_ms": r["latency_ms"],
        "used_fallback": bool(r["used_fallback"]),
        "context_stats": _json_or_none(r["context_stats_json"]) or {},
        "output": _json_or_none(r["output_json"]) or {},
        "error": r["error"],
    }


def create_narrative_generation_record(
    *,
    generation_id: str,
    session_id: str | None,
    opportunity_id: str | None,
    transition_id: str | None,
    provider: str,
    provider_model: str,
    template_version: str,
    retry_count: int,
    validation_outcome: str,
    latency_ms: int | None,
    used_fallback: bool,
    context_stats: dict[str, Any],
    output: dict[str, Any],
    error: str | None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO narrative_generations (
            generation_id, session_id, opportunity_id, transition_id,
            provider, provider_model, template_version, retry_count,
            validation_outcome, latency_ms, used_fallback,
            context_stats_json, output_json, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            generation_id,
            session_id,
            opportunity_id,
            transition_id,
            provider,
            provider_model,
            template_version,
            retry_count,
            validation_outcome,
            latency_ms,
            1 if used_fallback else 0,
            json.dumps(context_stats),
            json.dumps(output),
            error,
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM narrative_generations WHERE generation_id = ?", (generation_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_narrative_generation_row(row)


def list_narrative_generation_records(
    *,
    session_id: str | None = None,
    opportunity_id: str | None = None,
    transition_id: str | None = None,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    clauses = []
    params: list[Any] = []
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    if opportunity_id:
        clauses.append("opportunity_id = ?")
        params.append(opportunity_id)
    if transition_id:
        clauses.append("transition_id = ?")
        params.append(transition_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cursor.execute(
        f"SELECT * FROM narrative_generations {where} ORDER BY generation_timestamp DESC",
        params,
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_narrative_generation_row(r) for r in rows]


def get_canonical_event_record(event_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scene_events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
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


# Phase 19: Relationship & Promise Engine persistence helpers.


def _map_relationship_participant_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
        "role": r["role"],
    }


def _map_relationship_source_ref_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "source_type": r["source_type"],
        "source_id": r["source_id"],
        "claim_kind": r["claim_kind"],
    }


def _map_relationship_event_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "event_id": r["event_id"],
        "relationship_id": r["relationship_id"],
        "event_type": r["event_type"],
        "source_type": r["source_type"],
        "source_id": r["source_id"],
        "summary": r["summary"],
        "created_at": r["created_at"],
    }


def _map_relationship_perspective_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "perspective_id": r["perspective_id"],
        "relationship_id": r["relationship_id"],
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
        "kind": r["kind"],
        "view": r["view"],
        "is_canonical_interaction": bool(r["is_canonical_interaction"]),
        "visibility": r["visibility"],
        "created_at": r["created_at"],
    }


def _map_relationship_entity_link_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "link_id": r["link_id"],
        "relationship_id": r["relationship_id"],
        "link_type": r["link_type"],
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
        "created_at": r["created_at"],
    }


def _load_relationship_children(
    cursor: sqlite3.Cursor, relationship_id: str
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    cursor.execute(
        "SELECT * FROM relationship_participants WHERE relationship_id = ? ORDER BY created_at ASC",
        (relationship_id,),
    )
    participants = [_map_relationship_participant_row(r) for r in cursor.fetchall()]
    cursor.execute(
        "SELECT * FROM relationship_source_events WHERE relationship_id = ? ORDER BY created_at ASC",
        (relationship_id,),
    )
    source_refs = [_map_relationship_source_ref_row(r) for r in cursor.fetchall()]
    cursor.execute(
        "SELECT * FROM relationship_events WHERE relationship_id = ? ORDER BY created_at ASC",
        (relationship_id,),
    )
    events = [_map_relationship_event_row(r) for r in cursor.fetchall()]
    cursor.execute(
        "SELECT * FROM relationship_perspectives WHERE relationship_id = ? ORDER BY created_at ASC",
        (relationship_id,),
    )
    perspectives = [_map_relationship_perspective_row(r) for r in cursor.fetchall()]
    cursor.execute(
        "SELECT * FROM relationship_entity_links WHERE relationship_id = ? ORDER BY created_at ASC",
        (relationship_id,),
    )
    entity_links = [_map_relationship_entity_link_row(r) for r in cursor.fetchall()]
    return participants, source_refs, events, perspectives, entity_links


def _map_relationship_row(
    r: sqlite3.Row,
    children: tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ],
) -> dict[str, Any]:
    participants, source_refs, events, perspectives, entity_links = children
    return {
        "relationship_id": r["relationship_id"],
        "kinds": _json_or_none(r["kind_json"]) or [],
        "status": r["status"],
        "visibility": r["visibility"],
        "creation_context": r["creation_context"],
        "participants": participants,
        "source_refs": source_refs,
        "events": events,
        "perspectives": perspectives,
        "entity_links": entity_links,
        "last_interaction_at": r["last_interaction_at"]
        if "last_interaction_at" in r.keys()
        else (events[-1]["created_at"] if events else None),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def create_relationship_record(
    *,
    kinds: list[str],
    participants: list[dict[str, Any]],
    status: str,
    visibility: str,
    creation_context: str,
    source_type: str | None,
    source_id: str | None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    relationship_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO relationships (relationship_id, kind_json, status, visibility, creation_context)
        VALUES (?, ?, ?, ?, ?)
    """,
        (relationship_id, json.dumps(kinds), status, visibility, creation_context),
    )
    for participant in participants:
        cursor.execute(
            """
            INSERT INTO relationship_participants (participant_id, relationship_id, entity_type, entity_id, role)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                relationship_id,
                participant.get("entity_type"),
                participant.get("entity_id"),
                participant.get("role", "participant"),
            ),
        )
    if source_type and source_id:
        cursor.execute(
            """
            INSERT INTO relationship_source_events (link_id, relationship_id, source_type, source_id, claim_kind)
            VALUES (?, ?, ?, ?, 'canonical_fact')
        """,
            (str(uuid.uuid4()), relationship_id, source_type, source_id),
        )
    conn.commit()
    record = get_relationship_record(relationship_id)
    conn.close()
    return record


def get_relationship_record(relationship_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM relationships WHERE relationship_id = ?", (relationship_id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    children = _load_relationship_children(cursor, relationship_id)
    record = _map_relationship_row(row, children)
    conn.close()
    return record


def list_relationship_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM relationships ORDER BY created_at ASC")
    rows = cursor.fetchall()
    records = [
        _map_relationship_row(
            r, _load_relationship_children(cursor, r["relationship_id"])
        )
        for r in rows
    ]
    conn.close()
    return records


def add_relationship_event_record(
    *,
    relationship_id: str,
    event_type: str,
    source_type: str,
    source_id: str,
    summary: str,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO relationship_events (event_id, relationship_id, event_type, source_type, source_id, summary)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            str(uuid.uuid4()),
            relationship_id,
            event_type,
            source_type,
            source_id,
            summary,
        ),
    )
    cursor.execute(
        """
        UPDATE relationships
        SET updated_at = CURRENT_TIMESTAMP, last_interaction_at = CURRENT_TIMESTAMP
        WHERE relationship_id = ?
    """,
        (relationship_id,),
    )
    conn.commit()
    record = get_relationship_record(relationship_id)
    conn.close()
    return record


def add_relationship_perspective_record(
    *,
    relationship_id: str,
    entity_type: str,
    entity_id: str,
    kind: str,
    view: str,
    is_canonical_interaction: bool,
    visibility: str,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO relationship_perspectives (
            perspective_id, relationship_id, entity_type, entity_id, kind, view,
            is_canonical_interaction, visibility
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            str(uuid.uuid4()),
            relationship_id,
            entity_type,
            entity_id,
            kind,
            view,
            1 if is_canonical_interaction else 0,
            visibility,
        ),
    )
    conn.commit()
    record = get_relationship_record(relationship_id)
    conn.close()
    return record


def add_relationship_entity_link_record(
    *, relationship_id: str, link_type: str, entity_type: str, entity_id: str
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO relationship_entity_links (link_id, relationship_id, link_type, entity_type, entity_id)
        VALUES (?, ?, ?, ?, ?)
    """,
        (str(uuid.uuid4()), relationship_id, link_type, entity_type, entity_id),
    )
    conn.commit()
    record = get_relationship_record(relationship_id)
    conn.close()
    return record


def _map_promise_participant_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "participant_type": r["participant_type"],
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
    }


def _map_promise_state_history_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "state_id": r["state_id"],
        "promise_id": r["promise_id"],
        "previous_state": r["previous_state"],
        "new_state": r["new_state"],
        "evidence_type": r["evidence_type"],
        "evidence_id": r["evidence_id"],
        "reason": r["reason"],
        "created_at": r["created_at"],
    }


def _map_promise_entity_link_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "link_id": r["link_id"],
        "promise_id": r["promise_id"],
        "link_type": r["link_type"],
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
        "created_at": r["created_at"],
    }


def _load_promise_children(
    cursor: sqlite3.Cursor, promise_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    cursor.execute(
        "SELECT * FROM promise_participants WHERE promise_id = ? ORDER BY created_at ASC",
        (promise_id,),
    )
    participants = [_map_promise_participant_row(r) for r in cursor.fetchall()]
    cursor.execute(
        "SELECT * FROM promise_state_history WHERE promise_id = ? ORDER BY created_at ASC",
        (promise_id,),
    )
    state_history = [_map_promise_state_history_row(r) for r in cursor.fetchall()]
    cursor.execute(
        "SELECT * FROM promise_entity_links WHERE promise_id = ? ORDER BY created_at ASC",
        (promise_id,),
    )
    entity_links = [_map_promise_entity_link_row(r) for r in cursor.fetchall()]
    return participants, state_history, entity_links


def _map_promise_row(
    r: sqlite3.Row,
    children: tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]],
) -> dict[str, Any]:
    participants, state_history, entity_links = children
    return {
        "promise_id": r["promise_id"],
        "promisor_entity_type": r["promisor_entity_type"],
        "promisor_entity_id": r["promisor_entity_id"],
        "promise_text": r["promise_text"],
        "structured_meaning": _json_or_none(r["structured_meaning_json"]) or {},
        "conditions": _json_or_none(r["conditions_json"]) or [],
        "scope": r["scope"],
        "visibility": r["visibility"],
        "source_type": r["source_type"],
        "source_id": r["source_id"],
        "source_authorization": r["source_authorization"],
        "lifecycle_state": r["lifecycle_state"],
        "inheritable": bool(r["inheritable"]),
        "transferable": bool(r["transferable"]),
        "participants": participants,
        "state_history": state_history,
        "entity_links": entity_links,
        "deadline_iso": r["deadline_iso"] if "deadline_iso" in r.keys() else None,
        "deadline_source_type": r["deadline_source_type"]
        if "deadline_source_type" in r.keys()
        else None,
        "deadline_source_id": r["deadline_source_id"]
        if "deadline_source_id" in r.keys()
        else None,
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def create_promise_record(
    *,
    promisor_entity_type: str,
    promisor_entity_id: str,
    promise_text: str,
    structured_meaning: dict[str, Any],
    conditions: list[str],
    scope: str,
    visibility: str,
    source_type: str,
    source_id: str,
    source_authorization: str,
    participants: list[dict[str, Any]],
    inheritable: bool,
    transferable: bool,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    promise_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO promises (
            promise_id, promisor_entity_type, promisor_entity_id, promise_text,
            structured_meaning_json, conditions_json, scope, visibility,
            source_type, source_id, source_authorization, lifecycle_state,
            inheritable, transferable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'made', ?, ?)
    """,
        (
            promise_id,
            promisor_entity_type,
            promisor_entity_id,
            promise_text,
            json.dumps(structured_meaning),
            json.dumps(conditions),
            scope,
            visibility,
            source_type,
            source_id,
            source_authorization,
            1 if inheritable else 0,
            1 if transferable else 0,
        ),
    )
    for participant in participants:
        cursor.execute(
            """
            INSERT INTO promise_participants (participant_id, promise_id, participant_type, entity_type, entity_id)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                promise_id,
                participant.get("participant_type", "recipient"),
                participant.get("entity_type"),
                participant.get("entity_id"),
            ),
        )
    conn.commit()
    record = get_promise_record(promise_id)
    conn.close()
    return record


def get_promise_record(promise_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promises WHERE promise_id = ?", (promise_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    children = _load_promise_children(cursor, promise_id)
    record = _map_promise_row(row, children)
    conn.close()
    return record


def list_promise_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promises ORDER BY created_at ASC")
    rows = cursor.fetchall()
    records = [
        _map_promise_row(r, _load_promise_children(cursor, r["promise_id"]))
        for r in rows
    ]
    conn.close()
    return records


def transition_promise_record(
    promise_id: str,
    new_state: str,
    *,
    evidence_type: str | None = None,
    evidence_id: str | None = None,
    reason: str = "",
    target_entity_type: str | None = None,
    target_entity_id: str | None = None,
) -> dict[str, Any]:
    """Validate and apply a promise state transition. Idempotent for the same
    state; the original wording/source is never mutated, and each transition is
    appended to immutable state history."""
    from app.relationship import validate_promise_transition

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promises WHERE promise_id = ?", (promise_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Promise not found")

    current = row["lifecycle_state"]
    validate_promise_transition(
        {
            "lifecycle_state": current,
            "conditions": _json_or_none(row["conditions_json"]) or [],
            "source_authorization": row["source_authorization"],
        },
        new_state,
        evidence_type=evidence_type,
        evidence_id=evidence_id,
        player_authorized=(evidence_type == "player_authorized"),
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
    )

    if new_state == current:
        conn.close()
        return get_promise_record(promise_id)

    cursor.execute(
        """
        INSERT INTO promise_state_history (state_id, promise_id, previous_state, new_state, evidence_type, evidence_id, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            str(uuid.uuid4()),
            promise_id,
            current,
            new_state,
            evidence_type,
            evidence_id,
            reason,
        ),
    )
    cursor.execute(
        "UPDATE promises SET lifecycle_state = ?, updated_at = CURRENT_TIMESTAMP WHERE promise_id = ?",
        (new_state, promise_id),
    )
    conn.commit()
    conn.close()
    return get_promise_record(promise_id)


def add_promise_entity_link_record(
    *, promise_id: str, link_type: str, entity_type: str, entity_id: str
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO promise_entity_links (link_id, promise_id, link_type, entity_type, entity_id)
        VALUES (?, ?, ?, ?, ?)
    """,
        (str(uuid.uuid4()), promise_id, link_type, entity_type, entity_id),
    )
    conn.commit()
    record = get_promise_record(promise_id)
    conn.close()
    return record


def relationships_for_entity(entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT relationship_id FROM relationship_participants
        WHERE entity_type = ? AND entity_id = ?
    """,
        (entity_type, entity_id),
    )
    ids = {r["relationship_id"] for r in cursor.fetchall()}
    records = []
    for relationship_id in ids:
        cursor.execute(
            "SELECT * FROM relationships WHERE relationship_id = ?", (relationship_id,)
        )
        row = cursor.fetchone()
        if row:
            records.append(
                _map_relationship_row(
                    row, _load_relationship_children(cursor, relationship_id)
                )
            )
    conn.close()
    return records


def promises_for_entity(entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT promise_id FROM promises WHERE promisor_entity_type = ? AND promisor_entity_id = ?
    """,
        (entity_type, entity_id),
    )
    ids = {r["promise_id"] for r in cursor.fetchall()}
    cursor.execute(
        """
        SELECT promise_id FROM promise_participants WHERE entity_type = ? AND entity_id = ?
    """,
        (entity_type, entity_id),
    )
    ids |= {r["promise_id"] for r in cursor.fetchall()}
    records = []
    for promise_id in ids:
        cursor.execute("SELECT * FROM promises WHERE promise_id = ?", (promise_id,))
        row = cursor.fetchone()
        if row:
            records.append(
                _map_promise_row(row, _load_promise_children(cursor, promise_id))
            )
    conn.close()
    return records


def promises_linked_to_entity(entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT promise_id FROM promise_entity_links WHERE entity_type = ? AND entity_id = ?
    """,
        (entity_type, entity_id),
    )
    ids = {r["promise_id"] for r in cursor.fetchall()}
    records = []
    for promise_id in ids:
        cursor.execute("SELECT * FROM promises WHERE promise_id = ?", (promise_id,))
        row = cursor.fetchone()
        if row:
            records.append(
                _map_promise_row(row, _load_promise_children(cursor, promise_id))
            )
    conn.close()
    return records


# ---------------------------------------------------------------------------
# Phase 20: multi-Aspect campaign sessions, places, and Wandering persistence.
# ---------------------------------------------------------------------------


def _map_campaign_aspect_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "campaign_id": r["campaign_id"],
        "soul_id": r["soul_id"],
        "aspect_id": r["aspect_id"],
        "display_name": r["display_name"],
        "viewpoint_location": r["viewpoint_location"],
        "is_active": bool(r["is_active"]),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def ensure_campaign_aspect(
    *,
    campaign_id: str,
    soul_id: str,
    display_name: str | None = None,
    aspect_id: str | None = None,
    viewpoint_location: str | None = None,
) -> dict[str, Any]:
    """Idempotently register a playable Aspect in a campaign."""
    conn = get_db_connection()
    cursor = conn.cursor()
    display_name = display_name or soul_id
    cursor.execute(
        """
        INSERT INTO campaign_aspects
            (campaign_id, soul_id, aspect_id, display_name, viewpoint_location, is_active)
        VALUES (?, ?, ?, ?, ?, 0)
        ON CONFLICT(campaign_id, soul_id) DO UPDATE SET
            display_name = excluded.display_name,
            aspect_id = COALESCE(excluded.aspect_id, campaign_aspects.aspect_id),
            viewpoint_location = COALESCE(excluded.viewpoint_location, campaign_aspects.viewpoint_location),
            updated_at = CURRENT_TIMESTAMP
    """,
        (campaign_id, soul_id, aspect_id, display_name, viewpoint_location),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_aspects WHERE campaign_id = ? AND soul_id = ?",
        (campaign_id, soul_id),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_aspect_row(row)


def get_campaign_aspect_record(campaign_id: str, soul_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_aspects WHERE campaign_id = ? AND soul_id = ?",
        (campaign_id, soul_id),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_aspect_row(row) if row else None


def list_campaign_aspect_records(campaign_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_aspects WHERE campaign_id = ? ORDER BY created_at ASC",
        (campaign_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_campaign_aspect_row(r) for r in rows]


def set_campaign_aspect_active(campaign_id: str, soul_id: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE campaign_aspects SET is_active = 0 WHERE campaign_id = ?",
        (campaign_id,),
    )
    cursor.execute(
        """
        UPDATE campaign_aspects SET is_active = 1, updated_at = CURRENT_TIMESTAMP
        WHERE campaign_id = ? AND soul_id = ?
    """,
        (campaign_id, soul_id),
    )
    conn.commit()
    conn.close()


def update_campaign_aspect_viewpoint(
    campaign_id: str, soul_id: str, viewpoint_location: str
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE campaign_aspects SET viewpoint_location = ?, updated_at = CURRENT_TIMESTAMP
        WHERE campaign_id = ? AND soul_id = ?
    """,
        (viewpoint_location, campaign_id, soul_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_aspects WHERE campaign_id = ? AND soul_id = ?",
        (campaign_id, soul_id),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_aspect_row(row) if row else None


def get_active_campaign_session_for_campaign(
    campaign_id: str,
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM campaign_sessions
        WHERE campaign_id = ? AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    """,
        (campaign_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_session_row(row) if row else None


def set_campaign_session_active_soul(session_id: str, soul_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE campaign_sessions SET active_soul_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
    """,
        (soul_id, session_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_sessions WHERE session_id = ?", (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_session_row(row)


def create_aspect_switch_record(
    *,
    campaign_id: str,
    session_id: str,
    from_soul_id: str,
    to_soul_id: str,
    idempotent: bool,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    switch_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO aspect_switches
            (switch_id, campaign_id, session_id, from_soul_id, to_soul_id, idempotent)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            switch_id,
            campaign_id,
            session_id,
            from_soul_id,
            to_soul_id,
            1 if idempotent else 0,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM aspect_switches WHERE switch_id = ?", (switch_id,))
    row = cursor.fetchone()
    conn.close()
    return {
        "switch_id": row["switch_id"],
        "campaign_id": row["campaign_id"],
        "session_id": row["session_id"],
        "from_soul_id": row["from_soul_id"],
        "to_soul_id": row["to_soul_id"],
        "idempotent": bool(row["idempotent"]),
        "created_at": row["created_at"],
    }


def get_last_aspect_switch_record(
    session_id: str, to_soul_id: str
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM aspect_switches
        WHERE session_id = ? AND to_soul_id = ?
        ORDER BY created_at DESC LIMIT 1
    """,
        (session_id, to_soul_id),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "switch_id": row["switch_id"],
        "campaign_id": row["campaign_id"],
        "session_id": row["session_id"],
        "from_soul_id": row["from_soul_id"],
        "to_soul_id": row["to_soul_id"],
        "idempotent": bool(row["idempotent"]),
        "created_at": row["created_at"],
    }


def _map_place_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "place_id": r["place_id"],
        "place_name": r["place_name"],
        "place_kind": r["place_kind"],
        "public_label": r["public_label"],
        "region_id": r["region_id"],
        "region_precision": r["region_precision"],
        "coordinate_latitude": r["coordinate_latitude"],
        "coordinate_longitude": r["coordinate_longitude"],
        "coordinate_precision_m": r["coordinate_precision_m"],
        "consent_scope": r["consent_scope"],
        "safety_status": r["safety_status"],
        "is_active": bool(r["is_active"]),
        "created_by_soul_id": r["created_by_soul_id"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
        "last_visited_at": r["last_visited_at"]
        if "last_visited_at" in r.keys()
        else None,
    }


def create_place_record(
    *,
    place_name: str,
    place_kind: str = "interpretive",
    public_label: str | None = None,
    region_id: str | None = None,
    region_precision: str = "reduced",
    coordinate_latitude: float | None = None,
    coordinate_longitude: float | None = None,
    coordinate_precision_m: str = "coarse",
    consent_scope: str = "private",
    safety_status: str = "unknown",
    created_by_soul_id: str | None = None,
    place_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    place_id = place_id or str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO places (
            place_id, place_name, place_kind, public_label, region_id,
            region_precision, coordinate_latitude, coordinate_longitude,
            coordinate_precision_m, consent_scope, safety_status, created_by_soul_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            place_id,
            place_name,
            place_kind,
            public_label,
            region_id,
            region_precision,
            coordinate_latitude,
            coordinate_longitude,
            coordinate_precision_m,
            consent_scope,
            safety_status,
            created_by_soul_id,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM places WHERE place_id = ?", (place_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_place_row(row)


def get_place_record(place_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM places WHERE place_id = ?", (place_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_place_row(row) if row else None


def list_place_records(
    *, active_only: bool = True, consent_scope: str | None = None
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM places"
    clauses: list[str] = []
    params: list[Any] = []
    if active_only:
        clauses.append("is_active = 1")
    if consent_scope:
        clauses.append("consent_scope = ?")
        params.append(consent_scope)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_map_place_row(r) for r in rows]


def update_place_safety_status(place_id: str, safety_status: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE places SET safety_status = ?, is_active = CASE
            WHEN ? = 'retired' THEN 0 ELSE is_active END, updated_at = CURRENT_TIMESTAMP
        WHERE place_id = ?
    """,
        (safety_status, safety_status, place_id),
    )
    conn.commit()
    cursor.execute("SELECT * FROM places WHERE place_id = ?", (place_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_place_row(row) if row else None


def add_place_history_record(
    *,
    place_id: str,
    event_type: str,
    event_id: str,
    soul_id: str | None,
    provenance_source_type: str,
    provenance_source_id: str,
    visibility: str = "public_canon",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    history_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO place_history (
            history_id, place_id, event_type, event_id, soul_id,
            provenance_source_type, provenance_source_id, visibility
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            history_id,
            place_id,
            event_type,
            event_id,
            soul_id,
            provenance_source_type,
            provenance_source_id,
            visibility,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM place_history WHERE history_id = ?", (history_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_place_history_row(row)


def _map_place_history_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "history_id": r["history_id"],
        "place_id": r["place_id"],
        "event_type": r["event_type"],
        "event_id": r["event_id"],
        "soul_id": r["soul_id"],
        "provenance_source_type": r["provenance_source_type"],
        "provenance_source_id": r["provenance_source_id"],
        "visibility": r["visibility"],
        "created_at": r["created_at"],
    }


def list_all_place_history_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM place_history ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_place_history_row(r) for r in rows]


def list_place_history_records(
    place_id: str, viewer_soul_id: str | None = None
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM place_history WHERE place_id = ? ORDER BY created_at ASC",
        (place_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    records = [_map_place_history_row(r) for r in rows]
    if viewer_soul_id is None:
        return [r for r in records if r["visibility"] == "public_canon"]
    return [
        r
        for r in records
        if r["visibility"] == "public_canon" or r["soul_id"] == viewer_soul_id
    ]


def get_or_create_location_consent_record(soul_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM location_consent WHERE soul_id = ?", (soul_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {
            "soul_id": row["soul_id"],
            "location_access_granted": bool(row["location_access_granted"]),
            "purpose": row["purpose"],
            "precision_level": row["precision_level"],
            "retention_days": row["retention_days"],
            "updated_at": row["updated_at"],
        }
    cursor.execute(
        """
        INSERT INTO location_consent (soul_id, location_access_granted, purpose, precision_level)
        VALUES (?, 0, '', 'coarse')
    """,
        (soul_id,),
    )
    conn.commit()
    conn.close()
    return {
        "soul_id": soul_id,
        "location_access_granted": False,
        "purpose": "",
        "precision_level": "coarse",
        "retention_days": None,
        "updated_at": None,
    }


def update_location_consent_record(
    *,
    soul_id: str,
    location_access_granted: bool,
    purpose: str = "",
    precision_level: str = "coarse",
    retention_days: int | None = None,
) -> dict[str, Any]:
    get_or_create_location_consent_record(soul_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE location_consent SET
            location_access_granted = ?, purpose = ?, precision_level = ?,
            retention_days = ?, updated_at = CURRENT_TIMESTAMP
        WHERE soul_id = ?
    """,
        (
            1 if location_access_granted else 0,
            purpose,
            precision_level,
            retention_days,
            soul_id,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM location_consent WHERE soul_id = ?", (soul_id,))
    row = cursor.fetchone()
    conn.close()
    return {
        "soul_id": row["soul_id"],
        "location_access_granted": bool(row["location_access_granted"]),
        "purpose": row["purpose"],
        "precision_level": row["precision_level"],
        "retention_days": row["retention_days"],
        "updated_at": row["updated_at"],
    }


def create_location_sample_record(
    *,
    soul_id: str,
    latitude: float,
    longitude: float,
    precision_m: float,
    purpose: str,
    consent_scope: str = "private",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    sample_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO location_samples
            (sample_id, soul_id, latitude, longitude, precision_m, purpose, consent_scope)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (sample_id, soul_id, latitude, longitude, precision_m, purpose, consent_scope),
    )
    conn.commit()
    cursor.execute("SELECT * FROM location_samples WHERE sample_id = ?", (sample_id,))
    row = cursor.fetchone()
    conn.close()
    return {
        "sample_id": row["sample_id"],
        "soul_id": row["soul_id"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "precision_m": row["precision_m"],
        "purpose": row["purpose"],
        "consent_scope": row["consent_scope"],
        "created_at": row["created_at"],
    }


def list_location_samples_records(soul_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM location_samples WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "sample_id": row["sample_id"],
            "soul_id": row["soul_id"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "precision_m": row["precision_m"],
            "purpose": row["purpose"],
            "consent_scope": row["consent_scope"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def create_wandering_discovery_record(
    *,
    soul_id: str,
    place_id: str | None,
    opportunity_type: str,
    opportunity_id: str | None,
    hidden_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    discovery_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO wandering_discoveries
            (discovery_id, soul_id, place_id, opportunity_type, opportunity_id, hidden_details_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            discovery_id,
            soul_id,
            place_id,
            opportunity_type,
            opportunity_id,
            json.dumps(hidden_details or {}),
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM wandering_discoveries WHERE discovery_id = ?", (discovery_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_wandering_discovery_row(row)


def _map_wandering_discovery_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "discovery_id": r["discovery_id"],
        "soul_id": r["soul_id"],
        "place_id": r["place_id"],
        "opportunity_type": r["opportunity_type"],
        "opportunity_id": r["opportunity_id"],
        "hidden_details": _json_or_none(r["hidden_details_json"]) or {},
        "created_at": r["created_at"],
    }


def list_wandering_discoveries_records(soul_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM wandering_discoveries WHERE soul_id = ? ORDER BY created_at DESC",
        (soul_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_wandering_discovery_row(r) for r in rows]


# ---------------------------------------------------------------------------
# Phase 21: Living Visual World persistence. Art Moments and VisualJobs are
# bookkeeping/interpretation, never canonical history.
# ---------------------------------------------------------------------------


def _map_art_moment_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "art_moment_id": r["art_moment_id"],
        "session_id": r["session_id"],
        "campaign_id": r["campaign_id"],
        "soul_id": r["soul_id"],
        "visual_type": r["visual_type"],
        "cooldown_key": r["cooldown_key"],
        "eligibility_rule": r["eligibility_rule"],
        "source_entity_type": r["source_entity_type"],
        "source_entity_id": r["source_entity_id"],
        "title": r["title"],
        "source_evidence": _json_or_none(r["source_evidence_json"]) or [],
        "reference_asset_ids": _json_or_none(r["reference_asset_ids_json"]) or [],
        "spec": _json_or_none(r["spec_json"]) or {},
        "status": r["status"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def _map_visual_job_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "job_id": r["job_id"],
        "art_moment_id": r["art_moment_id"],
        "session_id": r["session_id"],
        "campaign_id": r["campaign_id"],
        "soul_id": r["soul_id"],
        "visual_type": r["visual_type"],
        "provider": r["provider"],
        "provider_model": r["provider_model"],
        "workflow_role": r["workflow_role"],
        "workflow_version": r["workflow_version"],
        "generation_state": r["generation_state"],
        "retry_count": r["retry_count"],
        "spec": _json_or_none(r["spec_json"]) or {},
        "reference_asset_ids": _json_or_none(r["reference_asset_ids_json"]) or [],
        "quarantined_image_url": r["quarantined_image_url"],
        "final_image_url": r["final_image_url"],
        "guardian_status": r["guardian_status"],
        "guardian_report": _json_or_none(r["guardian_report_json"]),
        "failure_reason": r["failure_reason"],
        "superseded_job_id": r["superseded_job_id"],
        "contributor_id": r["contributor_id"],
        "contributor_name": r["contributor_name"],
        "created_at": r["created_at"],
        "started_at": r["started_at"],
        "completed_at": r["completed_at"],
    }


def _map_visual_job_guardian_report_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "report_id": r["report_id"],
        "job_id": r["job_id"],
        "status": r["status"],
        "confidence": r["confidence"],
        "violations": _json_or_none(r["violations_json"]) or [],
        "correction_instructions": (
            _json_or_none(r["correction_instructions_json"]) or []
        ),
        "inspected_at": r["inspected_at"],
    }


def _map_visual_curation_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "curation_id": r["curation_id"],
        "art_moment_id": r["art_moment_id"],
        "contributor_id": r["contributor_id"],
        "contributor_name": r["contributor_name"],
        "style_guidance": r["style_guidance"],
        "composition": r["composition"],
        "mood": r["mood"],
        "motif": r["motif"],
        "symbolism": r["symbolism"],
        "provenance_note": r["provenance_note"],
        "created_at": r["created_at"],
    }


def create_art_moment_record(
    *,
    session_id: str,
    campaign_id: str,
    soul_id: str,
    visual_type: str,
    cooldown_key: str | None,
    eligibility_rule: str,
    source_entity_type: str | None,
    source_entity_id: str | None,
    title: str,
    source_evidence: list[dict[str, Any]],
    reference_asset_ids: list[str],
    spec: dict[str, Any],
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    art_moment_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO art_moments (
            art_moment_id, session_id, campaign_id, soul_id, visual_type,
            cooldown_key, eligibility_rule, source_entity_type, source_entity_id,
            title, source_evidence_json, reference_asset_ids_json, spec_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            art_moment_id,
            session_id,
            campaign_id,
            soul_id,
            visual_type,
            cooldown_key,
            eligibility_rule,
            source_entity_type,
            source_entity_id,
            title,
            json.dumps(source_evidence),
            json.dumps(reference_asset_ids),
            json.dumps(spec),
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM art_moments WHERE art_moment_id = ?", (art_moment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_moment_row(row)


def get_art_moment_record(art_moment_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM art_moments WHERE art_moment_id = ?", (art_moment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_moment_row(row) if row else None


def get_art_moment_by_cooldown_key_record(
    cooldown_key: str,
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM art_moments WHERE cooldown_key = ? ORDER BY created_at DESC LIMIT 1",
        (cooldown_key,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_moment_row(row) if row else None


def list_art_moments_records(session_id: str | None = None) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if session_id:
        cursor.execute(
            "SELECT * FROM art_moments WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
    else:
        cursor.execute("SELECT * FROM art_moments ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_art_moment_row(r) for r in rows]


def update_art_moment_state_record(
    art_moment_id: str, status: str
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE art_moments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE art_moment_id = ?",
        (status, art_moment_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM art_moments WHERE art_moment_id = ?", (art_moment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_moment_row(row) if row else None


def update_art_moment_spec_record(
    art_moment_id: str, spec: dict[str, Any]
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE art_moments SET spec_json = ?, updated_at = CURRENT_TIMESTAMP WHERE art_moment_id = ?",
        (json.dumps(spec), art_moment_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM art_moments WHERE art_moment_id = ?", (art_moment_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_art_moment_row(row) if row else None


def create_visual_job_record(
    *,
    art_moment_id: str,
    session_id: str,
    campaign_id: str,
    soul_id: str,
    visual_type: str,
    spec: dict[str, Any],
    reference_asset_ids: list[str],
    retry_count: int = 0,
    superseded_job_id: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    job_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO visual_jobs (
            job_id, art_moment_id, session_id, campaign_id, soul_id, visual_type,
            retry_count, spec_json, reference_asset_ids_json, superseded_job_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            job_id,
            art_moment_id,
            session_id,
            campaign_id,
            soul_id,
            visual_type,
            retry_count,
            json.dumps(spec),
            json.dumps(reference_asset_ids),
            superseded_job_id,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM visual_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_row(row)


def get_visual_job_record(job_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visual_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_row(row) if row else None


def get_latest_visual_job_for_art_moment_record(
    art_moment_id: str,
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_jobs WHERE art_moment_id = ? ORDER BY created_at DESC LIMIT 1",
        (art_moment_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_row(row) if row else None


def list_visual_jobs_records(
    *,
    session_id: str | None = None,
    art_moment_id: str | None = None,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    clauses = []
    params: list[Any] = []
    if session_id:
        clauses.append("session_id = ?")
        params.append(session_id)
    if art_moment_id:
        clauses.append("art_moment_id = ?")
        params.append(art_moment_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cursor.execute(f"SELECT * FROM visual_jobs {where} ORDER BY created_at ASC", params)
    rows = cursor.fetchall()
    conn.close()
    return [_map_visual_job_row(r) for r in rows]


def update_visual_job_generation_record(
    job_id: str,
    *,
    generation_state: str | None = None,
    provider: str | None = None,
    provider_model: str | None = None,
    workflow_role: str | None = None,
    workflow_version: str | None = None,
    provider_request_id: str | None = None,
    generation_seed: int | None = None,
    quarantined_image_url: str | None = None,
    guardian_status: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    updates = []
    params: list[Any] = []
    if generation_state is not None:
        updates.append("generation_state = ?")
        params.append(generation_state)
        if generation_state == "running":
            updates.append("started_at = COALESCE(started_at, CURRENT_TIMESTAMP)")
        if generation_state in (
            "completed",
            "approved",
            "rejected",
            "hidden",
            "blocked",
            "failed",
            "cancelled",
        ):
            updates.append("completed_at = CURRENT_TIMESTAMP")
    if provider is not None:
        updates.append("provider = ?")
        params.append(provider)
    if provider_model is not None:
        updates.append("provider_model = ?")
        params.append(provider_model)
    if workflow_role is not None:
        updates.append("workflow_role = ?")
        params.append(workflow_role)
    if workflow_version is not None:
        updates.append("workflow_version = ?")
        params.append(workflow_version)
    if provider_request_id is not None:
        updates.append("provider_request_id = ?")
        params.append(provider_request_id)
    if generation_seed is not None:
        updates.append("generation_seed = ?")
        params.append(generation_seed)
    if quarantined_image_url is not None:
        updates.append("quarantined_image_url = ?")
        params.append(quarantined_image_url)
    if guardian_status is not None:
        updates.append("guardian_status = ?")
        params.append(guardian_status)
    if failure_reason is not None:
        updates.append("failure_reason = ?")
        params.append(failure_reason)
    params.append(job_id)
    cursor.execute(
        f"UPDATE visual_jobs SET {', '.join(updates)} WHERE job_id = ?", params
    )
    conn.commit()
    cursor.execute("SELECT * FROM visual_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_row(row)


def update_visual_job_promotion_record(
    job_id: str,
    *,
    final_image_url: str,
    guardian_status: str,
    guardian_report: dict[str, Any],
    generation_state: str,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE visual_jobs
        SET final_image_url = ?, guardian_status = ?, guardian_report_json = ?,
            generation_state = ?, completed_at = CURRENT_TIMESTAMP
        WHERE job_id = ?
    """,
        (
            final_image_url,
            guardian_status,
            json.dumps(guardian_report),
            generation_state,
            job_id,
        ),
    )
    conn.commit()
    cursor.execute("SELECT * FROM visual_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_row(row)


def update_visual_job_state_record(job_id: str, state: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visual_jobs SET generation_state = ?, completed_at = CURRENT_TIMESTAMP WHERE job_id = ?",
        (state, job_id),
    )
    conn.commit()
    cursor.execute("SELECT * FROM visual_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_row(row)


def record_visual_job_guardian_report(
    job_id: str, report: dict[str, Any]
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    report_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO visual_job_guardian_reports (
            report_id, job_id, status, confidence, violations_json,
            correction_instructions_json
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            report_id,
            job_id,
            report.get("status", "pass"),
            report.get("confidence", 0.0),
            json.dumps(report.get("violations", [])),
            json.dumps(report.get("correction_instructions", [])),
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM visual_job_guardian_reports WHERE report_id = ?", (report_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_visual_job_guardian_report_row(row)


def list_visual_job_guardian_reports_records(
    job_id: str,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_job_guardian_reports WHERE job_id = ? ORDER BY inspected_at ASC",
        (job_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_visual_job_guardian_report_row(r) for r in rows]


def create_visual_curation_record(
    *,
    art_moment_id: str,
    contributor_id: str,
    contributor_name: str | None,
    style_guidance: str,
    composition: str,
    mood: str,
    motif: str,
    symbolism: str,
    provenance_note: str,
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    curation_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO visual_curations (
            curation_id, art_moment_id, contributor_id, contributor_name,
            style_guidance, composition, mood, motif, symbolism, provenance_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            curation_id,
            art_moment_id,
            contributor_id,
            contributor_name,
            style_guidance,
            composition,
            mood,
            motif,
            symbolism,
            provenance_note,
        ),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM visual_curations WHERE curation_id = ?", (curation_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_visual_curation_row(row)


def list_visual_curations_records(
    art_moment_id: str,
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM visual_curations WHERE art_moment_id = ? ORDER BY created_at ASC",
        (art_moment_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_visual_curation_row(r) for r in rows]


# ---------------------------------------------------------------------------
# Phase 22: Temporal Pacing & Living Time persistence helpers. These are
# bookkeeping/eligibility records, never canonical history.
# ---------------------------------------------------------------------------


def _map_campaign_time_settings_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "campaign_id": r["campaign_id"],
        "time_policy": r["time_policy"],
        "timezone": r["timezone"],
        "real_time_ratio": r["real_time_ratio"],
        "fictional_anchor_iso": r["fictional_anchor_iso"],
        "fictional_now_iso": r["fictional_now_iso"],
        "updated_at": r["updated_at"],
    }


def get_or_create_campaign_time_settings_record(campaign_id: str) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaign_time_settings WHERE campaign_id = ?", (campaign_id,)
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return _map_campaign_time_settings_row(row)
    cursor.execute(
        """
        INSERT INTO campaign_time_settings (campaign_id, time_policy, timezone)
        VALUES (?, 'none', 'UTC')
    """,
        (campaign_id,),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM campaign_time_settings WHERE campaign_id = ?", (campaign_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_campaign_time_settings_row(row)


def update_campaign_time_settings_record(
    campaign_id: str,
    *,
    time_policy: str | None = None,
    timezone: str | None = None,
    real_time_ratio: float | None = None,
    fictional_anchor_iso: str | None = None,
    fictional_now_iso: str | None = None,
) -> dict[str, Any]:
    settings = get_or_create_campaign_time_settings_record(campaign_id)
    new_policy = time_policy if time_policy is not None else settings["time_policy"]
    new_timezone = timezone if timezone is not None else settings["timezone"]
    new_ratio = (
        real_time_ratio if real_time_ratio is not None else settings["real_time_ratio"]
    )
    new_anchor = (
        fictional_anchor_iso
        if fictional_anchor_iso is not None
        else settings["fictional_anchor_iso"]
    )
    new_now = (
        fictional_now_iso if fictional_now_iso is not None else settings["fictional_now_iso"]
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE campaign_time_settings
        SET time_policy = ?, timezone = ?, real_time_ratio = ?,
            fictional_anchor_iso = ?, fictional_now_iso = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE campaign_id = ?
    """,
        (new_policy, new_timezone, new_ratio, new_anchor, new_now, campaign_id),
    )
    conn.commit()
    conn.close()
    return get_or_create_campaign_time_settings_record(campaign_id)


def _map_aspect_temporal_state_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "campaign_id": r["campaign_id"],
        "soul_id": r["soul_id"],
        "last_active_at": r["last_active_at"],
        "deterministic_event_count": r["deterministic_event_count"],
        "fictional_now_iso": r["fictional_now_iso"],
        "updated_at": r["updated_at"],
    }


def get_or_create_aspect_temporal_state_record(
    campaign_id: str, soul_id: str
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM aspect_temporal_state WHERE campaign_id = ? AND soul_id = ?",
        (campaign_id, soul_id),
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        return _map_aspect_temporal_state_row(row)
    cursor.execute(
        """
        INSERT INTO aspect_temporal_state (campaign_id, soul_id, last_active_at, deterministic_event_count)
        VALUES (?, ?, CURRENT_TIMESTAMP, 0)
    """,
        (campaign_id, soul_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT * FROM aspect_temporal_state WHERE campaign_id = ? AND soul_id = ?",
        (campaign_id, soul_id),
    )
    row = cursor.fetchone()
    conn.close()
    return _map_aspect_temporal_state_row(row)


def update_aspect_temporal_state_record(
    campaign_id: str,
    soul_id: str,
    *,
    last_active_at: str | None = None,
    deterministic_event_count: int | None = None,
) -> dict[str, Any]:
    existing = get_or_create_aspect_temporal_state_record(campaign_id, soul_id)
    new_last = last_active_at if last_active_at is not None else existing["last_active_at"]
    new_count = (
        deterministic_event_count
        if deterministic_event_count is not None
        else existing["deterministic_event_count"]
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE aspect_temporal_state
        SET last_active_at = ?, deterministic_event_count = ?, updated_at = CURRENT_TIMESTAMP
        WHERE campaign_id = ? AND soul_id = ?
    """,
        (new_last, new_count, campaign_id, soul_id),
    )
    conn.commit()
    conn.close()
    return get_or_create_aspect_temporal_state_record(campaign_id, soul_id)


def list_aspect_temporal_state_records(campaign_id: str) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM aspect_temporal_state WHERE campaign_id = ? ORDER BY updated_at ASC",
        (campaign_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_map_aspect_temporal_state_row(r) for r in rows]


def _map_temporal_cooldown_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "cooldown_key": r["cooldown_key"],
        "last_offered_at": r["last_offered_at"],
        "last_offered_event_count": r["last_offered_event_count"],
        "updated_at": r["updated_at"],
    }


def get_temporal_cooldown_record(cooldown_key: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM temporal_cooldowns WHERE cooldown_key = ?", (cooldown_key,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_temporal_cooldown_row(row) if row else None


def record_temporal_cooldown(
    *, cooldown_key: str, last_offered_at: str, last_offered_event_count: int
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO temporal_cooldowns (cooldown_key, last_offered_at, last_offered_event_count, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(cooldown_key) DO UPDATE SET
            last_offered_at = excluded.last_offered_at,
            last_offered_event_count = excluded.last_offered_event_count,
            updated_at = CURRENT_TIMESTAMP
    """,
        (cooldown_key, last_offered_at, last_offered_event_count),
    )
    conn.commit()
    conn.close()
    return get_temporal_cooldown_record(cooldown_key)


def list_temporal_cooldown_records() -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM temporal_cooldowns ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_temporal_cooldown_row(r) for r in rows]


def _map_scheduled_consequence_row(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "consequence_id": r["consequence_id"],
        "session_id": r["session_id"],
        "campaign_id": r["campaign_id"],
        "source_type": r["source_type"],
        "source_id": r["source_id"],
        "rule": r["rule"],
        "eligible_after_iso": r["eligible_after_iso"],
        "min_elapsed_seconds": r["min_elapsed_seconds"],
        "min_events": r["min_events"],
        "note": r["note"],
        "lifecycle_state": r["lifecycle_state"],
        "created_at": r["created_at"],
        "resolved_at": r["resolved_at"],
    }


def create_scheduled_consequence_record(
    *,
    session_id: str,
    campaign_id: str,
    source_type: str,
    source_id: str,
    rule: str,
    eligible_after_iso: str | None = None,
    min_elapsed_seconds: float | None = None,
    min_events: int | None = None,
    note: str = "",
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    consequence_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO scheduled_consequences (
            consequence_id, session_id, campaign_id, source_type, source_id,
            rule, eligible_after_iso, min_elapsed_seconds, min_events, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            consequence_id,
            session_id,
            campaign_id,
            source_type,
            source_id,
            rule,
            eligible_after_iso,
            min_elapsed_seconds,
            min_events,
            note,
        ),
    )
    conn.commit()
    conn.close()
    return get_scheduled_consequence_record(consequence_id)


def get_scheduled_consequence_record(consequence_id: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM scheduled_consequences WHERE consequence_id = ?", (consequence_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _map_scheduled_consequence_row(row) if row else None


def list_scheduled_consequence_records(
    *, session_id: str | None = None, campaign_id: str | None = None
) -> list[dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if session_id:
        cursor.execute(
            "SELECT * FROM scheduled_consequences WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
    elif campaign_id:
        cursor.execute(
            "SELECT * FROM scheduled_consequences WHERE campaign_id = ? ORDER BY created_at ASC",
            (campaign_id,),
        )
    else:
        cursor.execute("SELECT * FROM scheduled_consequences ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [_map_scheduled_consequence_row(r) for r in rows]


def update_scheduled_consequence_state_record(
    consequence_id: str, lifecycle_state: str, *, resolved_at: str | None = None
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if resolved_at is not None:
        cursor.execute(
            """
            UPDATE scheduled_consequences
            SET lifecycle_state = ?, resolved_at = ?
            WHERE consequence_id = ?
        """,
            (lifecycle_state, resolved_at, consequence_id),
        )
    else:
        cursor.execute(
            "UPDATE scheduled_consequences SET lifecycle_state = ? WHERE consequence_id = ?",
            (lifecycle_state, consequence_id),
        )
    conn.commit()
    conn.close()
    return get_scheduled_consequence_record(consequence_id)


def set_promise_deadline_record(
    *, promise_id: str, deadline_iso: str, source_type: str, source_id: str
) -> dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE promises
        SET deadline_iso = ?, deadline_source_type = ?, deadline_source_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE promise_id = ?
    """,
        (deadline_iso, source_type, source_id, promise_id),
    )
    conn.commit()
    conn.close()
    return get_promise_record(promise_id)


def set_campaign_session_last_active(
    session_id: str, last_active_at: str
) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE campaign_sessions SET last_active_at = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
        (last_active_at, session_id),
    )
    conn.commit()
    conn.close()
    return get_campaign_session_record(session_id)


def mark_place_visited(place_id: str, last_visited_at: str) -> dict[str, Any] | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE places SET last_visited_at = ?, updated_at = CURRENT_TIMESTAMP WHERE place_id = ?",
        (last_visited_at, place_id),
    )
    conn.commit()
    conn.close()
    return get_place_record(place_id)
