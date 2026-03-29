--- 
TITLE: TenderBot Global - Detailed Sprint Plan Task Breakdown - Day-by-Day Development, Integration, Testing & Delivery Guide
---

# 1. Sprint Overview & Prioritization Strategy

## 1.1 Strategic Approach

**Objective:**  
Establish the complete project foundation, align with hackathon judging criteria, and create a roadmap for maximum impact.

**Main Task:**  
Define project scope, success criteria, and risk mitigation strategy.

**sub-Tasks:**
1. Review TinyFish hackathon theme and judging criteria (technical maturity 50%, business viability 30%, market signal 20%).
2. Confirm TenderBot Global aligns with "real-world application powered by TinyFish Web Agent API" that solves multi-step web workflows.
3. Document core value proposition: autonomous agent monitoring 6+ global government portals, scoring tenders, pre-qualifying eligibility, tracking amendments, finding sub-opportunities, and auto-filling forms.
4. Create feature prioritization matrix: P0 Must Have (multi-portal scrape, scoring, eligibility), P1 Should Have (competitor intel, amendments), P2 Nice to Have (subcontractor radar).
5. Define demo success criteria: live TinyFish navigation, 15+ scored tenders, eligibility checklist, amendment alert, form-fill demo.
6. Identify high-risk areas: TinyFish portal failures, LLM scoring inconsistency, multi-portal parallel execution.
7. Create mitigation strategies: portal fallbacks, scoring validation, retry logic, AgentOps monitoring.

**Deliverables:**
- Project scope document with P0-P2 features.
- Demo storyboard (2-3 min video flow).
- Risk matrix with mitigations.

**Completion Criteria:**
- Clear understanding of what wins this hackathon.
- No scope creep risk from unclear priorities.
- Demo flow can be explained in 30 seconds.

**Success Metrics:**
- All P0 features prioritized first.
- Demo flow fits in 2-3 minutes.
- Risk matrix covers 90% of potential blockers.

---

## 1.2 Success Metrics for Hackathon

**Objective:**  
Define measurable outcomes that guarantee strong judging performance across all criteria.

**Main Task:**  
Create success criteria matrix aligned with judging weights.

**sub-Tasks:**
1. Technical Maturity (50%): TinyFish agents scrape 6 portals, handle pagination/pop-ups/sessions, score 100+ tenders, deep-scrape 10 high-value RFPs.
2. Business Viability (30%): $13T global TAM, $149/mo SaaS pricing, clear ROI ($10K+/mo saved), SMB-focused positioning.
3. Market Signal (20%): 2-3 min raw demo video, X post with 100+ views, build-in-public thread, professional GitHub repo.
4. TinyFish Integration: 8+ TinyFish agents (6 portals, deep RFP, eligibility, competitor intel, form-fill, amendment tracker).
5. Accelerator Partners: TinyFish (core), Fireworks.ai, MongoDB, Composio, ElevenLabs, AgentOps, Vercel.
6. Demo Readiness: Live browser navigation, real tender data, eligibility pass/fail, win probability, auto-fill demo.

**Deliverables:**
- Judging criteria alignment matrix.
- Demo checklist with pass/fail criteria.

**Completion Criteria:**
- Every feature maps to a judging criterion.
- Demo checklist has 15+ testable items.

**Success Metrics:**
- 90%+ of demo checklist items complete.
- All P0 features demo-ready.
- X post live with hackathon hashtags.

---

# 2. Phase 1: Foundation - Core Infrastructure

**Objective:**  
Establish project infrastructure, setup all external services, and prepare development environment for rapid iteration.

## 2.1 Project Initialization & Structure

**Main Task:**  
Create production-ready project structure with all dependencies and configuration.

**sub-Tasks:**
1. Initialize Git repository with .gitignore, README, and license.
2. Create project folder structure: `backend/`, `agents/`, `parsers/`, `db/`, `notifications/`, `frontend/`.
3. Install Python 3.10+ virtual environment.
4. Create `requirements.txt` with all dependencies: tinyfish, fastapi, pymongo, fireworks-ai, composio-openai, elevenlabs, agentops, apscheduler.
5. Setup environment variables template (.env.example) for all API keys.
6. Create FastAPI project skeleton with basic health endpoint.
7. Initialize MongoDB Atlas free cluster, create database `tenderbot`.
8. Create initial README with project overview, setup instructions, and sprint plan link.

**Deliverables:**
- Complete project repo with structure.
- Working FastAPI server on `localhost:8000`.
- MongoDB cluster ready.

**Completion Criteria:**
- `pip install -r requirements.txt` succeeds.
- `uvicorn main:app --reload` starts without errors.
- MongoDB connection test succeeds.

**Success Metrics:**
- Zero dependency conflicts.
- Server starts in <10 seconds.
- `/health` endpoint returns 200 OK.

## 2.2 External Service Setup & Authentication

**Main Task:**  
Configure and test all external API accounts and authentication.

**sub-Tasks:**
1. Create TinyFish account, generate API key, test basic agent call.
2. Create Fireworks.ai account, generate API key, test Llama 3.1 completion.
3. Create MongoDB Atlas cluster, create database user, test PyMongo connection.
4. Create Composio account, connect Slack workspace, test SLACK_SEND_MESSAGE action.
5. Create ElevenLabs account, test text-to-speech with sample script.
6. Create AgentOps account, generate API key, test session tracking.
7. Create Vercel account, connect GitHub repo.
8. Create Railway account, connect GitHub repo for backend.
9. Store all API keys in `.env` and test environment variable loading.

**Deliverables:**
- All 8 external services configured and tested.
- `.env.example` with all required keys documented.
- Service health check function returning status.

**Completion Criteria:**
- Every service returns expected response.
- No hard-coded secrets anywhere.
- Health check shows all services "healthy".

**Success Metrics:**
- 100% service uptime in test run.
- API key management secure.
- Health check response <2 seconds.

## 2.3 Database Schema Design & Initial Models

**Main Task:**  
Design and implement MongoDB schemas for all data types.

**sub-Tasks:**
1. Design `users` collection: company profile, preferences, portal credentials (encrypted), notification settings.
2. Design `tenders` collection: core fields, scoring data, eligibility, competitor intel, amendment history, status.
3. Design `portal_logs` collection: per-portal run results, success/failure, metrics.
4. Design `alerts` collection: sent notifications, delivery status, user acknowledgments.
5. Create PyMongo connection utility with database selection.
6. Implement schema validation using Pydantic models.
7. Create initial indexes on `relevance_score`, `deadline`, `status`, `country`.
8. Write seed script to create test user and sample tenders.

**Deliverables:**
- Complete schema definitions in `db/models.py`.
- Connection utility and validation working.
- Indexes created, seed data loaded.

**Completion Criteria:**
- All collections created with indexes.
- Seed data validates against schemas.
- Queries use indexes (explain plan confirms).

**Success Metrics:**
- Schema covers 100% of planned features.
- Seed data realistic for demo.
- Queries return in <100ms.

---

# 3. Phase 2: TinyFish Portal Agents

**Objective:**  
Implement 6 autonomous TinyFish agents that scrape real government portals and return structured tender data.

## 3.1 SAM.gov Search Agent

**Main Task:**  
Create TinyFish agent that navigates SAM.gov, searches for tenders, and extracts structured data.

**sub-Tasks:**
1. Identify SAM.gov search URL pattern and required filters.
2. Document UI elements: cookie banner, search form, filter panels, pagination.
3. Write natural language TinyFish goal describing navigation and extraction.
4. Specify target fields: title, agency, NAICS, deadline, value, solicitation number, description.
5. Implement agent wrapper function with retry logic.
6. Test with sample keywords, verify JSON output structure.
7. Add AgentOps session tracking.

**Deliverables:**
- `agents/sam_gov.py` with working agent.
- Sample output JSON for 10 tenders.

**Completion Criteria:**
- Agent handles cookie banner.
- Extracts 10+ tenders from 2+ pages.
- JSON output matches tender schema.

**Success Metrics:**
- 90% success rate over 10 runs.
- Complete data for all key fields.
- Runs in <60 seconds.

## 3.2 TED EU Search Agent

**Main Task:**  
Create TinyFish agent for TED EU portal with multilingual support.

**sub-Tasks:**
1. Identify TED EU search URL and filters (scope=ALL, status=open).
2. Document cookie consent, language selection, pagination.
3. Write goal prompt handling multilingual content.
4. Extract: title, contracting authority, country, CPV code, deadline, value.
5. Implement agent with English‑only extraction preference.
6. Test with EU‑focused keywords.
7. Add error handling for language detection.

**Deliverables:**
- `agents/ted_eu.py` working agent.
- Sample EU tenders with country codes.

**Completion Criteria:**
- Handles cookie consent.
- Extracts tenders from 2 pages.
- Country and CPV codes accurate.

**Success Metrics:**
- 85% success rate (multilingual harder).
- Accurate country extraction.

## 3.3 UNGM Search Agent

**Main Task:**  
Implement UNGM agent for global UN procurement opportunities.

**sub-Tasks:**
1. Study UNGM notice board and search functionality.
2. Document filter navigation for open notices.
3. Write goal for reference number, title, organization, deadline extraction.
4. Handle dynamic filter panels.
5. Test with global keywords.
6. Add special handling for UN organization codes.

**Deliverables:**
- `agents/ungm.py` agent.
- UN tenders with organization codes.

**Completion Criteria:**
- Navigates dynamic filters.
- Extracts reference numbers correctly.

**Success Metrics:**
- Consistent UN organization extraction.

## 3.4 Find‑a‑Tender (UK) Agent

**Main Task:**  
Build agent for UK public contracts portal.

**sub-Tasks:**
1. Identify search URL and UK‑specific fields.
2. Document pagination and buyer filtering.
3. Extract title, buyer, closing date, value, CPV codes.
4. Handle UK date formats.
5. Test with UK‑focused keywords.

**Deliverables:**
- `agents/find_a_tender.py`.

**Completion Criteria:**
- Extracts UK buyer names and CPV codes.

**Success Metrics:**
- 90% field completeness.

## 3.5 AusTender & CanadaBuys Agents

**Main Task:**  
Implement remaining two portal agents.

**sub-Tasks:**
1. AusTender: ATM ID, title, agency, close date, value.
2. CanadaBuys: solicitation number, title, department, closing date.
3. Create parallel execution test.

**Deliverables:**
- Both agents working.
- Parallel scrape returns 50+ tenders.

**Completion Criteria:**
- All 6 agents return data.

**Success Metrics:**
- Parallel execution reduces total time by 80%.

## 3.6 Multi‑Portal Orchestration Layer

**Main Task:**  
Create FastAPI endpoint that coordinates all 6 agents running in parallel.

**sub-Tasks:**
1. Create `/scrape` POST endpoint accepting user ID.
2. Fetch user profile from MongoDB.
3. Launch `asyncio.gather([sam_gov_agent(), ted_eu_agent(), ...])`.
4. Normalize and deduplicate results.
5. Store in MongoDB.
6. Return summary stats.

**Deliverables:**
- `/scrape` endpoint working.
- One‑click multi‑portal scrape.

**Completion Criteria:**
- Single API call scrapes all portals.
- Data stored correctly.

**Success Metrics:**
- Complete scrape in <3 minutes.
- No data loss between agents.

---

# 4. Phase 3: Relevance Scoring & Enrichment

**Objective:**  
Transform raw tender data into actionable insights using AI.

## 4.1 Fireworks.ai Relevance Scoring

**Main Task:**  
Implement LLM‑based scoring (0–100) for every tender.

**sub-Tasks:**
1. Create Fireworks.ai client with API key.
2. Design scoring prompt template including company profile + tender data.
3. Implement JSON output parsing.
4. Add fields: score, match_reasons, disqualifiers, action.
5. Batch score all tenders from scrape.
6. Store results in MongoDB.

**Deliverables:**
- Scoring service.
- All tenders have scores.

**Completion Criteria:**
- Scores range 0–100 meaningfully.
- Reasons explain score.

**Success Metrics:**
- 100% tenders scored.
- Top 10% have scores >80.

## 4.2 Deep RFP Enrichment Agent

**Main Task:**  
TinyFish agent extracts full RFP details from high‑score tenders.

**sub-Tasks:**
1. Select tenders with score ≥75.
2. Create deep‑scrape goal: navigate to detail page, extract eligibility, certifications, evaluation criteria.
3. Handle document download buttons.
4. Store enriched data.

**Deliverables:**
- 10+ enriched tenders.

**Completion Criteria:**
- Extracts eligibility requirements.

**Success Metrics:**
- 80% success rate on deep scrapes.

## 4.3 Eligibility Pre‑Qualification

**Main Task:**  
LLM compares RFP requirements against company profile.

**sub-Tasks:**
1. Extract eligibility criteria from deep scrape.
2. Create eligibility prompt comparing profile vs requirements.
3. Output per‑criterion pass/fail + action plan.
4. Store eligibility_score and checklist.

**Deliverables:**
- Eligibility results on top tenders.

**Completion Criteria:**
- Shows pass/fail per requirement.

**Success Metrics:**
- Action plan actionable.

---

# 5. Phase 4: Advanced Intelligence Features

**Objective:**  
Add gap features that differentiate TenderBot from existing tools.

## 5.1 Competitor Bid Intelligence

**Main Task:**  
Analyze past awards to estimate win probability.

**sub-Tasks:**
1. Identify award data sources (FPDS, TED awards).
2. Create TinyFish goal for award history.
3. LLM analyzes winners, values, patterns.
4. Output top competitors, smb_win_rate, our_probability.

**Deliverables:**
- Win probability on top tenders.

**Completion Criteria:**
- Named competitors + probability.

**Success Metrics:**
- Realistic probability estimates.

## 5.2 Amendment & Cancellation Tracker

**Main Task:**  
Detect changes to watched tenders.

**sub-Tasks:**
1. Store page snapshot per tender.
2. Periodic re‑scrape with comparison goal.
3. Detect deadline changes, new docs, cancellations.
4. Log to amendment_history.

**Deliverables:**
- Amendment detection working.

**Completion Criteria:**
- Detects simulated deadline change.

**Success Metrics:**
- Low false positives.

## 5.3 Subcontractor Radar

**Main Task:**  
Find sub‑bidding opportunities.

**sub-Tasks:**
1. Target prime contractor portals.
2. Extract sub‑opportunities.
3. Score and display separately.

**Deliverables:**
- Sub‑opportunities tab.

**Completion Criteria:**
- 3+ sub‑opportunities found.

**Success Metrics:**
- Relevant to company profile.

## 5.4 Auto Form‑Fill Assistant

**Main Task:**  
Pre‑fill application forms.

**sub-Tasks:**
1. Navigate to application page.
2. Map profile fields to form inputs.
3. Fill without submitting.
4. Report completion %.

**Deliverables:**
- Form‑fill demo.

**Completion Criteria:**
- Fills 70%+ fields.

**Success Metrics:**
- Works on SAM.gov form.

---

# 6. Phase 5: Frontend & User Experience

**Objective:**  
Build React dashboard showing all intelligence.

## 6.1 Dashboard Overview

**Main Task:**  
Top tenders by score + deadline.

**sub-Tasks:**
1. Fetch tenders from `/tenders?score_min=60`.
2. Tender cards with score, deadline, country.
3. Filters and sorting.
4. Urgency badges.

**Deliverables:**
- Working dashboard.

**Completion Criteria:**
- Shows 20+ tenders.

**Success Metrics:**
- Loads <2s.

## 6.2 Tender Detail View

**Main Task:**  
Rich detail page with all intelligence.

**sub-Tasks:**
1. Fetch `/tender/{id}`.
2. Sections for eligibility, competitor, amendments.
3. Auto‑fill button.

**Deliverables:**
- Detail view with all sections.

**Completion Criteria:**
- All intelligence visible.

**Success Metrics:**
- Intuitive layout.

---

# 7. Phase 6: Notifications & Voice

**Objective:**  
Multi‑channel alerts and daily briefings.

## 7.1 Composio Alerts

**Main Task:**  
Slack/email for deadlines, amendments.

**sub-Tasks:**
1. Connect Slack via Composio.
2. Format alert messages.
3. Trigger logic for each type.

**Deliverables:**
- Slack alerts working.

**Completion Criteria:**
- 3 alert types fire.

**Success Metrics:**
- Delivered in <5s.

## 7.2 ElevenLabs Voice Briefing

**Main Task:**  
Daily audio summary.

**sub-Tasks:**
1. Generate script from top tenders.
2. Convert to MP3.
3. Serve via dashboard.

**Deliverables:**
- Audio player.

**Completion Criteria:**
- 60s coherent audio.

**Success Metrics:**
- Natural sounding.

---

# 8. Phase 7: Monitoring & Health

**Objective:**  
Prove production readiness.

## 8.1 AgentOps Integration

**Main Task:**  
Track all agent runs.

**sub-Tasks:**
1. Wrap TinyFish calls.
2. Track sessions, errors, costs.
3. Display dashboard.

**Deliverables:**
- AgentOps dashboard.

**Completion Criteria:**
- Per‑portal metrics.

**Success Metrics:**
- 90%+ success rates.

## 8.2 Health Endpoint

**Main Task:**  
System status overview.

**sub-Tasks:**
1. Per‑portal uptime.
2. Job scheduler status.
3. LLM costs.

**Deliverables:**
- `/health` page.

**Completion Criteria:**
- All services green.

**Success Metrics:**
- <500ms response.

---

# 9. Phase 8: Demo & Submission

**Objective:**  
Package everything for maximum impact.

## 9.1 Demo Video Recording

**Main Task:**  
2‑3 min raw demo.

**sub-Tasks:**
1. Rehearse full flow.
2. Record using OBS.
3. No slides, raw screen.

**Deliverables:**
- 2 min video.

**Completion Criteria:**
- Shows all P0 features.

**Success Metrics:**
- One‑take recording.

## 9.2 X Post & Submission

**Main Task:**  
Public launch.

**sub-Tasks:**
1. Write X caption.
2. Post video.
3. Submit HackerEarth.

**Deliverables:**
- Live X post.

**Completion Criteria:**
- Submission complete.

**Success Metrics:**
- 100+ views.

---

This is your **RetailGen‑style detailed sprint plan** for TenderBot Global. [code_file:111]
