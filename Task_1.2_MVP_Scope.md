# Task 1.2 — MVP Scope Definition (Frozen)

> **Rule:** No new features are added mid-build without revisiting THIS document.  
> **Deadline:** March 29, 2026 (13 days from March 16)  
> **Judging weights:** Technical 50% · Business 30% · Market Signal 20%

---

## 1. Full Feature Prioritization

Every potential feature is scored on three axes and assigned a tier:

- **Demo Impact** — How visually/narratively powerful is this in the 2–3 min live demo?
- **Judge Score Value** — How directly does it improve scores on the 3 judging criteria?
- **Build Risk** — How likely is this to break, block, or eat time beyond its value?

---

### 🟢 CORE — Must Work in Live Demo (Non-Negotiable)

These features must be fully functional before Day 10. If any of these is broken on demo day, the submission is weak.

| # | Feature | Why CORE | Judging Criterion |
|---|---|---|---|
| C1 | **Company Profile & Onboarding** | The anchor for all scoring, eligibility, and matching. Without it, the agent has nothing to personalize against. | Technical + Business |
| C2 | **Multi-Portal Discovery — SAM.gov + TED EU + UNGM** (minimum 3 portals live, target 6) | The single biggest TinyFish proof point. Parallel agents on real, API-less portals = irreplaceable TinyFish usage. Must show at least 3 portals working live. | **Technical (50%)** |
| C3 | **Tender Normalization + MongoDB Storage** | Without a unified data layer, nothing else (scoring, dashboard, alerts) can work. Foundation for the entire system. | Technical |
| C4 | **AI Relevance Scoring (0–100, Fireworks.ai)** | Turns a raw list into an intelligent shortlist. The score badge on the dashboard is the most visible "AI moment" for judges. | Technical + Business |
| C5 | **React Dashboard — Tender List View** | Judges must see a polished UI with real data. Cards with score, country flag, agency, deadline countdown. This is what the demo camera points at. | Technical + Market Signal |
| C6 | **Tender Detail View** | Shows depth: relevance reasons, disqualifiers, action label. This is where judges see the intelligence layer, not just a list. | Technical + Business |
| C7 | **Deep RFP Enrichment (TinyFish deep-scrape agent)** | Second TinyFish proof point. Shows the agent going *deeper* into a tender page beyond the listing — multi-step, real-world web navigation. Must work for at least 1 tender in the demo. | **Technical (50%)** |
| C8 | **Eligibility Pre-Qualification (with checklist)** | Most emotionally compelling business feature — "you qualify for 8/10 criteria, missing ISO 27001" is a sentence judges immediately understand as real value. | Technical + **Business (30%)** |
| C9 | **Slack Alert via Composio (at least 1 alert type)** | Proves the system acts autonomously, not just shows data. Even one working Slack alert type (e.g., new high-score tender) satisfies judging. | Technical + Business |
| C10 | **AgentOps Integration** | Proves production-grade observability. Judges should be able to see agent run logs. Simple to add, high credibility return. | **Technical (50%)** |
| C11 | **APScheduler Daily Scrape Job** | Proves autonomy — the system doesn't need a human to press "scrape." Essential for the "this is a real product" narrative. | Technical + Business |
| C12 | **Portal Health Status (/health endpoint + UI)** | Shows judges real-world reliability thinking. ✅ SAM.gov · ⚠️ TED EU timeout. Takes 1 hour to build, adds significant credibility. | Technical |

---

### 🟡 HIGH-IMPACT STRETCH — Build After All CORE Is Stable

These are compelling demo moments but should only be started once C1–C12 all work end-to-end.

| # | Feature | Why STRETCH | When to build |
|---|---|---|---|
| S1 | **Amendment & Cancellation Tracking** | Third TinyFish proof point (re-visit + compare). Great for the demo ("deadline extended from Mar 30 → Apr 15, system caught it"). But requires a snapshot system + LLM diff — non-trivial. | Day 7, after C1–C9 done |
| S2 | **Auto Form-Fill Agent** | Most visually dramatic demo moment — watching TinyFish fill a real government form. Direct Technical score boost. But portal form behavior is unpredictable; high breakage risk. Scope to 1 portal only (SAM.gov). | Day 9, only if S1 stable |
| S3 | **Daily Voice Briefing (ElevenLabs)** | Unique and memorable. "3 tenders today. Top pick: DoD Cloud, $2.4M, 87/100, 12 days left." Differentiates on Market Signal criterion. Low build effort (ElevenLabs SDK + simple script generator). | Day 11, after alerts work |
| S4 | **Find-a-Tender, AusTender, CanadaBuys agents** (portals 4–6) | More portals = stronger Technical score and wider demo narrative. But if SAM.gov + TED EU + UNGM all work reliably, 3 portals is already sufficient. Only add extras if agents for the first 3 are rock-solid. | Day 2, opportunistically |
| S5 | **Email Digest via Composio** | Easy add-on once Slack alert (C9) is working. Might be worth doing since it's Composio already configured. | Day 11, 30-min add-on |

---

### ⚪ OPTIONAL — Nice-to-Have, Drop If Time-Constrained

These are valuable product features but add non-trivial build time for marginal demo/judging gain *within the hackathon timeframe*.

| # | Feature | Why OPTIONAL | Drop Condition |
|---|---|---|---|
| O1 | **Competitor Intelligence & Win Probability** | Real B2B value, but requires a separate TinyFish agent scraping award history (FPDS, TED F03). Complex logic, high prompt engineering. Judges won't miss it if eligibility is strong. | Drop if Day 6 runs over |
| O2 | **Subcontractor Opportunity Radar** | Interesting feature but adds an entirely separate data source, agent type, and UI tab. Low immediate demo impact compared to core flows. | Drop entirely if past Day 8 |
| O3 | **Portal Credential Storage (encrypted)** | Most portals don't need login for the demo. Adds AES-256 encryption complexity for marginal demo benefit. | Drop entirely |
| O4 | **Language Detection + EU Translation** | TED EU tenders are multilingual. Auto-translating to English via Fireworks.ai is clever but non-essential for the demo. | Drop if Day 4 runs over |
| O5 | **Multi-user / team dashboard** | TenderBot is single-user for v1. Multi-user auth is a full product feature, not hackathon scope. | Drop entirely |
| O6 | **White-label / Agency tier** | Pricing model feature, not buildable for hackathon. Mention in business case write-up only. | Drop entirely |

---

## 2. Frozen v1 Hackathon Scope Statement

> This is the **contract with yourself**. If it isn't in these bullet points, it isn't being built for v1.

**TenderBot Global v1 (Hackathon) will definitely include:**

- **Live multi-portal tender discovery via TinyFish**, scraping at minimum SAM.gov + TED EU + UNGM in parallel using `asyncio.gather`, handling real-world UI complexity (cookies, pagination, dynamic filters), and returning normalized tender JSON into MongoDB.

- **AI-powered relevance scoring + eligibility pre-qualification**, where every tender is scored 0–100 by Fireworks.ai against the company profile, and high-score tenders (≥75) are deep-scraped by a second TinyFish agent that extracts RFP eligibility requirements, which are then assessed per-criterion (pass/fail) and shown as a checklist in the tender detail view.

- **A React dashboard (Vercel)** showing the top tenders ranked by score and deadline urgency, a full tender detail view with eligibility summary, a Slack alert via Composio for new high-score tenders, a daily APScheduler scrape job, and an AgentOps-monitored health status view — all connected to a FastAPI backend (Railway) and MongoDB Atlas.

---

## 3. What TenderBot Global v1 Is Explicitly NOT Building

This list is the guard against scope creep. Print it. Refer to it daily.

| ❌ Not building for v1 | Reason |
|---|---|
| Competitor intelligence scraper | High build risk, low marginal demo gain vs eligibility |
| Subcontractor radar | Separate data source, separate agent, separate UI tab — full sprint on its own |
| Auto form-fill agent | Build only if S1 (amendments) is stable AND Day 9 has slack time |
| Multi-user authentication | Product feature, not hackathon scope |
| Portal credential encryption (AES-256) | Portals that need login are out of scope for demo |
| EU tender translation (multilingual) | Nice-to-have, cut if Day 4 runs over |
| White-label / agency pricing tier | Business model narrative only, not buildable |
| Dedicated sub-opportunities UI tab | Out of scope |
| Email digest | Only add if Slack + Voice are both working with time to spare |
| Production CI/CD pipeline | Manual deploy to Railway + Vercel is fine for hackathon |

---

## 4. Demo Day Target State

By **March 28** (Day 12), the live demo must show this exact flow:

```
1. Show the company profile (pre-filled — don't type it live)
2. Click "Run Discovery" → show 3+ TinyFish agents running in parallel
3. Dashboard loads with 15–20 tenders, sorted by score
4. Open the top-scoring tender:
   - Score: 91/100 with 3 match reasons
   - Eligibility: 8/10 criteria met, ❌ missing ISO 27001
   - Action: "apply_now"
5. Briefly mention the deep-scrape agent retrieved this from the full RFP page
6. Show a Slack alert that already fired for this tender
7. Reference the /health page: "SAM.gov ✅, TED EU ✅, UNGM ✅"
8. Optionally: press play on voice briefing audio
```

This 8-step flow hits **every judging criterion** and uses TinyFish in at least **2 distinct, meaningful ways** (portal search agents + deep RFP scraper).

---

## 5. Feature Build Order (Priority Queue)

Strict order — do not start the next row before the current one is working end-to-end:

| Order | Task | Sprint Day |
|:---:|---|:---:|
| 1 | FastAPI base + TinyFish SAM.gov agent (single portal) | Day 1 |
| 2 | All 6 portal agents + parallel scraping | Day 2 |
| 3 | MongoDB schema + normalization + deduplication | Day 3 |
| 4 | Fireworks.ai relevance scoring pipeline | Day 4 |
| 5 | Deep RFP Agent (TinyFish) + eligibility (Fireworks.ai) | Day 5 |
| 6 | React dashboard — tender list + detail view | Day 10 |
| 7 | Composio Slack alert (new high-score tender) | Day 11 |
| 8 | AgentOps integration + /health endpoint | Day 11 |
| 9 | APScheduler daily job | Day 11 |
| — | **CORE COMPLETE. Start stretch below ↓** | — |
| 10 | Amendment tracker (S1) | Day 7 |
| 11 | ElevenLabs voice briefing (S3) | Day 11 |
| 12 | Auto form-fill on SAM.gov only (S2) | Day 9 |
| 13 | Portals 4–6: Find-a-Tender, AusTender, CanadaBuys (S4) | Day 2 |

---

## 6. Stop Rule

> At any point from **Day 11 onward**, if CORE features C1–C12 are all working AND at least one stretch feature (S1, S2, or S3) is done, **stop adding features and focus exclusively on:**
> - Stability testing the full demo flow
> - Seeding good demo data
> - Recording the demo video
> - Writing the X caption and HackerEarth submission text

A slightly smaller but **stable and polished** submission beats a full-featured but flaky one every time.
