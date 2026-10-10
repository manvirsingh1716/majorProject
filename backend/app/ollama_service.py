import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    pass


def ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2:1b")


def ollama_timeout() -> float:
    return float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))


def is_ollama_enabled() -> bool:
    return os.getenv("USE_OLLAMA", "true").lower() not in {"0", "false", "no", "off"}


def ollama_status() -> dict[str, object]:
    request = Request(f"{ollama_base_url()}/api/tags", method="GET")
    try:
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [model.get("name") for model in payload.get("models", [])]
        return {"enabled": is_ollama_enabled(), "reachable": True, "model": ollama_model(), "models": models}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {"enabled": is_ollama_enabled(), "reachable": False, "model": ollama_model(), "models": []}


def normalize_result(result: dict[str, object]) -> dict[str, object]:
    if not isinstance(result.get("summary"), str):
        result["summary"] = "The meeting was analyzed locally with Ollama; review the extracted items and transcript citations."
    if not isinstance(result.get("topics"), list):
        result["topics"] = ["Meeting discussion"]
    result["topics"] = [str(topic) for topic in result["topics"] if topic is not None]
    if not isinstance(result.get("open_questions"), list):
        result["open_questions"] = []
    result["open_questions"] = [str(question) for question in result["open_questions"] if question is not None]
    if not isinstance(result.get("risks"), list):
        result["risks"] = []
    result["risks"] = [str(risk) for risk in result["risks"] if risk is not None]
    decisions = result.get("decisions", [])
    if isinstance(decisions, list):
        for index, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                continue
            citation = decision.get("citation") if isinstance(decision.get("citation"), dict) else {}
            if not isinstance(decision.get("id"), str):
                decision["id"] = f"decision-{index + 1}"
            if not isinstance(decision.get("description"), str):
                decision["description"] = str(citation.get("quote", "Unresolved decision requiring review."))
            if not isinstance(citation.get("segment_id"), str) or not isinstance(citation.get("quote"), str) or not isinstance(citation.get("speaker"), str):
                decision["citation"] = {"segment_id": f"seg-{index + 1:02d}", "quote": decision["description"], "speaker": "Meeting transcript"}
            status = decision.get("status")
            if status not in {"CONFIRMED", "PROPOSED", "REJECTED", "UNRESOLVED"}:
                description = str(decision.get("description", "")).lower()
                decision["status"] = "CONFIRMED" if any(word in description for word in ("agreed", "approved", "decided")) else "PROPOSED"
            if not isinstance(decision.get("confidence"), int):
                decision["confidence"] = 50
    actions = result.get("action_items", [])
    if isinstance(actions, list):
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                continue
            citation = action.get("citation") if isinstance(action.get("citation"), dict) else {}
            if not isinstance(action.get("id"), str):
                action["id"] = f"action-{index + 1}"
            if not isinstance(action.get("title"), str):
                action["title"] = str(citation.get("quote", "Follow-up action requiring review."))[:72]
            if not isinstance(action.get("description"), str):
                action["description"] = str(citation.get("quote", action["title"]))
            if not isinstance(citation.get("segment_id"), str) or not isinstance(citation.get("quote"), str) or not isinstance(citation.get("speaker"), str):
                action["citation"] = {"segment_id": f"seg-{index + 1:02d}", "quote": action["description"], "speaker": "Meeting transcript"}
            if action.get("priority") not in {"HIGH", "MEDIUM", "LOW"}:
                action["priority"] = "HIGH" if any(word in str(action.get("description", "")).lower() for word in ("urgent", "blocker", "high")) else "MEDIUM"
            if action.get("status") not in {"OPEN", "IN_PROGRESS", "DONE"}:
                action["status"] = "OPEN"
            if isinstance(action.get("owner"), str):
                action["owner"] = action["owner"].rstrip(".,")
    return result


def analyze_with_ollama(title: str, project: str, transcript: str) -> dict[str, object]:
    citation_schema = {
        "type": "object",
        "properties": {"segment_id": {"type": "string"}, "quote": {"type": "string"}, "speaker": {"type": "string"}},
        "required": ["segment_id", "quote", "speaker"],
    }
    decision_schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}, "description": {"type": "string"}, "status": {"type": "string", "enum": ["CONFIRMED", "PROPOSED", "REJECTED", "UNRESOLVED"]}, "confidence": {"type": "integer", "minimum": 0, "maximum": 100}, "citation": citation_schema},
        "required": ["id", "description", "status", "confidence", "citation"],
    }
    action_schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"}, "owner": {"type": ["string", "null"]}, "deadline": {"type": ["string", "null"]}, "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]}, "status": {"type": "string", "enum": ["OPEN", "IN_PROGRESS", "DONE"]}, "citation": citation_schema},
        "required": ["id", "title", "description", "owner", "deadline", "priority", "status", "citation"],
    }
    schema = {"type": "object", "properties": {"summary": {"type": "string"}, "topics": {"type": "array", "items": {"type": "string"}}, "decisions": {"type": "array", "items": decision_schema}, "action_items": {"type": "array", "items": action_schema}, "open_questions": {"type": "array", "items": {"type": "string"}}, "risks": {"type": "array", "items": {"type": "string"}}}, "required": ["summary", "topics", "decisions", "action_items", "open_questions", "risks"]}
    prompt = f"""You are the meeting intelligence engine for Meeting2Action.
Analyze this transcript and return ONLY valid JSON matching the JSON Schema below.
Do not invent owners, deadlines, decisions, risks, or evidence. Use null when the transcript does not provide a value.
Every decision and action item must cite one exact line from the transcript. Segment IDs are one-based transcript line IDs: seg-01, seg-02, etc.
Confidence is an integer from 0 to 100. Keep decisions separate when they have different statuses.

Meeting title: {title}
Project: {project}

Schema:
{json.dumps(schema)}

Transcript:
{transcript}
"""
    body = json.dumps({"model": ollama_model(), "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.1}}).encode("utf-8")
    request = Request(f"{ollama_base_url()}/api/generate", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=ollama_timeout()) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        result = json.loads(response_payload["response"])
        if not isinstance(result, dict):
            raise OllamaError("Ollama returned a non-object analysis")
        return normalize_result(result)
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise OllamaError(f"Ollama analysis failed: {error}") from error
