
from pathlib import Path
import sqlite3
import json
import re
import requests
import pymupdf

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "edugraph.db"
UPLOAD_DIR = BASE_DIR / "uploads"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"


def init_graph_db():
    """Create Knowledge Graph tables without changing existing tables."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                node_type TEXT NOT NULL DEFAULT 'Concept',
                UNIQUE(material_id, name)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER NOT NULL,
                source_node_id INTEGER NOT NULL,
                relationship TEXT NOT NULL,
                target_node_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                FOREIGN KEY(source_node_id) REFERENCES graph_nodes(id),
                FOREIGN KEY(target_node_id) REFERENCES graph_nodes(id)
            )
        """)


def extract_relationships(text):
    """Ask the local LLM to extract factual concept relationships."""
    prompt = f"""
Extract knowledge graph triples from the text below.

Return ONLY valid JSON in this exact format:
{{
  "relationships": [
    {{
      "source": "Normalization",
      "relation": "includes",
      "target": "First Normal Form",
      "source_type": "Concept",
      "target_type": "Concept"
    }}
  ]
}}

Rules:
- Use only facts explicitly supported by the text.
- Keep concept names short and meaningful.
- Do not invent relationships.
- Return an empty relationships list if none are supported.
- Maximum 10 relationships.
- Text may contain irrelevant or incomplete information.

TEXT:
{text}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        },
        timeout=120
    )
    response.raise_for_status()
    data = response.json()
    parsed = json.loads(data["response"])
    return parsed.get("relationships", [])


def save_relationship(material_id, page_number, item):
    source = str(item.get("source", "")).strip()
    relation = str(item.get("relation", "")).strip()
    target = str(item.get("target", "")).strip()

    if not source or not relation or not target:
        return

    if len(source) > 150 or len(target) > 150 or len(relation) > 100:
        return

    with sqlite3.connect(DB_PATH) as conn:
        for name, node_type in (
            (source, item.get("source_type", "Concept")),
            (target, item.get("target_type", "Concept"))
        ):
            conn.execute("""
                INSERT OR IGNORE INTO graph_nodes
                (material_id, name, node_type)
                VALUES (?, ?, ?)
            """, (material_id, name, str(node_type)[:50]))

        source_row = conn.execute("""
            SELECT id FROM graph_nodes
            WHERE material_id = ? AND name = ?
        """, (material_id, source)).fetchone()

        target_row = conn.execute("""
            SELECT id FROM graph_nodes
            WHERE material_id = ? AND name = ?
        """, (material_id, target)).fetchone()

        if not source_row or not target_row:
            return

        conn.execute("""
            INSERT INTO graph_edges
            (material_id, source_node_id, relationship,
             target_node_id, page_number)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM graph_edges
                WHERE material_id = ?
                  AND source_node_id = ?
                  AND relationship = ?
                  AND target_node_id = ?
                  AND page_number = ?
            )
        """, (
            material_id, source_row[0], relation,
            target_row[0], page_number,
            material_id, source_row[0], relation,
            target_row[0], page_number
        ))


def index_pdf_graph(material_id, stored_filename):
    """Extract graph relationships from each readable PDF page."""
    init_graph_db()

    pdf_path = UPLOAD_DIR / stored_filename
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Rebuild this material's graph to avoid stale relationships.
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM graph_edges WHERE material_id = ?",
            (material_id,)
        )
        conn.execute(
            "DELETE FROM graph_nodes WHERE material_id = ?",
            (material_id,)
        )

    total = 0

    with pymupdf.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = " ".join(page.get_text().split())
            if not text:
                continue

            # Keep each local-model request manageable.
            for start in range(0, len(text), 1800):
                piece = text[start:start + 1800]
                if len(piece) < 40:
                    continue

                try:
                    relationships = extract_relationships(piece)
                    for item in relationships:
                        if isinstance(item, dict):
                            save_relationship(
                                material_id, page_number, item
                            )
                            total += 1
                except (requests.RequestException, ValueError, KeyError) as error:
                    print(
                        f"Graph extraction skipped on page "
                        f"{page_number}: {error}"
                    )

    return total


def search_graph(question, material_id=None, limit=10):
    """Find graph relationships whose concepts match the question."""
    init_graph_db()

    words = set(re.findall(r"[a-zA-Z0-9]+", question.lower()))
    if not words:
        return []

    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT s.name, e.relationship, t.name,
                   e.page_number, e.material_id
            FROM graph_edges e
            JOIN graph_nodes s ON s.id = e.source_node_id
            JOIN graph_nodes t ON t.id = e.target_node_id
            WHERE 1 = 1
        """
        params = []

        if material_id is not None:
            query += " AND e.material_id = ?"
            params.append(material_id)

        rows = conn.execute(query, params).fetchall()

    results = []
    for source, relation, target, page, mid in rows:
        combined = f"{source} {relation} {target}".lower()
        if any(word in combined for word in words):
            results.append({
                "source": source,
                "relationship": relation,
                "target": target,
                "page_number": page,
                "material_id": mid
            })

    return results[:limit]


if __name__ == "__main__":
    init_graph_db()
    print("Knowledge Graph tables are ready!")
