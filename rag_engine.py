
from pathlib import Path
import sqlite3
import numpy as np
import pymupdf
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "edugraph.db"
UPLOAD_DIR = BASE_DIR / "uploads"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def init_rag_db():
    """Create a separate table for searchable PDF text."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS material_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY(material_id) REFERENCES materials(id)
            )
        """)


def split_text(text, chunk_size=900, overlap=150):
    """Split PDF text into overlapping chunks."""
    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def index_pdf(material_id, stored_filename):
    """Extract a PDF, create embeddings, and save searchable chunks."""
    pdf_path = UPLOAD_DIR / stored_filename

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    init_rag_db()
    all_chunks = []

    with pymupdf.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text()

            for chunk_index, chunk in enumerate(split_text(text)):
                all_chunks.append(
                    (page_number, chunk_index, chunk)
                )

    if not all_chunks:
        raise ValueError(
            "No readable text found in this PDF."
        )

    model = get_model()
    texts = [item[2] for item in all_chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM material_chunks WHERE material_id = ?",
            (material_id,)
        )

        conn.executemany("""
            INSERT INTO material_chunks
            (material_id, page_number, chunk_index,
             chunk_text, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (
                material_id,
                page_number,
                chunk_index,
                chunk,
                np.asarray(embedding, dtype=np.float32).tobytes()
            )
            for (page_number, chunk_index, chunk), embedding
            in zip(all_chunks, embeddings)
        ])

    return len(all_chunks)


if __name__ == "__main__":
    init_rag_db()
    print("RAG database table is ready!")


def search_materials(
    question,
    top_k=4,
    subject=None,
    professor_id=None,
    material_id=None
):
    """Find the most relevant PDF chunks for a question."""
    init_rag_db()

    model = get_model()
    query_embedding = model.encode(
        [question],
        normalize_embeddings=True
    )[0]


    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT
                mc.material_id,
                mc.page_number,
                mc.chunk_text,
                mc.embedding
            FROM material_chunks AS mc
            JOIN materials AS m ON m.id = mc.material_id
            WHERE 1 = 1
        """
        params = []

        if subject:
            query += " AND m.subject = ?"
            params.append(subject)

        if professor_id is not None:
            query += " AND m.professor_id = ?"
            params.append(professor_id)

        if material_id is not None:
            query += " AND mc.material_id = ?"
            params.append(material_id)
        rows = conn.execute(query, params).fetchall()


    if not rows:
        return []

    results = []

    for material_id, page_number, chunk_text, blob in rows:
        embedding = np.frombuffer(blob, dtype=np.float32)
        score = float(np.dot(query_embedding, embedding))

        results.append({
            "material_id": material_id,
            "page_number": page_number,
            "text": chunk_text,
            "score": score
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


def answer_question(
    question,
    top_k=4,
    subject=None,
    professor_id=None,
    material_id=None,
    results=None,
    graph_results=None
):
    """Answer a question using retrieved PDF notes and local Ollama."""
    import requests

    if results is None:
        results = search_materials(
            question,
            top_k=top_k,
            subject=subject,
            professor_id=professor_id,
            material_id=material_id
        )

    if not results:
        return "Uploaded notes mein readable information nahi mili."

    context_parts = []

    for item in results:
        context_parts.append(
            f"[Page {item['page_number']}]\n{item['text']}"
        )

    context = "\n\n".join(context_parts)

    graph_context = ""

    if graph_results:
        graph_context = "\n".join(
            f"- {item['source']} "
            f"{item['relationship']} "
            f"{item['target']} "
            f"(Page {item['page_number']})"
            for item in graph_results
        )
    else:
        graph_context = "No matching graph relationships found."

    prompt = f"""
You are EduGraphAI, a college study assistant.

Use the professor notes as the primary evidence.
Use the knowledge graph relationships as supplementary evidence
to explain connections between concepts.

Answer in simple, student-friendly language.

Follow these rules:
1. Answer the student's exact question using the professor notes as the primary source.
2. Use Knowledge Graph relationships only when relevant to the question.
3. Do not present database concepts such as Primary Key or NULL as normal forms.
4. Do not repeat the same normal form or explanation.
5. Explain each normal form accurately according to the provided evidence.
6. Do not invent facts or relationships.
7. If evidence is insufficient or conflicting, say so clearly.
8. Mention relevant source page numbers when available.
9. Keep the answer organized with headings and numbered points.
KNOWLEDGE GRAPH RELATIONSHIPS:
{graph_context}

PROFESSOR NOTES:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""

    try:
        print("AI is generating the answer...")
        response = requests.post(
           
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        print("AI response received.")
        return response.json()["response"].strip()

    except requests.RequestException as error:
        return f"Could not connect to the local AI model: {error}"



if __name__ == "__main__":
    init_rag_db()
    print("RAG database table is ready!")
