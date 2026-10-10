from datetime import datetime, timezone
from typing import Literal
import re
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .ollama_service import OllamaError, analyze_with_ollama, is_ollama_enabled, ollama_model, ollama_status

load_dotenv()

app = FastAPI(title="Meeting2Action API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
