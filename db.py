
import sqlite3
from config import DB_PATH

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        kind TEXT NOT NULL,
        branch TEXT,
        subject TEXT,
        year INTEGER,
        content TEXT DEFAULT ''
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
        document_id UNINDEXED,
        title,
        text,
        tokenize='unicode61'
    );

    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch TEXT,
        subject TEXT,
        question TEXT NOT NULL,
        choices TEXT,
        answer TEXT NOT NULL,
        explanation TEXT DEFAULT ''
    );
    """)
    con.commit()
    con.close()

def upsert_document(title, path, kind, branch=None, subject=None, year=None, content=""):
    con = connect()
    con.execute("""
        INSERT INTO documents(title,path,kind,branch,subject,year,content)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(path) DO UPDATE SET
          title=excluded.title, kind=excluded.kind, branch=excluded.branch,
          subject=excluded.subject, year=excluded.year, content=excluded.content
    """, (title,path,kind,branch,subject,year,content))
    doc_id = con.execute("SELECT id FROM documents WHERE path=?", (path,)).fetchone()[0]
    con.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
    return con, doc_id

def add_chunks(con, doc_id, title, chunks):
    con.executemany(
        "INSERT INTO chunks(document_id,title,text) VALUES(?,?,?)",
        [(doc_id,title,c) for c in chunks if c.strip()]
    )

def search_chunks(query, limit=8, branch=None, subject=None, year=None):
    con = connect()
    sql = """
      SELECT c.document_id, c.title, c.text, d.path, d.kind, d.branch, d.subject, d.year
      FROM chunks c JOIN documents d ON d.id=c.document_id
      WHERE chunks MATCH ?
    """
    params=[query]
    if branch:
        sql += " AND (d.branch=? OR d.branch IS NULL)"
        params.append(branch)
    if subject:
        sql += " AND (d.subject=? OR d.subject IS NULL)"
        params.append(subject)
    if year:
        sql += " AND (d.year=? OR d.year IS NULL)"
        params.append(year)
    sql += " LIMIT ?"
    params.append(limit)
    try:
        rows=con.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # Fallback for Arabic/punctuation-heavy questions.
        safe = " ".join(_words(query))
        rows=con.execute(
            "SELECT c.document_id,c.title,c.text,d.path,d.kind,d.branch,d.subject,d.year "
            "FROM chunks c JOIN documents d ON d.id=c.document_id "
            "WHERE c.text LIKE ? LIMIT ?", ("%"+safe+"%",limit)
        ).fetchall()
    con.close()
    return rows

def _words(s):
    return [w for w in s.split() if len(w) > 2][:8]
