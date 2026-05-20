from __future__ import annotations

import sqlite3


def initialize_memory_schema(conn: sqlite3.Connection, applied_at: str) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            applied_at  TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS memories (
            id              TEXT PRIMARY KEY,
            path            TEXT NOT NULL,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL,
            status          TEXT DEFAULT 'active',
            scope           TEXT DEFAULT NULL,
            content         TEXT NOT NULL,
            content_hash    TEXT,
            confidence      REAL DEFAULT 0.9,
            importance      REAL DEFAULT 0.5,
            memory_kind     TEXT DEFAULT 'reference',
            source_type     TEXT,
            source_ref      TEXT,
            source_session_id TEXT DEFAULT NULL,
            captured_at     TEXT DEFAULT NULL,
            last_validated_at TEXT DEFAULT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT,
            indexed_at      TEXT,
            last_seen       TEXT,
            retention_days  INTEGER DEFAULT 365,
            expires_at      TEXT,
            superseded_by   TEXT
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
            name, content,
            content='memories', content_rowid='rowid'
        );

        CREATE TABLE IF NOT EXISTS memory_edges (
            id          TEXT PRIMARY KEY,
            source_id   TEXT NOT NULL,
            target_id   TEXT NOT NULL,
            relation    TEXT NOT NULL,
            confidence  REAL DEFAULT 0.8,
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS memory_events (
            id          TEXT PRIMARY KEY,
            memory_id   TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            payload     TEXT,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memory_write_events (
            id                TEXT PRIMARY KEY,
            memory_id         TEXT NOT NULL,
            session_id        TEXT DEFAULT NULL,
            turn_id           TEXT DEFAULT NULL,
            project_id        TEXT DEFAULT NULL,
            write_type        TEXT NOT NULL,
            confidence        REAL DEFAULT NULL,
            sensitivity       TEXT DEFAULT 'private',
            user_visible_text TEXT NOT NULL,
            source_excerpt    TEXT DEFAULT NULL,
            status            TEXT NOT NULL DEFAULT 'saved',
            created_at        TEXT NOT NULL,
            updated_at        TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS memory_revisions (
            id               TEXT PRIMARY KEY,
            memory_id         TEXT NOT NULL,
            previous_content  TEXT NOT NULL,
            new_content       TEXT NOT NULL,
            edited_by         TEXT NOT NULL,
            reason            TEXT DEFAULT NULL,
            created_at        TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memory_conflicts (
            id                    TEXT PRIMARY KEY,
            existing_memory_id    TEXT NOT NULL,
            proposed_content      TEXT NOT NULL,
            proposed_content_hash TEXT NOT NULL,
            proposed_type         TEXT NOT NULL,
            proposed_scope        TEXT DEFAULT NULL,
            proposed_memory_kind  TEXT,
            proposed_source_type  TEXT,
            proposed_source_session_id TEXT DEFAULT NULL,
            proposed_confidence   REAL,
            proposed_importance   REAL,
            proposed_retention_days INTEGER,
            proposed_expires_at   TEXT DEFAULT NULL,
            conflict_type         TEXT NOT NULL,
            reason                TEXT NOT NULL,
            similarity            REAL DEFAULT 0.0,
            token_overlap         REAL DEFAULT 0.0,
            status                TEXT DEFAULT 'open',
            resolution            TEXT DEFAULT NULL,
            resolved_memory_id    TEXT DEFAULT NULL,
            created_at            TEXT NOT NULL,
            updated_at            TEXT DEFAULT NULL,
            resolved_at           TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS session_transcripts (
            id          TEXT PRIMARY KEY,
            session_id  TEXT NOT NULL,
            project_id  TEXT DEFAULT NULL,
            ghost_mode  INTEGER DEFAULT 0,
            turn_index  INTEGER NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            model       TEXT DEFAULT NULL,
            cost        REAL DEFAULT NULL,
            trace_id    TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
            content,
            content='session_transcripts',
            content_rowid='rowid'
        );

        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id  TEXT PRIMARY KEY,
            type         TEXT NOT NULL,
            session_id   TEXT DEFAULT NULL,
            created_at   TEXT NOT NULL,
            expires_at   TEXT DEFAULT NULL,
            size_bytes   INTEGER DEFAULT 0,
            redacted     INTEGER DEFAULT 0,
            content_path TEXT DEFAULT NULL,
            content      TEXT DEFAULT NULL
        );
        """
    )
    conn.executescript(
        """
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memory_fts(rowid, name, content)
            VALUES (new.rowid, new.name, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memory_fts(memory_fts, rowid, name, content)
            VALUES ('delete', old.rowid, old.name, old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
            INSERT INTO memory_fts(memory_fts, rowid, name, content)
            VALUES ('delete', old.rowid, old.name, old.content);
            INSERT INTO memory_fts(rowid, name, content)
            VALUES (new.rowid, new.name, new.content);
        END;

        CREATE TRIGGER IF NOT EXISTS transcripts_ai AFTER INSERT ON session_transcripts BEGIN
            INSERT INTO transcript_fts(rowid, content) VALUES (new.rowid, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS transcripts_ad AFTER DELETE ON session_transcripts BEGIN
            INSERT INTO transcript_fts(transcript_fts, rowid, content) VALUES ('delete', old.rowid, old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS transcripts_au AFTER UPDATE ON session_transcripts BEGIN
            INSERT INTO transcript_fts(transcript_fts, rowid, content) VALUES ('delete', old.rowid, old.content);
            INSERT INTO transcript_fts(rowid, content) VALUES (new.rowid, new.content);
        END;
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        (1, applied_at, "MVP v0.1"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        (2, applied_at, "session_transcripts FTS5"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
        (3, applied_at, "artifacts table"),
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS memory_conflicts_open_unique
        ON memory_conflicts(existing_memory_id, proposed_content_hash)
        WHERE status = 'open'
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS memory_write_events_session_idx
        ON memory_write_events(session_id, created_at DESC)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS memory_write_events_memory_idx
        ON memory_write_events(memory_id, created_at DESC)
        """
    )
    ensure_memory_control_columns(conn, applied_at)
    ensure_session_transcripts_columns(conn)


def ensure_memory_control_columns(conn: sqlite3.Connection, now: str) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(memories)").fetchall()}
    migrations = {
        "memory_kind": "ALTER TABLE memories ADD COLUMN memory_kind TEXT DEFAULT 'reference'",
        "source_session_id": "ALTER TABLE memories ADD COLUMN source_session_id TEXT DEFAULT NULL",
        "captured_at": "ALTER TABLE memories ADD COLUMN captured_at TEXT DEFAULT NULL",
        "last_validated_at": "ALTER TABLE memories ADD COLUMN last_validated_at TEXT DEFAULT NULL",
        # Phase 3 evidence fields (schema v3)
        "evidence_quote": "ALTER TABLE memories ADD COLUMN evidence_quote TEXT DEFAULT NULL",
        "sensitivity": "ALTER TABLE memories ADD COLUMN sensitivity TEXT DEFAULT 'private'",
        "validity_window_days": "ALTER TABLE memories ADD COLUMN validity_window_days INTEGER DEFAULT NULL",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)
    conn.execute(
        """
        UPDATE memories
        SET memory_kind = CASE
            WHEN type = 'episodic' THEN 'episode'
            WHEN type = 'feedback' THEN 'feedback'
            WHEN type = 'project' THEN 'project'
            WHEN type = 'user' THEN 'identity'
            ELSE 'reference'
        END
        WHERE memory_kind IS NULL OR memory_kind = ''
        """
    )
    conn.execute(
        "UPDATE memories SET last_validated_at = COALESCE(last_validated_at, updated_at, created_at, ?) WHERE last_validated_at IS NULL",
        (now,),
    )


def ensure_session_transcripts_columns(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(session_transcripts)").fetchall()}
    if not columns:
        return  # table doesn't exist yet — initialize_memory_schema will handle it
    migrations = {
        "project_id": "ALTER TABLE session_transcripts ADD COLUMN project_id TEXT DEFAULT NULL",
        "ghost_mode": "ALTER TABLE session_transcripts ADD COLUMN ghost_mode INTEGER DEFAULT 0",
        "model": "ALTER TABLE session_transcripts ADD COLUMN model TEXT DEFAULT NULL",
        "cost": "ALTER TABLE session_transcripts ADD COLUMN cost REAL DEFAULT NULL",
        "trace_id": "ALTER TABLE session_transcripts ADD COLUMN trace_id TEXT DEFAULT NULL",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)
