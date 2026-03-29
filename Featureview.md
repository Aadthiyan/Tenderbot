Here is the complete competitive analysis + unique feature breakdown of TenderBot Global. [query]

🏪 What Already Exists in the Market
Competitor	Focus	Price	Key Weakness
GovWin IQ (Deltek)	US Federal + Canada only	$15K–$30K/yr enterprise	US-centric, no autonomous agents, database not live-scraped 
​
BidPrime	US Federal/State/Local	$149–$499/mo	Only US portals, no AI scoring, no form fills 
​
Tendium	Public sector discovery	Contact sales	EU/Nordic focused, no multi-portal automation, no deep scrape 
​
Oppex	200-country aggregator	€50/mo	Static database (pre-aggregated, not live-scraped), dated UI 
​
GovDash	US Federal RFP writing	Contact sales	Only SAM.gov, writing tool not discovery agent 
​
Monity.ai	SAM.gov alerts only	Freemium	Single portal, no AI scoring, no cross-portal discovery 
​
AutoRFP.ai	RFP response writing	$899/mo	Response tool, not discovery; no live web agents 
​
SAM Copilot (MS)	SAM.gov only	Unknown	Microsoft ecosystem lock-in, single portal, no browser agent 
​
Key gap: Every competitor either covers only 1–2 portals, is a static database (not live-scraped), charges $10K+/yr for enterprise, or is a writing tool — not an autonomous discovery + enrichment agent.

🌟 TenderBot Global — Unique Feature Breakdown
Feature 1: Live Multi-Portal Browser Automation (No Competitor Has This)
Every competitor uses pre-aggregated static databases updated daily/weekly. TenderBot uses TinyFish to navigate live portals in real-time — the moment a tender is published, TenderBot sees it. [query]

text
Competitors: Scrape once → store → show
TenderBot:   Live browser → extract → score → show (real-time)
No manual data pipeline, no stale listings, no missed opportunities. [query]

Feature 2: 6-Portal Parallel Discovery (Unique Cross-Portal Coverage)
No single tool covers SAM.gov + TED EU + UNGM + Find-a-Tender + AusTender + CanadaBuys simultaneously in one workflow. TenderBot is the first to give a SMB a single inbox for the $13T global government contract market.

text
GovWin IQ     → US + Canada only
BidPrime      → US only
Tendium       → EU/Nordic only
TenderBot     → US + EU + UN + UK + AU + CA simultaneously ✅
Feature 3: AI Relevance Scoring (0–100) with Reasoning
Competitors either have no scoring or use basic keyword matching. TenderBot uses Fireworks.ai LLM to reason about tender fit — understanding sector overlap, budget compatibility, eligibility nuance, and contract type. [query]
​

json
{
  "score": 87,
  "match_reasons": ["cloud infrastructure = core sector", "value within budget"],
  "disqualifiers": ["requires ISO 27001 — not listed in profile"],
  "action": "apply_now"
}
This tells users why a tender matches — not just that it does. [query]

Feature 4: TinyFish Deep Scrape — Full RFP Intelligence
For high-score tenders, TinyFish goes back into the portal and extracts the complete RFP document details: eligibility requirements, certifications needed, evaluation weightings, submission deadlines, contact emails, pre-bid meeting dates.

text
Competitors: Show you the tender listing
TenderBot:   Reads the full RFP for you → tells you if you qualify
No competitor does this autonomously for every high-score tender.

Feature 5: Multimodal Alerts (Slack + Email + Voice)
Competitors send basic email notifications. TenderBot sends: [query]

🔔 Slack alerts (Composio) with tender card + deadline countdown

📧 Email digest with top 5 matches formatted as table

🎙️ ElevenLabs voice briefing — a daily 60-sec audio summary played on your dashboard

"3 new tenders today. Top pick: DoD Cloud contract, $2.4M, 87/100 score, 12 days left."

This multimodal output is unique to TenderBot in this market. [query]

Feature 6: Freemium SaaS vs. Enterprise Lock-in
Every serious competitor (GovWin, Deltek, Bloomberg Gov) costs $10K–$30K/yr — unreachable for SMBs. TenderBot's model:
​

text
Free     → 3 portals, 10 tenders/mo, email only
Pro      → $149/mo — all 6 portals, unlimited tenders, Slack + voice
Agency   → $499/mo — multi-client dashboard, white-label, API access
Target customer: 100M+ SMBs globally that are completely priced out of GovWin.

🆚 TenderBot vs. Market — Full Comparison
Feature	GovWin IQ	BidPrime	Tendium	TenderBot
Feature	GovWin IQ	BidPrime	Tendium	TenderBot
Live browser scraping	❌ Static DB	❌ Static DB	❌ Static DB	✅ TinyFish live
Portals covered	US+Canada	US only	EU only	6 global portals
AI relevance scoring	⚠️ Basic	❌	⚠️ Keyword	✅ LLM 0–100
Full RFP deep scrape	❌	❌	❌	✅ TinyFish
Voice briefings	❌	❌	❌	✅ ElevenLabs
Slack alerts	❌	❌	⚠️ Email	✅ Composio
SMB pricing	❌ $15K+/yr	⚠️ $149/mo US only	❌ Enterprise	✅ $149/mo global
Agent monitoring	❌	❌	❌	✅ AgentOps
💡 The One-Line Differentiation
"Every competitor is a database. TenderBot is an autonomous agent — it goes out into the live web, reads government portals like a human expert, and brings back only the opportunities you can actually win."

This is defensible because TinyFish browser automation is the core moat — any competitor trying to replicate it would need to rebuild on a web agent stack from scratch. [query] Ready to start Day 1 build?

# TenderBot Global – Final Feature Set

This document captures the **final hackathon feature set** for TenderBot Global, organized to clearly show what the product does, how it uses TinyFish, and how it creates business value.

---

## 1. Multi‑Portal Tender Discovery (TinyFish‑Powered)

### 1.1 Global Government Portal Coverage

**What it does:**  
TenderBot continuously monitors multiple major public procurement portals across regions, using autonomous web agents.

**Included portals (v1 target):**
- **USA** – SAM.gov (federal opportunities)
- **European Union** – TED (Tenders Electronic Daily)
- **United Nations** – UNGM / UN procurement portals
- **United Kingdom** – Find‑a‑Tender
- **Australia** – AusTender
- **Canada** – CanadaBuys

**Key behaviors:**
- Opens each portal’s **search interface** using TinyFish.
- Applies filters for:
  - Open / active tenders.
  - Date range (e.g., last 30 days).
  - User‑defined sector keywords.
- Handles **real‑world web complexity**:
  - Cookie banners and consent dialogs.
  - Search forms and filter panels.
  - Pagination across multiple result pages.
- Extracts a **normalized set** of fields per tender:
  - Title, agency/buyer, country/region.
  - Deadline date and published date.
  - Estimated value/budget (if available).
  - Category or code (NAICS, CPV, etc.).
  - Short description or abstract.
  - URL to the full tender description.

**Why it matters:**
- Eliminates **manual portal‑hopping** and copy‑pasting.
- Ensures users see global tenders, not just one country.
- Fully satisfies the hackathon requirement to use TinyFish for **live, multi‑step web workflows**.

---

## 2. Unified Tender Catalog & Data Layer

### 2.1 Normalized Tender Storage

**What it does:**  
Stores all tenders from all portals in a single, consistent data model.

**Details:**
- A **canonical tender schema** captures:
  - Core metadata (title, agency, country, deadline, value, URL).
  - Category codes (NAICS/CPV).
  - Source portal identifier.
  - Derived fields:
    - `days_until_deadline`
    - `status` (active / expired / applied / cancelled)
- Deduplication:
  - `tender_id` is generated from key fields (e.g., hash of title + agency + deadline) to ensure the same tender is not stored twice.
- Indexing and filtering:
  - Supports fast filtering by score, deadline window, country, and status.

**Why it matters:**
- Enables cross‑portal comparison and ranking.
- Provides a robust foundation for scoring, eligibility, and search.

---

## 3. Company Profile & Targeting

### 3.1 Rich Company Profile

**What it does:**  
Captures a structured, procurement‑oriented profile for each user company.

**Profile fields include:**
- Company basics:
  - Name, website.
  - Headquarters country.
- Target focus:
  - Sectors/industries (e.g., Cloud, Cybersecurity, AI).
  - Keywords describing offerings.
  - Target countries / regions.
  - Preferred contract value range.
- Capability attributes:
  - Annual turnover / revenue range.
  - Staff headcount.
  - Years in business.
  - Existing certifications (ISO 9001, ISO 27001, SOC2, etc.).
  - Prior government contract experience (brief notes).
- Operational settings:
  - Selected portals to monitor.
  - Notification preferences (Slack, email).
  - Tender language preferences (where applicable).

**Why it matters:**
- This profile is the **anchor** for all matching, scoring, and eligibility logic.
- Allows TenderBot to act as a **personalized procurement analyst** instead of a generic search engine.

---

## 4. AI‑Driven Relevance Scoring

### 4.1 Tender Match Score (0–100) with Explanations

**What it does:**  
Rates how well each tender matches the company’s capabilities and goals, using LLM reasoning.

**Key aspects:**
- Each tender is evaluated against the company profile, considering:
  - Sector alignment.
  - Keyword overlap.
  - Value range vs budget.
  - Geographic match (company vs tender region).
  - Contract type and complexity.
- Output per tender includes:
  - `relevance_score` (0–100).
  - `match_reasons` – why the score is high/low.
  - `disqualifiers` – explicit reasons to avoid (wrong geography, too big/small, misaligned sector).
  - `action` recommendation:
    - `apply_now`
    - `watch`
    - `skip`

**Why it matters:**
- Reduces cognitive load: users don’t need to open every tender.
- Turns a **long unranked list** into a prioritized, explainable shortlist.

---

## 5. Deep RFP Enrichment (High‑Value Tenders)

### 5.1 Full Tender Detail Extraction

**What it does:**  
For high‑score tenders, TenderBot uses TinyFish to open the detailed tender/RFP pages and extract deeper information.

**Deep‑scraped elements:**
- Detailed description and objectives.
- Complete list of **eligibility requirements**.
- Required **registrations and certifications**.
- Evaluation criteria and weightings (e.g., technical vs price).
- Submission format and mandatory documents.
- Contact details and Q&A channels.
- Pre‑bid briefing or site‑visit information (if present).
- Any visible amendment or addendum notes.

**Why it matters:**
- Users get a **clear, structured snapshot** without manually reading dozens of pages.
- Provides the raw material for eligibility checks and form‑fill guidance.

---

## 6. Eligibility Pre‑Qualification Engine

### 6.1 Eligibility Score & Checklist

**What it does:**  
Judges, ahead of time, whether the company qualifies for a tender and explains why.

**Outputs for each enriched tender:**
- `eligibility_score` (0–100) – how well the company fits requirements.
- `eligibility_checklist` – per requirement:
  - Requirement text.
  - Status: pass / fail / unknown.
  - Gap (if failing).
- `eligibility_action_plan` – short, prioritized list of steps to become eligible in the future (e.g., “Register in SAM.gov”, “Obtain ISO 27001”, “Increase documented experience in X domain”).

**Why it matters:**
- Prevents teams from wasting days on bids they cannot legally win.
- Offers a **path to readiness**, turning lost opportunities into a roadmap.

---

## 7. Competitor Intelligence & Win Probability

### 7.1 Past Awards & Patterns

**What it does:**  
Analyzes public award histories to give context on who typically wins similar contracts.

**Key elements:**
- Gathers award data from public sources for:
  - Same agency / buyer.
  - Similar category / sector.
  - Comparable contract size.
- Summarizes:
  - Frequent winners (prime contractors/consultancies).
  - Average award values.
  - SMB win frequency vs large primes.
- LLM‑based synthesis produces:
  - `top_competitors` – list of frequent winners.
  - `avg_award_value` and distribution hints.
  - `smb_win_rate` for this category.
  - `our_win_probability` estimate for the current company.
  - `winning_strategy` summary.

**Why it matters:**
- Gives capture managers a realistic view of **competition and odds**.
- Helps decide where to invest bidding effort.

---

## 8. Subcontractor Opportunity Radar

### 8.1 Sub‑Bids and Partnership Opportunities

**What it does:**  
Finds opportunities not directly listed as main tenders, but as **subcontracts or supplier calls**.

**Sources include (conceptually):**
- Prime contractor supplier portals.
- Sub‑award or subcontracting sections of public portals.
- Public outreach posts by large vendors.

**Features:**
- Extracts sub‑opportunities with:
  - Prime contractor name.
  - Short opportunity summary.
  - Type of work sought.
  - Requirements and timelines.
  - Link to the application or contact pathway.
- Scores each sub‑opportunity against the company profile.
- Presents a dedicated **Sub‑Opportunities** view in the dashboard.

**Why it matters:**
- Opens up **indirect routes to government work**, useful especially for smaller companies who may prefer to be subcontractors to big primes.

---

## 9. Amendment & Cancellation Tracking

### 9.1 Continuous Monitoring of Watched Tenders

**What it does:**  
Keeps track of changes made to tenders that the user cares about.

**Core behaviors:**
- Periodically re‑visits the tender’s official page.
- Uses an LLM to compare current content with the last stored snapshot.
- Detects changes such as:
  - Deadline extensions or date shifts.
  - New documents or attachments.
  - Added or modified requirements.
  - Cancellations or suspensions.
- Logs change events into an `amendment_history` timeline.

**Why it matters:**
- Prevents missed updates that could invalidate or dramatically change a bid.
- Strengthens the “real‑time, live web” angle for judges.

---

## 10. Auto Form‑Fill Assistant

### 10.1 Assisted Application Form Completion

**What it does:**  
Uses TinyFish to automatically fill out as much of the application form as possible, without submitting.

**Key behaviors:**
- Navigates from tender detail to its application/registration form.
- Identifies common fields (company name, registration numbers, tax IDs, address, contacts, certifications, revenue, etc.).
- Fills these inputs with company profile data wherever a semantic match is found.
- Leaves complex narrative fields (e.g., technical proposal) for humans.
- Reports:
  - Fields successfully filled.
  - Fields still required.
  - Overall completion percentage.

**Why it matters:**
- Cuts down tedious data entry.
- Acts as a strong **demo moment** showing a real, multi‑step, form‑interacting web workflow.

---

## 11. Dashboard & UX Features

### 11.1 Main Dashboard (Tender Overview)

**What it shows:**
- List of top tenders, sorted by:
  - Relevance score.
  - Deadline urgency.
- Each tender card displays:
  - Title, agency, country flag.
  - Relevance badge (e.g., 92/100, `Apply now`).
  - Deadline countdown (e.g., “12 days left”).
  - High‑level tags (e.g., “Cloud”, “Cybersecurity”).

### 11.2 Tender Detail View

**Sections:**
- Core metadata (title, agency, value, portal, URL).
- Relevance summary (score + reasons + disqualifiers).
- Eligibility module (score + checklist + action plan).
- Competitor intel (top competitors, average award, win probability).
- Amendment timeline (changes with timestamps and summaries).
- Auto‑fill status (e.g., “23/27 fields pre‑filled”).
- Actions:
  - Watch / unwatch.
  - Open on official portal.
  - Trigger auto‑fill.

### 11.3 Sub‑Opportunities Tab

**Features:**
- List of subcontracting chances with:
  - Prime contractor, synopsis, relevance score, deadline.
  - Direct link to prime contractor portal.

### 11.4 Alerts Center

**Features:**
- Central list of triggered alerts:
  - New high‑score tenders.
  - Deadlines approaching.
  - Amendments / cancellations.
  - New sub‑opportunities.
- Clear icons and labels for each alert type.

**Why UX matters:**
- Judges can understand the product in seconds.
- Users can operate the system without training.

---

## 12. Notifications & Voice Briefing

### 12.1 Slack / Email Alerts

**Alert types:**
- **New high‑score tender** – when a tender crosses a relevance threshold.
- **Deadline warning** – when a tender is within, say, 48 hours of closing.
- **Amendment alert** – when material changes are detected.
- **Cancellation alert** – when a watched tender is cancelled.
- **New subcontractor opportunity** – when relevant sub‑bids are found.

**Alert contents:**
- Tender title and agency.
- Country, value, and deadline.
- Relevance and/or eligibility scores.
- Direct link to tender detail view in TenderBot.

### 12.2 Daily Voice Briefing

**What it provides:**
- A short (≈60 seconds) synthesized audio update that says:
  - How many new relevant tenders were found.
  - Which tender is the “top pick” today and why (score, value, deadline, eligibility).
  - Any major amendments or cancellations.
- Accessible from:
  - The dashboard (play button).
  - Optionally, link in Slack/email.

**Why it matters:**
- Adds a **memorable, differentiated touch** that demonstrates integration breadth and user‑centric design.

---

## 13. Reliability, Health & Observability

### 13.1 System Health Indicators

**Exposed data:**
- Per‑portal status:
  - Success rate over last N runs.
  - Average latency.
  - Error types (timeouts, captchas, layout changes).
- Overall system status:
  - Scrape scheduler functioning.
  - Scoring and alerts running successfully.

### 13.2 Agent Run Monitoring

**Tracked for each agent run:**
- Portal name or agent type (search, deep scrape, eligibility, etc.).
- Start/end timestamps.
- Number of tenders or records processed.
- Any errors and their context.

**Why it matters:**
- Proves to judges that this is not a fragile script, but an **observable agentic system** that can be operated and improved like a real product.

---

## 14. Meta Features (Hackathon‑Specific)

### 14.1 Public Demo & Build‑in‑Public Assets

**Included:**
- 2–3 minute raw demo video showing:
  - Live TinyFish portal navigation.
  - Dashboard with real multi‑portal data.
  - Eligibility and competitor blocks.
  - Auto‑fill demonstration.
- Public X post with:
  - Clear one‑line value prop.
  - Short explanation of impact (e.g., “found $X in opportunities in 90 seconds”).
  - Tag to the TinyFish account and hackathon hashtag.

**Why it matters:**
- Directly addresses the **Market Signal & Public Proof** judging criterion.

---

This feature set defines the **final scope** of TenderBot Global for the TinyFish hackathon: a production‑style, autonomous web agent product that discovers, filters, enriches, and operationalizes global government tenders for real companies.
