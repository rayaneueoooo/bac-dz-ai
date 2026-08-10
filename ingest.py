
import json
import re
from pathlib import Path
from pypdf import PdfReader

from config import DATA_DIR
from db import init_db, upsert_document, add_chunks

CHUNK_SIZE = 1800

def split_text(text):
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks=[]
    current=""
    for p in paragraphs:
        if len(current) + len(p) + 1 <= CHUNK_SIZE:
            current = (current + "\n" + p).strip()
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks

def infer_meta(path):
    rel=path.relative_to(DATA_DIR).parts
    kind=rel[0] if rel else "other"
    branch=None; subject=None; year=None
    for part in rel:
        if part.isdigit() and 2000 <= int(part) <= 2100:
            year=int(part)
    if kind in {"lessons","summaries"} and len(rel)>=3:
        branch=rel[1]; subject=rel[2]
    if kind=="bac" and len(rel)>=4:
        branch=rel[2]; subject=rel[3]
    return kind,branch,subject,year

def extract_file(path):
    if path.suffix.lower()==".pdf":
        reader=PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if path.suffix.lower() in {".txt",".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""

def ingest():
    init_db()
    count=0
    for path in DATA_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".pdf",".txt",".md"}:
            continue
        text=extract_file(path)
        if not text.strip():
            continue
        kind,branch,subject,year=infer_meta(path)
        title=path.stem.replace("_"," ")
        con,doc_id=upsert_document(title,str(path.relative_to(DATA_DIR)),kind,branch,subject,year,text[:10000])
        add_chunks(con,doc_id,title,split_text(text))
        con.commit(); con.close()
        count += 1
    print(f"Indexed {count} documents.")
    return count

if __name__=="__main__":
    ingest()
