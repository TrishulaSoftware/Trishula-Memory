"""
memory_engine.py — Sovereign Persistent Memory Core
Zero-LangChain, Zero-LiteLLM architecture. Pure SQLite and structured fact extraction.
Part of Trishula Sovereign Fleet (Trishula Software)
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

class SovereignMemory:
    """
    Persistent cross-session memory ledger for autonomous agents.
    Stores episodic events, extracted user preferences, and institutional knowledge.
    """
    def __init__(self, db_path: str = "trishula_memory.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT,
                key TEXT,
                value TEXT,
                confidence REAL,
                decay_score REAL DEFAULT 1.0,
                created_at TEXT,
                last_accessed TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_cat_key ON memories (category, key)
        """)
        conn.commit()
        conn.close()

    def add_memory(self, category: str, key: str, value: Any, confidence: float = 1.0) -> str:
        """Stores or updates a memory entry."""
        val_str = json.dumps(value) if not isinstance(value, str) else value
        mem_id = hashlib.sha256(f"{category}:{key}".encode()).hexdigest()[:16]
        now = datetime.now(timezone.utc).isoformat() + "Z"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memories (id, category, key, value, confidence, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                value = excluded.value,
                confidence = excluded.confidence,
                last_accessed = excluded.last_accessed
        """, (mem_id, category, key, val_str, confidence, now, now))
        conn.commit()
        conn.close()
        return mem_id

    def get_memory(self, category: str, key: str) -> Optional[Any]:
        """Retrieves a memory entry by category and key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM memories WHERE category = ? AND key = ?", (category, key))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return row[0]

    def list_category(self, category: str) -> List[Dict[str, Any]]:
        """Lists all active memories in a category."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, key, value, confidence, last_accessed FROM memories WHERE category = ?", (category,))
        rows = cursor.fetchall()
        conn.close()
        res = []
        for r in rows:
            try:
                v = json.loads(r[2])
            except Exception:
                v = r[2]
            res.append({"id": r[0], "key": r[1], "value": v, "confidence": r[3], "last_accessed": r[4]})
        return res
