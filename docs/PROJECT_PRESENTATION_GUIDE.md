# Meeting2Action

## Project Presentation and Demonstration Guide

Meeting2Action is an agentic meeting-to-execution platform. It converts an unstructured meeting transcript into traceable project knowledge, checks proposed decisions against existing evidence, and turns approved follow-up actions into accountable work.

The central idea is:

**Meeting -> Understanding -> Evidence -> Verification -> Approval -> Execution -> Tracking**

This is a college major project with both a product goal and a research goal. The product should help teams avoid losing decisions after meetings. The research component studies whether expensive multi-agent reasoning is worth using for every decision, or whether the system can route only difficult decisions to deeper verification.

---

## 1. The Problem

Meeting information is usually stored as free-form speech, notes, chat messages, and documents. This creates several practical problems:

- Decisions can be forgotten or confused with proposals.
- Action items may not have a clear owner or deadline.
- Previous architectural decisions may not be checked before a new decision is made.
- Contradictions can be missed because project knowledge is distributed across documents and old meetings.
- Tasks created in external systems may lose their connection to the original meeting and evidence.
- Fully autonomous AI actions are risky because a model may misunderstand a commitment or invent missing information.

Meeting2Action addresses this by making every important output traceable to its transcript source and every external action subject to human approval.

---

## 2. What the System Does

A user can:

1. Create or select a project.
2. Paste or upload a meeting transcript.
3. Ask the system to analyze it.
4. Review the summary, topics, decisions, risks, questions, and action items.
5. See the exact transcript segment supporting each extracted item.
6. Assign owners, deadlines, priority, and status to action items.
7. Upload project documents such as ADRs, specifications, TXT, Markdown, PDF, or DOCX files.
8. Search project-isolated knowledge.
9. Verify a decision against project evidence.
10. Review contradictions and uncertainty.
11. Approve a follow-up task before an external system is changed.
12. Schedule or create the approved task through an integration.
13. Track the task back to the meeting and evidence that produced it.

The system must preserve unknown information as unknown. It must not invent an owner, deadline, source, or evidence reference.

---

## 3. How It Differs from Existing Products

Meeting2Action is not intended to compete with every feature of products such as Otter, Fireflies, Fathom, Notion AI, Jira, or Microsoft Teams. It connects capabilities that are often separated across those products.

| Product category | Typical strength | Gap Meeting2Action investigates |
|---|---|---|
| Transcription tools | Recording, transcription, summaries, and meeting notes | They usually stop at notes or summaries rather than checking decisions against project evidence. |
| Meeting assistants | Action-item extraction and reminders | They may not provide project-specific contradiction analysis with source references. |
| Knowledge tools | Document storage and search | They are not usually responsible for understanding a new meeting and turning it into controlled execution. |
| Project-management tools | Task assignment, status, due dates, and reporting | They generally do not determine whether a task or decision is supported by the organization knowledge base. |
| Workflow automation tools | Moving data between systems | They can automate actions but do not necessarily provide evidence-grounded reasoning and uncertainty. |
| General AI chatbots | Flexible question answering | They may hallucinate sources, owners, deadlines, or confident conclusions without a traceability contract. |

### Main differentiators

1. **Traceability**: each decision and action item keeps a citation to the transcript segment that produced it.
2. **Project-aware verification**: proposed decisions are checked against documents and previous project context.
3. **Contradiction awareness**: disagreement is surfaced as a review signal, not automatically treated as proof that a proposal is wrong. Documents may be outdated or superseded.
4. **Human-controlled execution**: external task creation or calendar changes require an explicit user action or approval state.
5. **Cost-aware intelligence**: simple decisions can use inexpensive retrieval or a single model call, while ambiguous or high-impact decisions can be routed to multiple agents.
6. **Measurable research**: the project compares quality, evidence correctness, token usage, cost, and latency across reasoning strategies.

The project should present these as design goals and research questions, not as claims that the current prototype already outperforms commercial products.

---

## 4. How Everything Works Together

### End-to-end flow

```text
Transcript upload or paste
        |
        v
Meeting analyzer
        |
        +--> Summary, topics, decisions, actions, risks, questions
        |
        v
Structured validation
        |
        v
PostgreSQL meeting and action records
        |
        +--> Transcript citations for traceability
        |
        +--> Project knowledge retrieval
        |        |
        |        +--> Keyword search initially
        |        +--> Embedding/vector search later
        |        +--> Hybrid retrieval eventually
        |
        v
Decision verification
        |
        +--> SUPPORTED
        +--> CONTRADICTED
        +--> INSUFFICIENT_EVIDENCE
        +--> AMBIGUOUS
        |
        v
Difficulty and cost router
        |
        +--> Simple RAG
        +--> Enhanced verification
        +--> Multi-agent verification
        |
        v
Human review and approval
        |
        v
Task/calendar/Jira integration through controlled tools
        |
        v
Execution log and dashboard tracking
```

### Current technical architecture

- **Frontend**: React, TypeScript, and Vite.
- **Backend**: FastAPI modular monolith.
- **Relational database**: PostgreSQL stores projects, documents, meetings, action items, and integration records.
- **Vector database boundary**: Qdrant is provisioned for future vector retrieval. Current project search is deterministic keyword retrieval.
- **LLM**: Ollama is used through a backend service abstraction. A deterministic local fallback keeps the prototype usable when Ollama is unavailable.
- **Document extraction**: TXT, Markdown, PDF, and DOCX are supported in the knowledge-base flow.
- **External integration boundary**: the current calendar adapter is a mock MCP-compatible boundary. It demonstrates the approval and execution shape before real Google OAuth is added.

### Why PostgreSQL and Qdrant are separate

PostgreSQL is the system of record for structured business data: projects, meetings, tasks, users, approvals, and audit records.

Qdrant is intended for semantic retrieval of document chunks. It answers questions such as: “Which project evidence is related to payment validation?”

The separation lets the system keep reliable transactional data in PostgreSQL while using a specialized store for similarity search.

---

## 5. Current Prototype Status

### Working now

- React/Vite workspace interface.
- New meeting composer with transcript paste and TXT/Markdown upload.
- Ollama analysis with deterministic fallback.
- Structured extraction of summaries, decisions, action items, risks, and open questions.
- Transcript citations for extracted items.
- PostgreSQL persistence for meetings and action items.
- Task assignment and status updates.
- Task completion and priority display.
- Project document upload for PDF, TXT, Markdown, and DOCX.
- Project-isolated keyword search.
- Basic decision verification with evidence results.
- Mock calendar scheduling endpoint with durable event ids.
- Searchable meetings view and open-task notification summary.
- Docker Compose services for PostgreSQL and Qdrant.

### Important prototype limitations

- Authentication and multi-user permissions are not implemented yet.
- Calendar scheduling is a mock provider, not real Google Calendar OAuth.
- Jira task creation is not implemented yet.
- Qdrant is provisioned but semantic embeddings are not wired into retrieval yet.
- Meeting data and project relationships need further normalization and backend dashboard APIs.
- Multi-agent verification and cost-aware routing are planned research features.
- Automated unit, API, and browser tests still need to be added.

Being explicit about these boundaries strengthens the presentation. A good major project shows a working vertical slice and a defensible extension plan.

---

## 6. Features We Will Add Next

### Phase A: Make the core product robust

- Add proper project and meeting relationships.
- Add backend dashboard aggregation.
- Add validation and error handling for malformed analysis results.
- Add audit logs for assignment, approval, and external execution.
- Add API and frontend tests.

### Phase B: Improve retrieval

- Generate embeddings for document chunks.
- Store vectors in Qdrant with project IDs as payload filters.
- Retrieve related documents and previous meetings.
- Combine keyword and vector retrieval into hybrid search.
- Return source references with every evidence-backed answer.

### Phase C: Add verification agents

Use four constrained agents:

1. **Decision Agent**: identifies what was actually proposed, confirmed, rejected, or left unresolved.
2. **Evidence Agent**: retrieves and summarizes relevant project evidence.
3. **Technical Critic**: identifies implications, risks, missing information, and implementation concerns.
4. **Judge**: combines the outputs into a structured verdict with cited evidence.

Agents must never invent sources. The judge must downgrade confidence when evidence is weak or conflicting.

### Phase D: Add cost-aware routing

A deterministic difficulty analyzer can score:

- ambiguity
- evidence conflict
- retrieval quality
- technical impact
- missing information

Example routing:

- Score 0-3: single-model or simple RAG analysis.
- Score 4-6: enhanced evidence verification.
- Score 7-10: multi-agent verification.

The thresholds must be evaluated experimentally rather than assumed to be optimal.

### Phase E: Add controlled integrations

- Real Google Calendar OAuth or a Google Calendar MCP server.
- Jira search, duplicate detection, task creation, and task updates.
- Human approval dialog before external side effects.
- Integration credentials stored outside the database and never exposed to the model.
- Execution logs linking every external task to its meeting, action item, decision, and evidence.

---

## 7. Important Design and Research Questions

These are useful presentation and viva questions.

### Product questions

**Who is the target user?**

Project leads, engineering managers, product teams, and organizations that need decisions and follow-up work to remain traceable.

**What is the minimum successful product?**

A user uploads a transcript, receives structured decisions and actions, edits them, uploads project evidence, and sees whether a decision may conflict with existing knowledge.

**Why is human approval required?**

A transcript can be ambiguous and external actions have real consequences. Human approval limits the blast radius of extraction or reasoning errors.

**What happens when the transcript does not contain an owner or deadline?**

The field remains null or unknown. The system may flag the missing information but must not infer it from weak clues.

**What happens if an old document contradicts a new decision?**

The system reports a possible contradiction and shows the evidence. It does not automatically reject the new decision because the old document may be superseded.

### Technical questions

**Why use a modular monolith?**

The project is still evolving and benefits from simple local development, shared transactions, and fewer operational dependencies. Separate services would add complexity without helping the initial research question.

**Why use PostgreSQL?**

It provides reliable transactions, structured relationships, constraints, and audit-friendly storage for business entities.

**Why use Qdrant?**

Semantic retrieval is different from relational filtering. Qdrant is specialized for vector similarity and can enforce project-level metadata filters.

**How is project isolation enforced?**

Every document chunk and retrieval query carries a project ID. A search must filter by that project ID before ranking results.

**How do you prevent hallucinated evidence?**

Evidence is selected by the retrieval layer and returned with document and chunk references. Structured validation rejects outputs that do not match the expected schema. The model is instructed to express insufficient evidence instead of inventing a source.

**How do you evaluate the system?**

Use a labelled synthetic or manually reviewed dataset and compare decision accuracy, evidence correctness, contradiction precision and recall, hallucination rate, retrieval Recall@K and Precision@K, token usage, estimated cost, and latency.

**What is the research hypothesis?**

Cost-aware routing can achieve similar verification quality to always using multi-agent reasoning while reducing average token usage, cost, and latency.

**What is the main risk?**

The system may extract an incorrect action or overstate a contradiction. The mitigation is source citation, explicit uncertainty, schema validation, human approval, and evaluation against labelled examples.

---

## 8. Presentation Structure

A strong 10-15 minute presentation can follow this order:

1. Problem: important meeting decisions disappear into unstructured transcripts.
2. Existing gap: transcription, knowledge search, and task tools are usually disconnected.
3. Proposed solution: Meeting2Action's traceable pipeline.
4. Architecture: React, FastAPI, PostgreSQL, Qdrant, Ollama, and controlled integrations.
5. Live demo using the Payment Platform example below.
6. Research question: when is multi-agent reasoning worth its cost?
7. Current results and limitations.
8. Future work: semantic retrieval, multi-agent verification, cost-aware routing, and real integrations.
9. Conclusion: convert meeting language into evidence-grounded, human-controlled execution.

### Suggested contribution statement

> Meeting2Action contributes a traceable and cost-aware architecture that connects meeting understanding, project-specific evidence retrieval, decision verification, and controlled task execution. Its research contribution is an evaluation of whether adaptive routing can preserve verification quality while reducing the cost and latency of multi-agent reasoning.

---

## 9. Demo Dataset: Payment Platform

Use this synthetic project because it demonstrates a decision, a contradiction, an action item, evidence, and a controlled execution step.

### Project

**Name:** Payment Platform

**Description:** Payment processing platform for online checkout and recurring billing.

### Knowledge document 1: ADR-17-payment-validation.md

```markdown
# ADR-17: Payment validation ownership

Status: Accepted
Date: 2026-08-12

Payment validation remains in the Payment Service, which is the source of truth for authorization rules, fraud checks, and validation errors.

The Gateway may perform request normalization and authentication, but it must not become the owner of payment validation. Keeping validation in one service prevents inconsistent payment states between the Gateway and Payment Service.

Any proposal to move validation into the Gateway requires a latency benchmark, an error-consistency analysis, and an explicit architecture review.
```

### Knowledge document 2: observability-notes.md

```markdown
# Payment observability notes

The team currently has request tracing at the Gateway and Payment Service boundaries. Validation failure reasons are not yet consistently represented in the shared dashboard.

Before changing validation ownership, the team should compare p95 latency, error rates, retry behavior, and trace completeness for both architectures.
```

### Meeting transcript

```text
Maya: Today's focus is payment architecture for Q3.
Maya: We agreed to keep Payment Service as the source of truth for validation.
Arjun: Decision: moving validation into Gateway is proposed, not approved.
Maya: Action: Arjun will prepare a latency comparison by Friday. Owner: Arjun.
Priya: Action: Priya will document the observability gaps by Thursday. Owner: Priya.
Priya: Open question: do we have enough observability to compare both designs?
Maya: Risk: split validation could create inconsistent payment states.
Arjun: If the benchmark supports the change, we will bring a revised proposal to architecture review.
```

### Expected extracted output

- **Confirmed decision**: Payment Service remains the source of truth for validation.
- **Proposed decision**: Moving validation into Gateway is not yet approved.
- **Action**: Arjun prepares a latency comparison by Friday.
- **Action**: Priya documents observability gaps by Thursday.
- **Open question**: Is observability sufficient for comparing both designs?
- **Risk**: Split validation could create inconsistent payment states.
- **Citations**: each item should point to its source transcript segment.

### Expected verification result

When verifying “Move payment validation into Gateway”, the system should retrieve ADR-17 and return a possible contradiction or insufficient-confidence warning. The explanation should say that current project evidence keeps validation in Payment Service and requires further analysis before changing ownership.

The system should not claim the proposal is permanently wrong. It should explain that the evidence may be superseded after a new architecture review.

---

## 10. Exact Demo Steps

### Start the application

From the repository root:

```bash
docker compose up -d postgres qdrant
npm install
python3 -m pip install --user --break-system-packages -r backend/requirements.txt
```

Start the backend in one terminal:

```bash
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

Start the frontend in another terminal:

```bash
npm run dev
```

Open `http://localhost:5173`.

Ollama is optional because the deterministic fallback works locally. For model-backed analysis:

```bash
ollama serve
ollama pull llama3.2:1b
```

### Run the demo

1. Open **Projects**.
2. Create or use the Payment Platform knowledge project.
3. Upload `ADR-17-payment-validation.md`.
4. Upload `observability-notes.md`.
5. Search for `payment validation ownership`.
6. Show the returned document chunks and match scores.
7. Open **New meeting**.
8. Enter `Payment Architecture Review` as the title.
9. Paste the transcript above.
10. Add attendees: `Maya, Arjun, Priya`.
11. Add a meeting date if desired.
12. Click **Analyze & save**.
13. Show the summary, decisions, action items, risks, open question, and transcript citations.
14. Open **Tasks**.
15. Assign Arjun and Priya to their respective tasks.
16. Change one task to `IN_PROGRESS`.
17. Click **Schedule** to demonstrate the controlled calendar adapter.
18. Return to **Projects**.
19. Verify `Move payment validation into Gateway`.
20. Explain the evidence and possible contradiction.
21. Refresh the browser and show that meeting and task edits persist through PostgreSQL.
22. Finish by explaining how the next version would require explicit approval before creating a real Jira task or Google Calendar event.

### Demo narration

> The transcript is not treated as a task list directly. First, the analyzer extracts structured candidates and attaches citations. Then the project knowledge layer retrieves relevant evidence. The verifier reports whether the proposal is supported, contradicted, ambiguous, or unsupported. Only after a human reviews the result should the system call an external integration. This preserves traceability and keeps the model from making unrestricted side effects.

---

## 11. Example API Checks

Health check:

```bash
curl http://localhost:8000/health
```

List persisted meetings:

```bash
curl http://localhost:8000/api/meetings
```

The interactive API documentation is available at:

```text
http://localhost:8000/docs
```

Build validation:

```bash
npm run build
```

---

## 12. Final Definition of Success

The project is successful when it demonstrates all of the following in a repeatable experiment:

1. Reliable extraction of meeting decisions and actions.
2. A citation for every extracted item.
3. Project-specific retrieval with no cross-project leakage.
4. Evidence-grounded contradiction detection.
5. Human approval before external side effects.
6. A complete trace from meeting to decision to evidence to task.
7. Measured comparison of single-model, RAG, multi-agent, and cost-aware strategies.
8. Reduced cost and latency without unacceptable loss of verification quality.

The strongest final demonstration is not that the AI acts autonomously. It is that the system knows what it knows, shows why it reached a conclusion, identifies uncertainty, and keeps a human in control of consequential execution.
