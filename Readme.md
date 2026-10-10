# Meeting2Action

## Project Type

College Major Project

## Project Title

**Meeting2Action: An Agentic Meeting-to-Execution Platform using Cost-Aware RAG**

## Project Objective

Build a web application that converts meeting transcripts into structured project information, retrieves relevant organizational knowledge, verifies proposed decisions against existing project context, identifies contradictions and risks, and converts approved action items into executable project tasks.

The system should also investigate whether multi-agent verification provides enough improvement in decision reliability to justify its additional token cost and latency.

---

# 1. Core Problem

Organizations hold many meetings where important decisions, action items, owners, deadlines, and unresolved questions are discussed.

After meetings:

* decisions may be forgotten
* action items may not be recorded
* owners may be unclear
* previous project context may be forgotten
* contradictory decisions may exist
* Jira tasks may not accurately represent the meeting
* teams may not know why a decision was made

Meeting2Action attempts to solve this by creating a traceable pipeline:

Meeting → Understanding → Project Knowledge → Verification → Approval → Execution → Tracking

---

# 2. Core Product

The system has seven major capabilities:

1. Meeting transcript analysis
2. Project knowledge management
3. RAG-based evidence retrieval
4. Decision verification
5. Multi-agent verification
6. External task execution
7. Execution tracking

---

# 3. Technology Stack

## Frontend

React + Vite + TypeScript

## Backend

Python + FastAPI

## Database

PostgreSQL

## Vector Database

Qdrant

## AI

LLM provider through an abstraction layer.

The implementation should allow switching between different LLM providers without changing business logic.

## Embeddings

Use a configurable embedding model.

## Authentication

JWT-based authentication.

## External integrations

Start with Jira.

GitHub and Calendar are optional future integrations.

## Agent orchestration

Keep orchestration simple.

A lightweight Python implementation may be used initially.

LangGraph may be introduced when multi-agent workflows require stateful orchestration or human approval checkpoints.

## Deployment

Docker Compose.

---

# 4. Design Principles

The project must prioritize:

* simplicity
* reliability
* modularity
* explainability
* traceability
* measurable AI performance
* low unnecessary infrastructure complexity

Do NOT introduce:

* Kubernetes
* microservices
* Kafka
* Redis unless clearly required
* complex event-driven architecture
* unnecessary distributed systems
* autonomous agents performing unrestricted actions

The system should initially be a modular monolithic FastAPI application.

---

# 5. Phase 1: Meeting Intelligence

## Goal

Convert a transcript into structured meeting information.

## Input

A user can:

* upload a TXT or Markdown transcript
* paste transcript text

## Output

The AI must extract:

### Summary

A concise meeting summary.

### Topics

Major topics discussed.

### Decisions

Each decision must contain:

* description
* status
* confidence
* source transcript segment

Decision statuses:

* PROPOSED
* CONFIRMED
* REJECTED
* UNRESOLVED

### Action Items

Each action item must contain:

* title
* description
* owner
* deadline
* priority
* status
* source transcript segment

Missing information must remain null or unknown.

The AI must not invent owners or deadlines.

### Open Questions

Questions that remain unresolved.

### Risks

Potential risks explicitly discussed during the meeting.

## Phase 1 UI

Dashboard

Meeting list

Meeting detail page

Meeting summary

Decisions

Action items

Open questions

Transcript

Users must be able to edit extracted decisions and action items.

## Phase 1 requirement

Every AI-generated item must be traceable to the original transcript.

---

# 6. Phase 2: Project Knowledge

Users can create projects.

Each project contains a knowledge base.

Supported initial documents:

* PDF
* TXT
* Markdown
* DOCX

Document pipeline:

Document → Text extraction → Chunking → Embedding → Qdrant

Metadata must include:

* project ID
* document ID
* filename
* document type
* page number when available
* chunk ID
* creation date

PostgreSQL stores document metadata.

Qdrant stores embeddings and searchable chunks.

The system must support project-level isolation.

A query from Project A must never retrieve knowledge from Project B.

---

# 7. Phase 3: RAG

For each decision or user question:

1. Generate a search query.
2. Retrieve relevant project documents.
3. Retrieve relevant previous meetings.
4. Combine retrieved evidence.
5. Provide evidence to the LLM.
6. Generate an answer or verification result.

Initially implement:

* vector retrieval

Then implement:

* keyword retrieval

Then:

* hybrid retrieval

The system should return source references with every evidence-backed answer.

---

# 8. Decision Verification

Each decision candidate should be compared against project knowledge.

Possible verification results:

SUPPORTED

CONTRADICTED

INSUFFICIENT_EVIDENCE

AMBIGUOUS

The verifier must explain:

* what the current meeting proposes
* what existing project evidence says
* why the evidence supports or contradicts the proposal
* which sources were used

The system must not claim that a decision is incorrect solely because an old document disagrees with it.

Documents may be outdated or superseded.

---

# 9. Phase 4: Multi-Agent Verification

Use four agents.

## Decision Agent

Determines what decision was actually proposed or made.

## Evidence Agent

Retrieves and analyzes supporting and contradictory evidence.

## Technical Critic

Analyzes technical implications and potential risks.

## Judge

Receives the outputs of the other agents and produces a final structured verdict.

The judge must provide evidence references.

Agents must not invent sources.

Every claim requiring evidence must reference retrieved project information.

---

# 10. Phase 5: Cost-Aware Routing

Do not use multi-agent verification for every decision.

Create a difficulty analyzer.

Inputs may include:

* ambiguity
* evidence conflict
* retrieval quality
* technical impact
* missing information

Calculate a difficulty score.

Initial routing can use deterministic rules.

Example:

0–3:

Simple RAG

4–6:

Enhanced verification

7–10:

Multi-agent verification

These thresholds are configurable and must be evaluated experimentally.

For every AI operation record:

* model
* input tokens
* output tokens
* estimated cost
* latency
* strategy
* verification result

The system must compare:

1. Single LLM
2. Vector RAG
3. Hybrid RAG
4. Multi-agent RAG
5. Cost-aware RAG

---

# 11. Phase 6: Execution

After verification, action items can be converted into external tasks.

Human approval is required before executing external actions.

Initial integration:

Jira

Required tools:

* search Jira issues
* get Jira issue
* create Jira task
* update Jira task

The application should check for duplicate tasks before creating a new task.

Every external task must retain a reference to:

* meeting
* decision
* action item
* evidence

---

# 12. MCP

MCP is used as an integration/tool interface.

The MCP layer should expose controlled tools for external systems.

Initial example:

search_jira()

get_jira_issue()

create_jira_task()

update_jira_task()

External actions must be explicitly authorized.

The application must maintain its own approval state and audit logs.

---

# 13. Phase 7: Execution Tracking

Track:

Meeting

↓

Decision

↓

Action Item

↓

External Task

↓

Progress

↓

Completion

The dashboard should show:

* number of meetings
* number of decisions
* confirmed decisions
* unresolved decisions
* conflicts
* action items
* completed tasks
* overdue tasks
* high-risk decisions

Users should be able to trace an external task back to the original meeting and evidence.

---

# 14. Database Entities

Initial entities:

User

Project

Meeting

TranscriptSegment

Decision

ActionItem

Document

VerificationResult

Task

Integration

ExecutionLog

Relationships:

Project → Meetings

Project → Documents

Meeting → TranscriptSegments

Meeting → Decisions

Meeting → ActionItems

Decision → VerificationResult

ActionItem → Task

Task → ExecutionLog

---

# 15. Backend Structure

Use a modular monolith.

backend/

app/

main.py

api/

meetings.py

projects.py

documents.py

decisions.py

tasks.py

auth.py

services/

meeting_service.py

llm_service.py

rag_service.py

verification_service.py

routing_service.py

task_service.py

agents/

decision_agent.py

evidence_agent.py

critic_agent.py

judge_agent.py

models/

meeting.py

decision.py

task.py

document.py

db/

database.py

integrations/

jira.py

mcp.py

tests/

---

# 16. Frontend Pages

Dashboard

Projects

Project Detail

Meeting Detail

Knowledge Base

Decisions

Tasks

Verification Review

Settings

Important UI components:

MeetingCard

DecisionCard

ActionItem

EvidencePanel

VerificationBadge

ApprovalDialog

TaskCard

---

# 17. API Design

Initial APIs:

POST /projects

GET /projects

GET /projects/{id}

POST /projects/{id}/meetings

GET /meetings/{id}

POST /meetings/{id}/analyze

GET /meetings/{id}/decisions

GET /meetings/{id}/actions

PATCH /decisions/{id}

PATCH /actions/{id}

POST /projects/{id}/documents

POST /projects/{id}/search

POST /decisions/{id}/verify

POST /decisions/{id}/approve

POST /tasks/{id}/execute

GET /projects/{id}/dashboard

Actual endpoint names may be adjusted to fit implementation conventions.

---

# 18. AI Output Requirements

AI outputs must use structured JSON.

All important outputs must be validated before entering the database.

The system must not trust arbitrary LLM output.

Required safeguards:

* schema validation
* retry for malformed output
* source references
* explicit uncertainty
* no fabricated owners
* no fabricated deadlines
* no fabricated evidence
* human approval before external side effects

---

# 19. Evaluation

The research component compares:

A. Single LLM

B. Single LLM + Vector RAG

C. Single LLM + Hybrid RAG

D. Multi-Agent RAG

E. Cost-Aware Multi-Agent RAG

Metrics:

* decision accuracy
* evidence correctness
* contradiction precision
* contradiction recall
* hallucination rate
* retrieval Recall@K
* retrieval Precision@K
* token usage
* estimated cost
* latency

The primary research question is:

"Can cost-aware routing achieve comparable or better decision verification quality than always using multi-agent reasoning while substantially reducing token usage, cost, and latency?"

---

# 20. Development Order

Do not implement everything simultaneously.

Required order:

Phase 1:

Meeting transcript → structured meeting analysis

Phase 2:

Project documents → knowledge base

Phase 3:

Knowledge base → RAG → evidence

Phase 4:

Evidence → multi-agent verification

Phase 5:

Difficulty → routing → cost optimization

Phase 6:

Verified action → human approval → Jira

Phase 7:

Task tracking → dashboard → evaluation

Each phase must produce a working feature before the next phase begins.

---

# 21. MVP Definition

The minimum successful product is:

1. User creates a project.
2. User uploads a transcript.
3. AI generates a summary.
4. AI extracts decisions.
5. AI extracts action items.
6. User can edit them.
7. User uploads project documents.
8. System retrieves relevant evidence.
9. System identifies potential decision conflicts.
10. User sees the evidence.

Everything after this is an extension of the MVP.

---

# 22. Final Demonstration

Use one realistic synthetic project.

Example:

Payment Platform.

Meeting:

Payment Architecture Review.

Meeting proposes:

"Move payment validation into Gateway."

Knowledge base contains:

ADR-17:

"Payment validation remains in Payment Service."

System:

1. Extracts proposal.
2. Retrieves ADR-17.
3. Detects possible contradiction.
4. Difficulty analyzer identifies the decision as high impact.
5. Routes it to multi-agent verification.
6. Agents analyze evidence.
7. Judge produces a contradiction warning.
8. Human reviews it.
9. Human approves an investigation task.
10. Jira task is created.
11. Dashboard tracks the task.
12. Evaluation dashboard records token cost and latency.

This demonstrates the entire product in one scenario.

---

# 23. Non-Goals

The first version will NOT implement:

* live meeting bots
* real-time transcription
* autonomous production deployments
* autonomous code changes
* unrestricted AI tool execution
* Kubernetes
* microservices
* complex distributed queues
* dozens of integrations
* training a large language model
* custom foundation models

These can be mentioned as future work.

---

# 24. Definition of Success

The project is successful if it demonstrates:

1. Reliable meeting understanding.
2. Project-specific retrieval.
3. Evidence-grounded decision verification.
4. Measurable benefit from multi-agent reasoning.
5. Reduced cost through adaptive routing.
6. Human-controlled external task execution.
7. Complete traceability from meeting → decision → evidence → task.
8. Quantitative evaluation of accuracy, cost, and latency.

---

# Milestone 1 Prototype

Run the frontend:

```bash
npm install
npm run dev
```

Open `http://localhost:5173/`. The prototype includes a sample Payment Architecture Review, dashboard metrics, decision and action-item extraction, transcript traceability, risks, open questions, and a new-meeting composer.

The browser includes a deterministic local analysis fallback so the first milestone works immediately. The server-backed path uses Ollama, so the model runs locally and no transcript is sent to a hosted AI provider.

Install Ollama, then pull the default model:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3.2:1b
```

In a second terminal, install the project environment and start the API:

```bash
cp .env.example .env
python3 -m pip install --user --break-system-packages -r backend/requirements.txt
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

Or run `bash setup-local.sh` to automate the model pull and dependency installation.

The API contract is isolated in `POST /api/meetings/analyze`. `GET /health` and `GET /api/ollama/status` report whether Ollama is reachable and which model is configured. Set `OLLAMA_MODEL` in `.env` to use another installed model. If Ollama is unavailable or returns invalid JSON, the API falls back to the deterministic analyzer and marks the response as `analysis_source: "fallback"`.

## Phase 2 and 3 Local Knowledge

Start PostgreSQL and Qdrant:

```bash
docker compose up -d postgres qdrant
cp .env.example .env
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

The Projects view now supports creating the default knowledge project, uploading PDF/TXT/Markdown/DOCX files, extracting and chunking text into PostgreSQL, project-isolated keyword search, and decision verification with source chunks. The API routes are `POST /api/projects/{id}/documents`, `POST /api/projects/{id}/search`, and `POST /api/projects/{id}/verify`.

Qdrant is provisioned in Docker as the next vector-storage boundary; the current search implementation is deterministic keyword retrieval so the project remains usable before embeddings are added.
