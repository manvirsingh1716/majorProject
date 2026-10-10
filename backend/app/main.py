from datetime import datetime, timezone
from typing import Literal
import re
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .ollama_service import OllamaError, analyze_with_ollama, is_ollama_enabled, ollama_model, ollama_status
from .database import Document, KnowledgeChunk, Project, SessionLocal, init_db
from .knowledge_service import chunk_text, extract_text, search_chunks

load_dotenv()

app = FastAPI(title="Meeting2Action API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    init_db()

class AnalyzeRequest(BaseModel):
    title: str = "Untitled meeting"
    project: str = "Payment Platform"
    transcript: str = Field(min_length=20)

class Citation(BaseModel):
    segment_id: str
    quote: str
    speaker: str

class Decision(BaseModel):
    id: str
    description: str
    status: Literal["CONFIRMED", "PROPOSED", "REJECTED", "UNRESOLVED"]
    confidence: int
    citation: Citation

class ActionItem(BaseModel):
    id: str
    title: str
    description: str
    owner: str | None
    deadline: str | None
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    status: Literal["OPEN", "IN_PROGRESS", "DONE"]
    citation: Citation

class MeetingAnalysis(BaseModel):
    id: str
    title: str
    project: str
    analyzed_at: str
    summary: str
    topics: list[str]
    decisions: list[Decision]
    action_items: list[ActionItem]
    open_questions: list[str]
    risks: list[str]
    transcript: str
    analysis_source: Literal["ollama", "fallback"] = "fallback"
    model: str | None = None

class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None

class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=8, ge=1, le=20)

class VerifyRequest(BaseModel):
    decision: str = Field(min_length=3)

class Evidence(BaseModel):
    document_id: int
    filename: str
    chunk_id: str
    content: str
    score: float

class VerificationResponse(BaseModel):
    result: Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS"]
    explanation: str
    evidence: list[Evidence]


def speaker_and_quote(line: str, index: int) -> Citation:
    match = re.match(r"\s*([^:]+):\s*(.*)", line)
    speaker = match.group(1).strip() if match else "Meeting transcript"
    quote = match.group(2).strip() if match else line.strip()
    return Citation(segment_id=f"seg-{index + 1:02d}", quote=quote, speaker=speaker)


def analyze_transcript(request: AnalyzeRequest) -> MeetingAnalysis:
    lines = [line.strip() for line in request.transcript.splitlines() if line.strip()]
    decisions: list[Decision] = []
    action_items: list[ActionItem] = []
    open_questions: list[str] = []
    risks: list[str] = []
    topics: list[str] = []

    for index, line in enumerate(lines):
        lower = line.lower()
        citation = speaker_and_quote(line, index)
        if any(token in lower for token in ("decide", "decision", "agreed", "move ", "will use", "approved")):
            status = "CONFIRMED" if any(token in lower for token in ("agreed", "approved", "decided")) else "PROPOSED"
            decisions.append(Decision(id=f"decision-{len(decisions) + 1}", description=citation.quote, status=status, confidence=91 if status == "CONFIRMED" else 78, citation=citation))
        if any(token in lower for token in ("action:", "todo:", "will ", "owner:", "follow up")):
            owner_match = re.search(r"(?:owner|assigned to)\s*[:\-]?\s*([A-Z][\w.-]+)", line, re.I)
            action_items.append(ActionItem(id=f"action-{len(action_items) + 1}", title=citation.quote[:72], description=citation.quote, owner=owner_match.group(1) if owner_match else None, deadline=None, priority="HIGH" if any(token in lower for token in ("urgent", "high", "blocker")) else "MEDIUM", status="OPEN", citation=citation))
        if "?" in line or any(token in lower for token in ("open question", "unclear", "need to confirm")):
            open_questions.append(citation.quote)
        if any(token in lower for token in ("risk", "concern", "might", "blocked", "failure")):
            risks.append(citation.quote)
        if any(token in lower for token in ("gateway", "validation", "architecture", "payment", "release", "service")):
            topic = "Payment architecture" if "payment" in lower or "gateway" in lower else "Delivery planning"
            if topic not in topics:
                topics.append(topic)

    if not decisions and lines:
        citation = speaker_and_quote(lines[0], 0)
        decisions.append(Decision(id="decision-1", description="No explicit decision detected; review transcript context.", status="UNRESOLVED", confidence=42, citation=citation))
    if not topics:
        topics = ["General meeting discussion"]

    return MeetingAnalysis(
        id=f"meeting-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        title=request.title,
        project=request.project,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        summary=f"The meeting covered {', '.join(topics[:2]).lower()} with {len(decisions)} decision candidate(s) and {len(action_items)} follow-up action(s).",
        topics=topics,
        decisions=decisions,
        action_items=action_items,
        open_questions=open_questions,
        risks=risks,
        transcript=request.transcript,
        analysis_source="fallback",
    )

@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "ollama": ollama_status()}


@app.get("/api/ollama/status")
def ollama_health() -> dict[str, object]:
    return ollama_status()

@app.post("/api/projects")
def create_project(request: ProjectRequest) -> dict[str, object]:
    with SessionLocal() as session:
        project = Project(name=request.name, description=request.description)
        session.add(project)
        try:
            session.commit()
        except Exception as error:
            session.rollback()
            raise HTTPException(status_code=409, detail="A project with this name already exists") from error
        session.refresh(project)
        return {"id": project.id, "name": project.name, "description": project.description, "created_at": project.created_at}

@app.get("/api/projects")
def list_projects() -> list[dict[str, object]]:
    with SessionLocal() as session:
        return [{"id": project.id, "name": project.name, "description": project.description, "created_at": project.created_at} for project in session.query(Project).order_by(Project.created_at.desc()).all()]

@app.post("/api/projects/{project_id}/documents")
async def upload_document(project_id: int, file: UploadFile = File(...)) -> dict[str, object]:
    content = await file.read()
    filename = file.filename or "uploaded-document"
    try:
        text = extract_text(filename, content)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    with SessionLocal() as session:
        if session.get(Project, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        document_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        document = Document(project_id=project_id, filename=filename, document_type=document_type)
        session.add(document)
        session.flush()
        chunks = chunk_text(text)
        for index, chunk in enumerate(chunks, start=1):
            session.add(KnowledgeChunk(project_id=project_id, document_id=document.id, chunk_id=f"doc-{document.id}-chunk-{index}", content=chunk))
        session.commit()
        return {"document_id": document.id, "project_id": project_id, "filename": filename, "document_type": document_type, "chunks_created": len(chunks)}

@app.get("/api/projects/{project_id}/documents")
def list_documents(project_id: int) -> list[dict[str, object]]:
    with SessionLocal() as session:
        if session.get(Project, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return [{"id": document.id, "filename": document.filename, "document_type": document.document_type, "created_at": document.created_at} for document in session.query(Document).filter_by(project_id=project_id).order_by(Document.created_at.desc()).all()]

@app.post("/api/projects/{project_id}/search")
def search_project(project_id: int, request: SearchRequest) -> list[Evidence]:
    with SessionLocal() as session:
        if session.get(Project, project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        rows = session.query(KnowledgeChunk).filter(KnowledgeChunk.project_id == project_id).all()
        matches = search_chunks([(chunk, chunk.content) for chunk in rows], request.query, request.limit)
        return [Evidence(document_id=chunk.document_id, filename=session.get(Document, chunk.document_id).filename, chunk_id=chunk.chunk_id, content=content, score=round(score, 3)) for chunk, content, score in matches]

@app.post("/api/projects/{project_id}/verify", response_model=VerificationResponse)
def verify_decision(project_id: int, request: VerifyRequest) -> VerificationResponse:
    evidence = search_project(project_id, SearchRequest(query=request.decision, limit=8))
    if not evidence:
        return VerificationResponse(result="INSUFFICIENT_EVIDENCE", explanation="No project knowledge matched this decision. The system cannot verify it yet.", evidence=[])
    proposal_terms = set(re.findall(r"[\w-]+", request.decision.lower()))
    contradiction_terms = {"not", "never", "remains", "instead", "reject", "avoid", "mustn't"}
    contradictory = [item for item in evidence if contradiction_terms.intersection(set(re.findall(r"[\w-]+", item.content.lower()))) and proposal_terms.intersection(set(re.findall(r"[\w-]+", item.content.lower())))]
    if contradictory:
        return VerificationResponse(result="CONTRADICTED", explanation="Project evidence contains language that conflicts with the proposed decision. Review whether that evidence is current or superseded before acting.", evidence=evidence)
    if len(evidence) == 1 and evidence[0].score < 0.4:
        return VerificationResponse(result="AMBIGUOUS", explanation="A weakly matching source was found, but it is not sufficient to establish support.", evidence=evidence)
    return VerificationResponse(result="SUPPORTED", explanation="The proposed decision matches project knowledge retrieved from the selected project.", evidence=evidence)

@app.post("/api/meetings/analyze", response_model=MeetingAnalysis)
def analyze_meeting(request: AnalyzeRequest) -> MeetingAnalysis:
    if is_ollama_enabled():
        try:
            generated = analyze_with_ollama(request.title, request.project, request.transcript)
            return MeetingAnalysis.model_validate({
                **generated,
                "id": f"meeting-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "title": request.title,
                "project": request.project,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "transcript": request.transcript,
                "analysis_source": "ollama",
                "model": ollama_model(),
            })
        except (OllamaError, ValueError):
            pass
    return analyze_transcript(request)
