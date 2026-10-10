import io
import re
from pathlib import Path
from pypdf import PdfReader
from docx import Document as WordDocument

SUPPORTED_TYPES = {"txt", "md", "pdf", "docx"}

def extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in SUPPORTED_TYPES:
        raise ValueError("Supported documents are PDF, TXT, Markdown, and DOCX")
    if extension in {"txt", "md"}:
        return content.decode("utf-8", errors="replace")
    if extension == "pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
    document = WordDocument(io.BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)

def chunk_text(text: str, words_per_chunk: int = 180) -> list[str]:
    words = re.findall(r"\S+", text)
    return [" ".join(words[index:index + words_per_chunk]) for index in range(0, len(words), words_per_chunk)] or ["(No extractable text found.)"]

def search_chunks(chunks: list[tuple[object, str]], query: str, limit: int = 8) -> list[tuple[object, str, float]]:
    terms = {term.lower() for term in re.findall(r"[\w-]+", query) if len(term) > 2}
    scored = []
    for chunk, content in chunks:
        words = set(re.findall(r"[\w-]+", content.lower()))
        score = sum(1 for term in terms if term in words) / max(len(terms), 1)
        if score > 0:
            scored.append((chunk, content, score))
    return sorted(scored, key=lambda item: item[2], reverse=True)[:limit]
