# TenderBot Global – End‑to‑End Workflow

This document explains, step by step, how TenderBot Global works from a user’s perspective and from the system’s perspective. It shows how data flows through TinyFish agents, the backend, LLMs, the database, alerts, and the UI.

---

## 1. User Onboarding & Profile Setup

### 1.1 Create Account / Start Session
The user lands on the TenderBot Global web app and starts as a new company.

**Steps:**
1. Open the onboarding screen.
2. Enter company profile details:
   - Company name
   - Sectors (e.g., Cloud, AI, Consulting)
   - Keywords (e.g., “cloud infrastructure”, “data platform”)
   - Target countries (US, EU, UK, AU, CA, etc.)
   - Typical deal size / budget range
3. Enter procurement‑relevant attributes:
   - Annual turnover
   - Staff headcount
   - Years in business
   - Certifications (ISO, SOC2, etc.)
   - Past government contracts (if any)
4. Optionally connect notification channels:
   - Slack webhook URL
   - Alert email
5. Optionally store portal credentials (for portals that need login):
   - SAM.gov
   - Other regional portals, where applicable

**Result:**  
A complete **user profile** is stored in the database. This profile becomes the reference for matching tenders, checking eligibility, and generating alerts.

---

## 2. Daily Multi‑Portal Discovery

### 2.1 Scheduled Scrape Trigger
A scheduler in the backend triggers a “daily discovery job” (and can also be started manually from the UI).

**Steps:**
1. Scheduler selects all active users.
2. For each user, it starts a scrape orchestration workflow using the saved profile.

**Result:**  
The system begins a new multi‑portal discovery run for that user.

---

### 2.2 TinyFish Agents Search Global Portals

For a single user, the orchestrator launches several TinyFish agents **in parallel**, one per portal:

- SAM.gov (USA)
- TED EU (European Union)
- UNGM / UN procurement
- Find‑a‑Tender (UK)
- AusTender (Australia)
- CanadaBuys (Canada)
- Plus optionally: prime contractor portals for subcontracting

**Per‑portal workflow:**

1. Agent opens the portal’s search page URL.
2. It applies filters based on the user profile:
   - Keywords
   - Status = open / active
   - Date range (e.g., last 30 days)
3. It handles UI complexity:
   - Cookie consent banners
   - Search forms and filters
   - Pagination (multiple pages of results)
4. For each tender result, it extracts structured fields such as:
   - Tender title
   - Issuing agency / buyer
   - Country / region
   - Deadline and published date
   - Estimated value / budget (if visible)
   - Category (NAICS, CPV, etc.)
   - Short description snippet
   - URL to full tender page

**Result:**  
Each portal returns a JSON array of tenders to the backend; the orchestrator gathers all results from all portals into a raw tender list.

---

## 3. Normalization & Storage

### 3.1 Normalizing Portal Data

The backend transforms raw portal‑specific fields into a **common tender schema**.

**Steps:**
1. Map portal‑specific keys into common fields:
   - e.g., `closeDate`, `deadline`, `closing_date` → `deadline`
2. Normalize values:
   - Convert dates into a standard ISO format.
   - Convert currency values to a consistent numeric field.
3. Compute helper fields:
   - `days_until_deadline`
   - `tender_id` (hash of title + agency + deadline)
4. Deduplicate:
   - If a tender with the same `tender_id` already exists, update instead of inserting.

**Result:**  
All tenders are saved in a unified `tenders` collection with consistent fields.

---

## 4. Relevance Scoring (Company–Tender Match)

### 4.1 LLM‑Based Relevance Assessment

Each normalized tender is evaluated against the user’s profile using a large language model.

**Steps:**
1. For each tender, construct a prompt that includes:
   - Company sectors, keywords, budget range, target countries.
   - Tender title, description, country, estimated value, category.
2. Ask the LLM to:
   - Score the tender from **0–100** for relevance.
   - List reasons for the score (matched sectors, keywords, budget fit, geography).
   - List any disqualifiers (wrong sector, too small/large budget, wrong region).
   - Suggest an action: `apply_now`, `watch`, or `skip`.
3. Save the returned data to each tender record:
   - `relevance_score`
   - `match_reasons`
   - `disqualifiers`
   - `action`

**Result:**  
Every tender now includes a numerical relevance score and qualitative explanation.

---

## 5. Deep RFP Enrichment

### 5.1 High‑Priority Tender Selection
The system identifies “high‑priority” tenders, typically:
- `relevance_score ≥ some threshold` (e.g., 75)
- Deadline sufficiently in the future (not already expiring today)

### 5.2 Deep Tender Details via TinyFish

For each high‑priority tender:

1. A **deep‑scrape agent** opens the full tender detail page using the tender’s URL.
2. It:
   - Follows “view full tender” / “details” / “documents” links.
   - Handles new windows or modal dialogs.
   - Locates and follows “download documents” or “view RFP” buttons.
3. It extracts rich details such as:
   - Eligibility requirements (exact textual criteria).
   - Required certifications and registrations.
   - Evaluation criteria and scoring weights.
   - Submission instructions (what to submit, how, where).
   - Contact person / email.
   - Pre‑bid meetings or Q&A sessions.
4. It returns this as structured data which is attached to the tender record.

**Result:**  
High‑priority tenders now have detailed RFP‑level insight, not just listing‑page snippets.

---

## 6. Eligibility Pre‑Qualification

### 6.1 Checking Company Fit Against Requirements

Using the enriched RFP details and the user’s profile:

1. The system prepares a prompt containing:
   - Detailed eligibility requirements from the tender.
   - Company attributes: turnover, years in business, certifications, locations, past contracts.
2. The LLM is asked to:
   - Assess each requirement as **pass / fail / unknown** for this company.
   - Compute an overall **eligibility score** (0–100).
   - Generate a brief **action plan** if the company is not fully qualified (e.g., “Obtain ISO 27001”, “Register on SAM.gov”).
3. This output is stored in fields like:
   - `eligibility_score`
   - `eligibility_checklist` (per‑criterion status)
   - `eligibility_action_plan`

**Result:**  
For each important tender, the system can show exactly how well the company qualifies and what is missing.

---

## 7. Competitor Intelligence & Win Probability

### 7.1 Collecting Award History

For selected tenders (or categories):

1. Agents query public award data sources (e.g., award pages, FPDS‑like systems, EU award forms).  
2. They extract:
   - Past winners (company names).
   - Awarded amounts.
   - Dates and contract types.
   - Repeated patterns (same agency, same sector).

### 7.2 LLM Analysis

With the award history and company profile:

1. The LLM is asked to:
   - Identify top competitors.
   - Summarize typical award sizes.
   - Estimate the **probability that an SMB like this company could win** this type of contract.
   - Describe patterns: “large primes dominate above a certain value”, “SMBs often win when local presence is required”.
2. Output is stored as:
   - `top_competitors`
   - `avg_award_value`
   - `smb_win_rate`
   - `our_win_probability`
   - `winning_strategy` summary.

**Result:**  
The tender detail view can show a realistic, data‑driven win‑probability estimate and competitor context.

---

## 8. Subcontractor Opportunity Radar

### 8.1 Discovering Sub‑Opportunities

In parallel with main tenders, specialized agents:

1. Visit prime contractor supplier / opportunity portals and relevant listings.  
2. Look for sub‑bids and partnership calls related to the same keywords and sectors.  
3. Extract:
   - Prime contractor name.
   - Project summary.
   - Requirements and deadlines.
   - How to apply or express interest.

### 8.2 Scoring and Display

1. Sub‑opportunities are normalized into a separate structure and scored against the company profile.  
2. They appear in a dedicated **“Sub‑Opportunities”** tab in the dashboard.

**Result:**  
Users see both **prime contracts** and **subcontracting options** that match their abilities.

---

## 9. Amendment & Cancellation Tracking

### 9.1 Monitoring Active Tenders

For all **active, watched** tenders:

1. A scheduled job periodically (e.g., every few hours) re‑visits each tender page with a TinyFish agent.  
2. The agent reads the current page and compares it (via an LLM) to a previous snapshot of the tender’s content.

### 9.2 Detecting Changes

The agent categorizes differences, for example:

- Deadline extensions or date changes.
- New documents or clarifications uploaded.
- Scope changes or modified requirements.
- Cancellation notices.

For each change, a structured record is added to the tender’s `amendment_history`, and specific flags are updated:

- `change_type`
- `changes_summary`
- `new_deadline`
- `is_cancelled`

**Result:**  
The system maintains a history of important changes and knows when a tender’s status or requirements have shifted.

---

## 10. Auto Form‑Fill Assistant

### 10.1 Pre‑Filling Application Forms

When a user presses **“Auto‑Fill Application”** on a given tender:

1. A TinyFish agent is instructed to:
   - Navigate to the tender’s application / registration page.
   - Identify common fields (company name, registration number, tax ID, contact details, address, certifications, turnover).
   - Fill in what it can using the company profile.
   - Avoid submitting the form.
2. The agent returns:
   - A list of fields successfully filled.
   - A list of fields that require manual input (e.g., custom technical proposal).
   - An estimated completion percentage.

**Result:**  
The tender detail view shows how much of the form is auto‑completed and what the user still needs to do manually.

---

## 11. Dashboard Experience

### 11.1 Main Dashboard

The React dashboard uses backend APIs to show:

- Top tenders sorted by **relevance score** and **deadline urgency**.
- For each tender:
  - Title, agency, country flag.
  - Score badge (e.g., 92/100).
  - Deadline countdown (e.g., “12 days left”).
  - Quick tags for `apply_now` / `watch`.
  - Short summary.

### 11.2 Tender Detail View

Clicking a tender shows:

- Full description and metadata.
- Relevance score + reasons + disqualifiers.
- Eligibility badge:
  - e.g., “Eligibility: 80% (8/10 criteria met)”.
- Eligibility checklist section (criterion → pass/fail).
- Competitor insights: top competitors, average award value, estimated win probability.
- Amendment timeline: list of detected changes with timestamps.
- Buttons:
  - “Auto‑Fill Application”
  - “Watch Tender”
  - “Open on Portal”

### 11.3 Sub‑Opportunities Tab

- List of subcontractor chances with:
  - Prime contractor.
  - Opportunity summary.
  - Relevance score.
  - Link to prime’s portal.

### 11.4 Alerts Center

- Feed of recent alerts:
  - New tenders.
  - Approaching deadlines.
  - Amendments / cancellations.
  - New sub‑opportunities.

---

## 12. Alerts & Voice Briefing

### 12.1 Slack / Email Alerts

When certain conditions are met (new high‑score tender, deadline within 48 hours, amendment, cancellation):

1. The backend formats a short, clear message summarizing:
   - Tender title, agency, country.
   - Value, deadline, relevance score.
   - Change or reason for alert.
2. The message is sent to the user’s chosen channel (Slack, email).

**Result:**  
The user is notified promptly of critical events without constantly checking the dashboard.

---

### 12.2 Daily Voice Briefing

Once per day:

1. The system selects key information:
   - Number of new tenders since yesterday.
   - Top 1–3 opportunities with scores, values, and deadlines.
   - Any important amendments or cancellations.
2. It builds a short script and sends it to the TTS service.
3. An audio file (e.g., MP3) is generated and linked in the dashboard (or delivered via link in Slack/email).

**Result:**  
The user can quickly listen to a concise spoken summary of their opportunity landscape.

---

## 13. Observability & Health

### 13.1 Agent Monitoring

Every TinyFish agent run is wrapped with monitoring:

- Start and end times.
- Portal name.
- Outcome (success, partial, failure).
- Number of tenders returned.
- Errors encountered.

These metrics are visible in a monitoring dashboard and also inform the `/health` endpoint.

### 13.2 Health Endpoint & Status View

The backend exposes a health summary, for example:

- SAM.gov: ✅ 90% success (last 24h)
- TED EU: ⚠️ intermittent timeouts
- UNGM: ✅ stable
- Overall system: ✅ operational

**Result:**  
You can show judges that your autonomous agent is not just “working once”, but is observed and managed like a production system.

---

## 14. Demo Flow (How Everything Comes Together)

A typical demo will show the workflow like this:

1. Configure a company profile live.  
2. Trigger or show a recent multi‑portal scrape.  
3. Show dashboard with multiple tenders and scores.  
4. Open a high‑score tender detail:
   - Eligibility checklist.
   - Win probability.
   - Amendment history.
5. Hit “Auto‑Fill Application” and show pre‑filled fields.  
6. Show a Slack alert and, optionally, play the daily voice briefing.  
7. Mention monitoring: reference health status and agent metrics.

This path touches **every part of the end‑to‑end workflow** and demonstrates clearly how TenderBot Global uses TinyFish to do real, high‑value work on the live web.

