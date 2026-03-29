# TenderBot Global – Detailed Task Plan

This document defines a **complete, task‑level plan** to build a functional, demo‑ready prototype of **TenderBot Global** for the TinyFish Hackathon. It is structured to maximize:
- Technical maturity (TinyFish as core infra, multi‑step web workflows)
- Business value (clear, global B2B pain and ROI)
- Market signal and presentation (strong demo, X post, narrative)

For every task you will find:
- **Description of the task**
- **Subtasks**
- **Deliverables**
- **Completion Criteria**
- **Success Metrics**

No time estimates are included, so you can adapt this to your own schedule.

---

## 1. Hackathon Setup & Project Framing

### 1.1 Understand Hackathon Rules & Judging Criteria

**Description of the task:**  
Fully internalize constraints and success metrics for the TinyFish Hackathon so every build decision supports winning.

**Subtasks:**
- Re‑read theme: *Build an autonomous web agent using the TinyFish API*.
- Re‑read rules on originality, TinyFish usage, team size, submission format, and X demo requirements.
- Re‑read judging criteria: technical maturity (50%), business viability (30%), market signal & public proof (20%).
- Note any disallowed patterns (no basic RAG, no static scrapers, no UI wrappers over APIs).

**Deliverables:**
- One‑page personal note summarizing: "What judges want" and "What they reject".
- Checklist of non‑negotiables: TinyFish as core infra, live web, demo video on X, business case.

**Completion Criteria:**
- You can articulate the judging criteria and constraints from memory.
- You can explain in 2–3 sentences why TenderBot Global is a strong fit for the theme.

**Success Metrics:**
- All later tasks clearly map to at least one judging criterion.
- No planned feature violates hackathon rules (e.g., purely API‑based or mock‑data‑only).

---

### 1.2 Define Product Scope for MVP

**Description of the task:**  
Decide what must be in the hackathon prototype and what can be considered stretch to avoid over‑scoping.

**Subtasks:**
- List all potential features: multi‑portal discovery, scoring, deep RFP enrichment, eligibility, competitor intel, amendment tracking, subcontractor radar, auto form‑fill, alerts, voice briefing.
- Mark each feature as: *Core for demo*, *High‑impact stretch*, *Optional nice‑to‑have*.
- Freeze a v1 hackathon scope: what absolutely must work in the live demo.
- Align scope with judging: focus on flows that show TinyFish doing multi‑step, complex web work.

**Deliverables:**
- Prioritized feature list labeled: Core / Stretch / Optional.
- Final scope statement (2–3 bullet points) describing what v1 will definitely include.

**Completion Criteria:**
- You have a clear, written understanding of what you are **not** building for this hackathon.

**Success Metrics:**
- No new features are added mid‑build without explicitly revisiting the scope document.

---

## 2. Architecture & Data Design

### 2.1 Confirm System Architecture

**Description of the task:**  
Lock in the high‑level architecture and main components so all implementation stays aligned.

**Subtasks:**
- Review the previously defined architecture (user layer, FastAPI layer, TinyFish agent pool, LLM layer, data layer, notifications, monitoring).
- Map each feature to a component (e.g., amendment tracking → TinyFish agent + cron + Composio + DB field).
- Ensure every critical path passes through TinyFish (to satisfy hackathon requirements).
- Document data flow for the most important user journey: profile → scrape → score → deep scrape → eligibility → dashboard → alerts.

**Deliverables:**
- Architecture section in your project README with a clear diagram (Mermaid text) and bullet‑point explanation.

**Completion Criteria:**
- No ambiguity about where any feature lives (frontend, backend, agent, DB, integration).

**Success Metrics:**
- No major architectural changes are needed once implementation starts.

---

### 2.2 Design Data Models

**Description of the task:**  
Design MongoDB schemas for tenders, users, portal logs, and alerts that support all planned features.

**Subtasks:**
- Enumerate all fields needed for a tender: core fields (title, agency, country, deadline, value, URL) + scoring fields + eligibility fields + competitor intel + amendments + subcontractor flags.
- Define user profile fields to support matching and eligibility: sectors, keywords, budget, certifications, historical contracts, portal credentials, slack/email endpoints.
- Decide how to track portal runs and amendments (separate log collection vs embedded arrays).
- Decide on indexing strategy (e.g., indexes on `relevance_score`, `deadline`, `status`, `country`).

**Deliverables:**
- Written JSON‑like schema for each collection in the .md file.
- Short notes describing required indexes.

**Completion Criteria:**
- Every feature can be implemented using the defined schemas without schema changes.

**Success Metrics:**
- Queries used in dashboard views are simple and do not require heavy aggregation.

---

## 3. Backend Orchestration (FastAPI)

### 3.1 Define API Endpoints

**Description of the task:**  
Specify all backend endpoints the frontend and tools will use, with clear request/response semantics.

**Subtasks:**
- List endpoints such as: `/profile`, `/scrape`, `/tenders`, `/tender/{id}`, `/alerts/config`, `/health`, `/subcontracts`, `/briefing/audio`, `/auto-fill`.
- For each endpoint, define:
  - Purpose.
  - Method (GET/POST).
  - Request body / query parameters.
  - Response structure (key fields, status codes).
- Decide which endpoints are synchronous (immediate response) vs fire‑and‑forget (trigger background jobs).

**Deliverables:**
- API specification section in the .md plan (a mini API contract).

**Completion Criteria:**
- Frontend can be built using only the documented endpoints.

**Success Metrics:**
- No undocumented ad‑hoc endpoints are needed during integration.

---

### 3.2 Implement Orchestration Logic (Conceptually)

**Description of the task:**  
Plan how the backend will coordinate scraping, scoring, deep scraping, eligibility checks, and saving data.

**Subtasks:**
- Define a high‑level flow for `run_full_scrape(profile)`:
  - Fetch user profile from DB.
  - Call the multi‑portal scraping function.
  - Normalize and deduplicate results.
  - Pass normalized tenders into the scoring pipeline.
  - For top tenders, trigger deep RFP scraping and eligibility checks.
  - Save everything into MongoDB.
- Plan how to handle failures from any portal without breaking the whole run.
- Plan how to expose scrape status to `/health` and the UI.

**Deliverables:**
- Written pseudo‑flow for the orchestrator in the .md file.

**Completion Criteria:**
- The orchestrator design explicitly handles partial failures and retries.

**Success Metrics:**
- Full scrape is robust: if one portal fails, results from others still appear in the demo.

---

## 4. TinyFish Agent Design

### 4.1 Portal Search Agents (6 Portals)

**Description of the task:**  
Specify how each TinyFish agent interacts with its portal to fetch active tenders.

**Subtasks:**
- For each portal (SAM.gov, TED EU, UNGM, Find‑a‑Tender, AusTender, CanadaBuys):
  - Identify search URL and main filters needed (status=open, date range, keywords).
  - Identify UI obstacles: cookie banners, login prompts (if any), pagination controls, search forms.
  - Define a natural‑language TinyFish goal that tells the agent exactly what to extract and how.
  - Decide limit per portal (e.g., first 10–20 results, first 2–3 pages).
- Plan a common normalization shape for all returned JSON arrays.

**Deliverables:**
- A table describing, per portal: search URL pattern, filters, obstacles, goal prompt, fields extracted.

**Completion Criteria:**
- For each portal, you know exactly which clicks and fields the TinyFish agent needs to perform.

**Success Metrics:**
- No portal agent requires re‑design once you start testing.

---

### 4.2 Deep RFP Scraper Agent

**Description of the task:**  
Define the TinyFish agent that opens the full tender page, fetches the RFP content and attachments, and structures the details.

**Subtasks:**
- For each portal, identify where the "full details" or "download documents" buttons live.
- Decide what RFP details you must extract for eligibility and competitor analysis: eligibility list, required certifications, evaluation criteria, submission instructions, pre‑bid details, contact info.
- Draft a detailed TinyFish goal that:
  - Navigates from the listing to the full tender view.
  - Handles pop‑ups or new windows.
  - Extracts content in a structured way.
- Describe how this agent is triggered only for high‑score tenders.

**Deliverables:**
- Written goal template for the Deep RFP agent and the list of expected output fields.

**Completion Criteria:**
- The output of this agent is sufficient to feed the eligibility and form‑fill components.

**Success Metrics:**
- In demo, at least one top tender shows rich extracted details beyond what listing pages provide.

---

### 4.3 Eligibility Analysis Agent

**Description of the task:**  
Specify how the system determines whether a company qualifies for a tender using RFP details and the user profile.

**Subtasks:**
- List all relevant company profile fields: turnover, years in business, staff headcount, certifications, countries registered, past government contracts.
- List examples of eligibility criteria that appear in RFPs: minimum turnover, specific ISO standards, geographic requirements, prior experience.
- Design a prompt to compare these two sets of information and produce:
  - Overall eligibility score (0–100).
  - Per‑criterion pass/fail/unknown.
  - A short action plan to close gaps.
- Define how to store this output in the tender document.

**Deliverables:**
- Structured description of the eligibility algorithm and prompt.

**Completion Criteria:**
- Each high‑score tender in the system can display a meaningful eligibility summary.

**Success Metrics:**
- In demo, you can show one tender where the company clearly passes and one where it clearly fails, with understandable explanations.

---

### 4.4 Competitor Intelligence Agent

**Description of the task:**  
Plan how to derive competitor insights and win probability from public award data.

**Subtasks:**
- Identify at least two award sources: FPDS/SAM award search, TED EU award notices.
- Design TinyFish goals to scrape recent awards matching the same agency and category as the current tender.
- Define how to summarize awards: frequent winners, average award value, SMB vs large‑vendor wins, contract size bands.
- Define the LLM analysis prompt for Fireworks.ai to produce a win‑probability estimate and key patterns.
- Decide how this appears in the UI (numeric probability + bullet points).

**Deliverables:**
- Competitor intel plan with example data and expected analysis output.

**Completion Criteria:**
- The analysis can run even if only a small number of past awards are found.

**Success Metrics:**
- In demo, you can show a real tender with a non‑trivial competitor story (e.g., big primes dominate, SMBs win only below a value threshold).

---

### 4.5 Amendment Tracking Agent

**Description of the task:**  
Define how the system detects and reports changes to tenders (extensions, new documents, cancellations).

**Subtasks:**
- Decide how to store a snapshot summary of each tender page (text or structured representation).
- Design TinyFish goal to re‑visit the tender URL and compare current state to the stored snapshot (via LLM comparison).
- Define categories of change: deadline change, new document, scope change, cancellation, clarifications.
- Define what gets logged in the `amendment_history` array and what triggers alerts.

**Deliverables:**
- Specification of snapshot representation and change categories.

**Completion Criteria:**
- Amendment events are fully representable as structured records.

**Success Metrics:**
- In demo, you can simulate an amendment and show the system catching and alerting on it.

---

### 4.6 Subcontractor Radar Agent

**Description of the task:**  
Plan the agent that surfaces subcontracting opportunities from prime contractor portals and related sources.

**Subtasks:**
- Identify at least two sources for sub‑opportunities: prime contractor supplier portals, subcontracting views on SAM.gov, relevant public posts.
- Define TinyFish goals that:
  - Navigate supplier opportunity pages.
  - Extract sub‑opportunity listings (title, prime contractor, scope, deadline, requirements).
- Design how to normalize these into a `sub_opportunity` representation.
- Decide how these will be scored and displayed separately from main tenders.

**Deliverables:**
- Subcontractor opportunity data model and scraping plan.

**Completion Criteria:**
- Sub‑opportunities are stored and queryable like tenders, but flagged as a different type.

**Success Metrics:**
- In demo, you can show at least one real sub‑opportunity card with prime contractor name.

---

### 4.7 Auto Form‑Fill Agent

**Description of the task:**  
Design the logic for automatically filling application forms using company data, without submitting.

**Subtasks:**
- Identify common fields across portals: organization name, registration number, tax ID, address, contact details, certifications, turnover.
- Decide how the agent will map profile fields to form labels and input names using semantics rather than hard‑coded selectors.
- Define TinyFish goal instructions that:
  - Locate relevant fields.
  - Fill them with provided values.
  - Avoid clicking any final "Submit" buttons.
  - Report which fields were filled and which need manual input.
- Decide how completion percentage is calculated.

**Deliverables:**
- Auto‑fill algorithm description and the list of supported field types.

**Completion Criteria:**
- You can describe, step by step, how the agent behaves on any new tender form using only text instructions.

**Success Metrics:**
- In demo, the UI can show a meaningful auto‑fill summary on at least one form.

---

## 5. Data Pipeline & Scoring

### 5.1 Normalization Pipeline

**Description of the task:**  
Define the transformation from raw portal‑specific JSON into the common tender schema.

**Subtasks:**
- For each portal, list the raw fields returned by TinyFish (names, formats).
- Define rules for mapping each raw field to canonical fields (title, agency, country, deadline, value, category).
- Define rules for date parsing, currency normalization, and missing values.
- Decide how to generate `tender_id` for deduplication.

**Deliverables:**
- Normalization rules documented per portal.

**Completion Criteria:**
- After normalization, tenders from all portals can be merged and sorted in a single list.

**Success Metrics:**
- No malformed or missing key fields in the demo dataset.

---

### 5.2 Relevance Scoring Logic

**Description of the task:**  
Plan the scoring algorithm and how Fireworks.ai is used to compute scores.

**Subtasks:**
- Define the conceptual scoring formula (e.g., 40% sector match, 20% keywords, 20% value range, 20% geography), even though Fireworks.ai will learn it through prompts.
- Design the LLM prompt so it sees both the tender data and the company profile.
- Define thresholds for actions: `apply_now`, `watch`, `skip`.
- Decide how to handle uncertain scores (e.g., missing value or unclear category).

**Deliverables:**
- Scoring specification including thresholds and examples of expected behavior.

**Completion Criteria:**
- You can explain why a sample tender should get a high or low score and the prompt supports that.

**Success Metrics:**
- In demo, the top 3 tenders look intuitively like the best matches for the provided profile.

---

## 6. Frontend (React Dashboard)

### 6.1 UX & Screen Design

**Description of the task:**  
Design user flows and screen layouts for all key views.

**Subtasks:**
- Define primary user journeys:
  - First‑time onboarding: create profile, select portals.
  - Returning user: review daily matches and alerts.
  - Deep dive into a single tender.
- Sketch screen layouts (even on paper):
  - Dashboard (cards, filters, score, deadline indicator).
  - Tender detail (sections for eligibility, competitor intel, amendments, auto‑fill status).
  - Sub‑opportunity tab.
  - Alerts center.
- Decide on basic UI components: cards, tables, badges, tabs.

**Deliverables:**
- Low‑fidelity wireframes or textual description of each screen in the .md file.

**Completion Criteria:**
- Every feature from the backend has a clearly designated place in the UI.

**Success Metrics:**
- In demo, navigation between views feels natural and requires minimal explanation.

---

### 6.2 Frontend–Backend Contract Validation

**Description of the task:**  
Ensure the frontend can consume backend responses without confusion.

**Subtasks:**
- For each screen, write down which endpoints it calls and what subset of fields it needs.
- Verify that all needed fields exist in the API specs.
- Adjust API or UI expectations where there are mismatches.

**Deliverables:**
- Per‑screen endpoint mapping document.

**Completion Criteria:**
- No unknowns remain about how the frontend will get its data.

**Success Metrics:**
- During implementation, there are no surprises about missing fields.

---

## 7. Notifications & Voice Briefing

### 7.1 Alert Strategy

**Description of the task:**  
Define when and how alerts are triggered so they are helpful, not noisy.

**Subtasks:**
- Decide alert types:
  - New high‑score tender.
  - Tender approaching deadline (e.g., < 48 hours).
  - Amendment/cancellation.
  - New subcontractor opportunity.
- For each type, define conditions in terms of tender fields and time.
- Design the Slack/email message templates with concise, actionable content.

**Deliverables:**
- Alert matrix (type → trigger → message format).

**Completion Criteria:**
- Every alert has a clear, non‑ambiguous trigger and a single recipient.

**Success Metrics:**
- In demo, each alert shown clearly answers "why did I receive this?".

---

### 7.2 Voice Briefing Content Design

**Description of the task:**  
Plan the script structure for the ElevenLabs daily audio briefing.

**Subtasks:**
- Define the information hierarchy:
  - Number of new tenders.
  - Top tender summary (title, agency, country, value, deadline, eligibility score, win probability).
  - Optional mention of new amendments or cancellations.
- Keep total script length under about 60 seconds.
- Design two example scripts:
  - One for a busy day (many new tenders).
  - One for a quiet day.

**Deliverables:**
- Voice script templates in the .md file.

**Completion Criteria:**
- The script can be generated using only data from MongoDB.

**Success Metrics:**
- In demo, the audio summary feels like a real analyst speaking, not just reading raw data.

---

## 8. Scheduling & Reliability

### 8.1 Job Scheduling Strategy

**Description of the task:**  
Define which background jobs exist and how often they run.

**Subtasks:**
- List cron jobs:
  - Daily full multi‑portal scrape.
  - Periodic amendment checks.
  - Deadline alert checks.
  - Daily voice briefing generation.
- For each job, define:
  - Input data (which users and tenders).
  - Steps it performs.
  - Which components it calls (agents, DB, notifications).

**Deliverables:**
- Job schedule table with job names and responsibilities.

**Completion Criteria:**
- No critical functionality depends on the user manually triggering a job.

**Success Metrics:**
- In demo, you can switch from manual triggering to describing the automated schedule convincingly.

---

### 8.2 Error Handling & Retries

**Description of the task:**  
Plan how to deal with portal failures, rate limits, and LLM issues.

**Subtasks:**
- Decide retry strategy for all TinyFish calls (e.g., up to 3 retries with backoff).
- Define fallback behavior if a portal is temporarily down (mark portal as degraded but continue others).
- Decide how to log and expose recurring errors via `/health` and AgentOps.
- Decide what happens when Fireworks.ai or other integrations fail (temporary skip vs whole job fail).

**Deliverables:**
- Error handling policy describing behavior per failure type.

**Completion Criteria:**
- Every external call in the system has a defined retry and fallback behavior on paper.

**Success Metrics:**
- In demo, if one portal fails live, the system still shows useful results from others and surfaces a clear status message.

---

## 9. Quality Assurance & Testing

### 9.1 Functional Testing Plan

**Description of the task:**  
Define tests that prove each feature works at least once in an end‑to‑end flow.

**Subtasks:**
- Write test scenarios for:
  - Multi‑portal scrape produces tenders.
  - Scoring orders tenders as expected.
  - Deep RFP extraction works for at least one tender.
  - Eligibility analysis produces pass/fail and a clear reason.
  - Competitor analysis produces a win‑probability figure.
  - Amendment tracking detects a simulated change.
  - Subcontractor radar shows at least one opportunity.
  - Auto form‑fill reports high completion percentage.
  - Alerts fire as expected.
- For each scenario, define:
  - Input conditions (profile, portals, sample tender).
  - Expected visible output in the UI or logs.

**Deliverables:**
- Functional test case list in the .md file.

**Completion Criteria:**
- Every core feature has at least one planned test scenario.

**Success Metrics:**
- During manual testing, each scenario is executed and confirmed at least once before recording the demo.

---

### 9.2 Demo Readiness Checklist

**Description of the task:**  
Ensure the prototype is stable and polished enough for a live demo and recording.

**Subtasks:**
- Create a pre‑demo checklist including:
  - All environment variables set (keys, URIs).
  - Backend and frontend running.
  - At least one user profile seeded.
  - At least one successful scrape has been run recently.
  - Alerts verified.
- Run through the entire demo flow once end‑to‑end without recording.
- Note any bugs or awkward transitions and decide whether to fix or work around them.

**Deliverables:**
- A demo checklist document and a list of any known, acceptable limitations.

**Completion Criteria:**
- You can complete the full demo flow without encountering a blocking issue.

**Success Metrics:**
- The recorded demo is completed in one or two takes with no critical failures.

---

## 10. Presentation & Submission

### 10.1 Narrative & Positioning

**Description of the task:**  
Craft the story you will tell to judges, investors, and on X.

**Subtasks:**
- Write a short narrative covering:
  - The size of the problem (global $13T government procurement market, SMBs locked out).
  - Why existing tools fail (static databases, single‑country focus, no agents).
  - How TenderBot Global changes the game (autonomous multi‑portal agent, eligibility, amendments, competitor intel, auto form‑fill).
- Align narrative with the judging criteria (tech maturity, business viability, market signal).
- Prepare a 30–45 second spoken intro for the demo video.

**Deliverables:**
- Narrative text and spoken intro script in the .md file.

**Completion Criteria:**
- You can explain TenderBot Global clearly in under one minute without looking at notes.

**Success Metrics:**
- The narrative flows logically during the demo and in the X caption.

---

### 10.2 Demo Recording Plan

**Description of the task:**  
Plan how to record the demo to make the most impact within 2–3 minutes.

**Subtasks:**
- Decide which screens and flows to show and in what order.
- Decide what to say while each part of the UI is visible.
- Decide how to briefly show TinyFish live agent behavior (e.g., SSE logs or video window of the browser).
- Plan a clean ending that reinforces the value proposition.

**Deliverables:**
- Demo storyboard: step‑by‑step list of shots and narration.

**Completion Criteria:**
- The storyboard fits comfortably within 2–3 minutes when rehearsed.

**Success Metrics:**
- The final video hits all major judging points:
  - Multi‑portal TinyFish agents.
  - Scoring + eligibility.
  - Amendment/alert example.
  - Auto form‑fill.

---

### 10.3 X Post & HackerEarth Submission Content

**Description of the task:**  
Prepare all text and links needed for public launch and official submission.

**Subtasks:**
- Draft the X post caption highlighting:
  - Autonomous web agent.
  - Number of portals.
  - Time saved and value found in demo.
  - Powered by TinyFish.
- Prepare short business case text (problem → solution → ROI → business model).
- Prepare technical architecture blurb summarizing stack and components.
- Collect all required links: X post, GitHub repo, live demo URL.

**Deliverables:**
- Final X caption.
- Final HackerEarth submission text prepared in the .md file.

**Completion Criteria:**
- Submission can be done by copy‑pasting prepared content and URLs.

**Success Metrics:**
- No scrambling or last‑minute writing at submission time; everything is ready.

---

## 11. Time Management & Prioritization Guidance

### 11.1 Build Order Strategy

**Description of the task:**  
Decide in what order to tackle tasks to maximize chances of finishing a solid demo.

**Subtasks:**
- Prioritize tasks in this order:
  1. Core multi‑portal scrape + normalization.
  2. Relevance scoring + basic dashboard listing.
  3. Deep RFP + eligibility.
  4. Alerts (at least one type) + simple health checks.
  5. Competitor intel OR auto form‑fill (whichever feels quicker).
  6. Remaining gap features and polish.
- Mark absolute must‑haves vs can‑drop‑if‑time‑runs‑out.

**Deliverables:**
- Ordered list of tasks labeled "must", "should", "could".

**Completion Criteria:**
- You never start a "could" task before finishing all "must" tasks.

**Success Metrics:**
- Even if you run out of time, core flows are solid and demoable.

---

### 11.2 Quality vs Scope Trade‑offs

**Description of the task:**  
Define rules for when to reduce scope to preserve stability and demo quality.

**Subtasks:**
- Decide which optional features can be skipped if integration is taking too long.
- Decide what "good enough" means for each feature (e.g., one portal fully working for competitor intel rather than all).
- Define a personal stop‑rule: past a certain point, no new features, only debugging and polish.

**Deliverables:**
- Written trade‑off rules in the .md file.

**Completion Criteria:**
- You have a clear policy to avoid breaking the demo with last‑minute changes.

**Success Metrics:**
- Final prototype is stable with slightly reduced scope rather than unstable with all features.

---

This task plan is intended to be used as your **execution checklist** during the hackathon. You can tick off each task once its Completion Criteria and Success Metrics are satisfied, ensuring the final TenderBot Global prototype is technically strong, business‑viable, and presentation‑ready.
