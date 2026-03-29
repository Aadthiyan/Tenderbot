# Sprint 1.1 & 1.2 — Strategic Foundation Documents

> **Status:** COMPLETE — all 5 deliverables below.  
> **Deadline:** March 29, 2026 · **Today:** March 16, 2026 · **Days remaining:** 13  
> **Rule:** Refer back to this document before making any scope or priority decision.

---

# DELIVERABLE 1 — Project Scope: P0 / P1 / P2 Feature Matrix

## Priority Definitions

| Priority | Label | Meaning |
|:---:|---|---|
| **P0** | **Must Have** | Demo is broken or unconvincing without this. Build first, never cut. |
| **P1** | **Should Have** | Significantly improves judging score. Build after all P0s are stable. |
| **P2** | **Nice to Have** | Adds polish or a stretch demo moment. Build only with spare time. |

---

## P0 — Must Have (Non-Negotiable Core)

| # | Feature | Why P0 | Judging Impact |
|---|---|---|---|
| P0.1 | **Company Profile Onboarding** | Without a profile there is nothing to match tenders against. The anchor for the entire system. | Business (30%) |
| P0.2 | **TinyFish SAM.gov Agent** | Primary portal, judges expect to see it. Also the most well-documented for TinyFish. | Technical (50%) |
| P0.3 | **TinyFish TED EU Agent** | Proves multi-region — EU is the second-largest procurement market. | Technical (50%) |
| P0.4 | **TinyFish UNGM Agent** | Proves global/UN reach. Visually impressive in demo (UN logo). | Technical (50%) |
| P0.5 | **Parallel scraping with `asyncio.gather`** | Proves architecture maturity — running 3+ agents simultaneously is the key "wow" engineering moment. | Technical (50%) |
| P0.6 | **Tender Normalization + MongoDB Storage** | The foundation for scoring, dashboard, and alerts. Nothing works without it. | Technical (50%) |
| P0.7 | **Fireworks.ai Relevance Scoring (0–100)** | The AI intelligence layer. Score badge on dashboard is the most visible "AI moment" for judges. | Technical (50%) + Business (30%) |
| P0.8 | **React Dashboard — Tender List** | Judges must see a polished UI with real, scored data from multiple portals. | Market Signal (20%) |
| P0.9 | **Tender Detail View** | Shows the depth: score + match reasons + disqualifiers + action label. | Technical (50%) + Business (30%) |
| P0.10 | **TinyFish Deep RFP Scraper Agent** | Second distinct TinyFish use case — agents going *deeper* into a page. Critical for judging. | Technical (50%) |
| P0.11 | **Eligibility Pre-Qualification (pass/fail checklist)** | Most compelling business moment. "You qualify for 8/10 criteria, missing ISO 27001" is immediately understood. | Business (30%) |
| P0.12 | **Composio Slack Alert (≥1 type)** | Proves autonomous operation — system acts without human input. | Technical (50%) |
| P0.13 | **AgentOps Integration** | Proves production-grade observability. Judges can see real agent run logs. | Technical (50%) |
| P0.14 | **APScheduler Daily Scrape Job** | Proves the system is autonomous — not just a button you press. Critical for "production-ready" narrative. | Technical (50%) + Business (30%) |
| P0.15 | **Portal Health Status (/health + UI)** | Visible proof of robustness. ✅ SAM.gov · ⚠️ TED EU is a strong signal. | Technical (50%) |

---

## P1 — Should Have (High-Impact, Build After P0 Is Stable)

| # | Feature | Why P1 | Build After |
|---|---|---|---|
| P1.1 | **Amendment & Cancellation Tracker** | Third TinyFish use case — agent re-visits live pages. Strong "real-time" demo moment. | P0 complete |
| P1.2 | **ElevenLabs Daily Voice Briefing** | Unique and memorable. Differentiates on Market Signal criterion. Low build effort. | Alerts (P0.12) |
| P1.3 | **Find-a-Tender (UK) Agent** (portal 4) | More portals = stronger Technical score. UK is a major market. | P0.2–P0.4 all stable |
| P1.4 | **AusTender Agent** (portal 5) | Adds AU region, rounds out the 5-portal story for demo. | P1.3 done |
| P1.5 | **CanadaBuys Agent** (portal 6) | Completes the 6-portal coverage for the "global" narrative. | P1.4 done |
| P1.6 | **Email Digest via Composio** | 30-min add-on once Slack (P0.12) is working. Strengthens Business Viability. | P0.12 done |

---

## P2 — Nice to Have (Build Only With Spare Time After Day 11)

| # | Feature | Why P2 | Risk |
|---|---|---|---|
| P2.1 | **Auto Form-Fill Agent** (SAM.gov only) | Dramatic demo moment — TinyFish filling a real government form. But form UIs are unpredictable. | High breakage risk |
| P2.2 | **Competitor Intel & Win Probability** | Real B2B value but requires separate agent + award data scraping + complex LLM prompt. | High build time |
| P2.3 | **Subcontractor Opportunity Radar** | Interesting but separate data source, separate agent, separate UI tab. Full sprint of own. | Very high scope cost |
| P2.4 | **EU Multilingual Translation** | TED EU tenders auto-translated to English. Clever but not demo-critical. | Medium |
| P2.5 | **Multi-user Auth** | Product feature, not hackathon scope. | Out of scope |

---

## Frozen Scope Statement (30-Second Version)

> **TenderBot Global v1** scrapes 6 live government portals in parallel using TinyFish, AI-scores every tender 0–100 against your company profile, deep-scrapes high-score tenders to pre-qualify your eligibility per-criterion, displays everything in a React dashboard, and sends Slack alerts — all running automatically on a daily schedule without human intervention.

---

---

# DELIVERABLE 2 — Demo Storyboard (2–3 Min Video Flow)

> **Format:** Raw OBS screen recording. No slides. No cuts. Real data only.  
> **Target duration:** 2 min 30 sec  
> **Recording tool:** OBS Studio  
> **Camera:** Screen only (no webcam required)

---

## Pre-Demo Setup Checklist (before pressing record)

- [ ] Browser open at `https://tenderbot.vercel.app/dashboard`
- [ ] At least 20 scored tenders already in MongoDB from a prior scrape
- [ ] At least 3 enriched tenders (score ≥ 75, eligibility data populated)
- [ ] Slack channel `#procurement-alerts` has at least 1 real alert fired
- [ ] ElevenLabs audio file generated for today (if P1.2 done)
- [ ] `/health` page shows at least 3 portals ✅
- [ ] Company profile pre-seeded: "TechVentures Inc — Cloud/AI/Consulting — $100K–$5M"

---

## Shot-by-Shot Storyboard

| # | Duration | Screen | What You Say | What Judges See |
|---|---|---|---|---|
| **1** | 0:00–0:20 | Dashboard (full screen) | *"TenderBot Global monitors the $13 trillion government procurement market so SMBs don't have to. Right now, you're looking at live tenders — just scraped from SAM.gov, TED EU, and UNGM — scored and ranked by AI relevance."* | Tender cards with score badges (87/100, 92/100), country flags 🇺🇸🇪🇺🌐, deadline countdowns |
| **2** | 0:20–0:45 | Click "Run Discovery" button | *"Let me trigger a fresh scrape so you can see TinyFish in action. Three agents just launched in parallel — one on SAM.gov, one on TED EU, one on UNGM. No APIs. Just a real browser navigating each portal the way a human would."* | Live scrape status updating: "SAM.gov: scraping… 12 tenders found" / "TED EU: scraping… 9 tenders found" |
| **3** | 0:45–1:05 | Dashboard refreshes with new data | *"21 new tenders, scored in under 90 seconds. These are real, live listings — not from a database updated last week."* | Cards sorted by score, multiple portals visible in source badges |
| **4** | 1:05–1:35 | Click top-scoring tender (e.g., 91/100) | *"The top match is a DoD Cloud Infrastructure contract, $2.4 million, 12 days to close. Score 91 out of 100. TinyFish read the full RFP page to tell us why — cloud and software align with our profile, but we're missing ISO 27001."* | Detail view: score meter, match reasons list, disqualifiers highlighted in red |
| **5** | 1:35–2:00 | Scroll to Eligibility section | *"The eligibility pre-qualification runs against our actual company profile. 8 out of 10 criteria pass. The two gaps have an action plan — get ISO 27001, register on SAM.gov. This took a consultant days. TenderBot did it in seconds."* | Eligibility checklist: ✅ ✅ ✅ ❌ ✅ ✅ ✅ ✅ ❌ ✅ · Action plan bullets |
| **6** | 2:00–2:15 | Switch to Slack (screenshot or live) | *"The moment that tender was scraped and scored above 80, Composio fired a Slack alert to our procurement channel automatically."* | Slack message: 📋 DoD Cloud Infrastructure · Score 91 · 12 days · link |
| **7** | 2:15–2:25 | Click `/health` page | *"Every agent run is tracked in AgentOps. SAM.gov is healthy, TED EU had one timeout but recovered. This is a production-grade autonomous system, not a demo script."* | Health page: ✅ SAM.gov 94% · ✅ TED EU 88% · ✅ UNGM 91% |
| **8** | 2:25–2:30 | Back to dashboard, voice player (if P1.2) | *"Each morning there's a 60-second voice briefing. 21 new tenders today. Top pick — $2.4 million DoD Cloud. 12 days left. Good luck."* | Audio wave playing, "Today's Briefing" card |

---

## Demo Spoken Intro (30-Second Version for X Caption Context)

> *"Every competitor in this space is a static database updated once a day. TenderBot is an autonomous agent that goes out onto the live web right now, reads government portals that have zero APIs, and brings back only the opportunities your company can actually win — with eligibility pre-qualified, deadlines tracked, and alerts sent. Powered by TinyFish."*

---

---

# DELIVERABLE 3 — Risk Matrix with Mitigations

## Risk Scoring: Likelihood (1–5) × Impact (1–5) = Risk Score (1–25)

| # | Risk | Likelihood | Impact | Score | Mitigation | Fallback |
|---|---|:---:|:---:|:---:|---|---|
| **R1** | **TinyFish portal agent fails on one portal (layout change, timeout)** | 4 | 3 | **12** | Add retry logic (3 attempts with 5s backoff). Use try/except per agent in `asyncio.gather`. Log to `portal_logs`. | Other 5 portals continue. Show ⚠️ on health page. Demo still works with 2+ portals live. |
| **R2** | **TinyFish rate-limited or API key issue during demo** | 2 | 5 | **10** | Test API limits beforehand. Keep a pre-scraped dataset in MongoDB as backup. | Show dashboard using pre-loaded data. "Live scrape already ran this morning" narrative. |
| **R3** | **Fireworks.ai returns malformed JSON from scoring prompt** | 3 | 3 | **9** | Add JSON validation + fallback score of 50 if parse fails. Use `response_format={"type": "json_object"}` in API call. | Tender is stored without score, retried next run. UI shows "Scoring pending". |
| **R4** | **SAM.gov or TED EU changes UI/layout mid-build** | 3 | 4 | **12** | Monitor portal UIs daily. TinyFish natural-language goals are more robust than CSS selectors — less brittle. | Switch to alternate portal (UK/AU). Adjust goal prompt. 1-hour fix. |
| **R5** | **`asyncio.gather` deadlocks or one agent blocks others** | 2 | 4 | **8** | Set a timeout per TinyFish call (e.g., `asyncio.wait_for(agent(), timeout=120)`). | Failed agents return empty list. Others complete normally. |
| **R6** | **MongoDB write conflicts or duplicate tenders on concurrent scrapes** | 2 | 2 | **4** | Use `upsert=True` with `tender_id` as filter. Index on `tender_id` as unique. | Worst case: duplicate entry. Easy to clean with a dedup script. |
| **R7** | **Deep RFP scraper can't navigate to full tender page (login wall, redirect)** | 3 | 3 | **9** | Mark tender as `enriched: false`. Skip eligibility for that tender. Hide eligibility section in UI. | Demo falls back to showing eligibility on a different, successful tender. |
| **R8** | **Composio Slack integration misconfigured (wrong webhook, permissions)** | 2 | 3 | **6** | Test Slack alert before Day 7. Keep a screenshot of a fired alert as backup proof. | Show alert from pre-saved `alerts` collection in the Alerts Center UI. |
| **R9** | **Railway backend goes down during demo recording** | 1 | 5 | **5** | Record demo with backend running locally + ngrok tunnel as fallback. Keep Railway + local both ready. | Switch to local server. Demo looks identical. |
| **R10** | **LLM eligibility analysis hallucination (wrong pass/fail)** | 3 | 2 | **6** | Use a structured prompt with explicit "ONLY say pass, fail, or unknown" instruction. Validate output keys. | Manual override seeds for demo tender. UI still shows correct data. |
| **R11** | **React frontend build fails on Vercel** | 2 | 3 | **6** | Test Vercel build on Day 10 immediately after frontend is built. Keep `npm run dev` local as fallback. | Run localhost:3000 during demo recording. Not visible to viewer. |
| **R12** | **Time runs out before all P0s are done** | 2 | 5 | **10** | Strict build order (P0s only until Day 10). Stop Rule: no new features after Day 11 if core isn't stable. | Submit with 3 portals + scoring + dashboard. Still a strong entry without eligibility. |

---

## Top 3 Risks to Monitor Daily

1. **R1 + R4** — Portal reliability. Run each agent manually every morning during build to catch changes early.
2. **R3** — Fireworks.ai JSON parsing. Write the JSON validator on Day 4, don't leave it for later.
3. **R12** — Time. Check P0 checklist every evening. If any P0 is not done by its sprint day, drop all P1/P2 work immediately.

---

---

# DELIVERABLE 4 — Judging Criteria Alignment Matrix

> Answers: "For every judging criterion, which features satisfy it, and how?"

## Technical Maturity (50% of Score)

| Sub-criterion | Feature(s) that satisfy it | How to prove in demo |
|---|---|---|
| TinyFish as core infrastructure | P0.2–P0.4 (portal agents), P0.10 (deep RFP), P1.1 (amendment tracker) | Show live scrape running — TinyFish agent logs scrolling in real-time |
| Handles real-world edge cases | All portal agents handle: cookie banners, pagination, dynamic filters, session state | Mention during demo: "handling cookie consent on TED EU..." |
| Production-ready architecture | P0.13 (AgentOps), P0.14 (APScheduler), P0.15 (/health), P0.6 (MongoDB dedup) | Show /health page · mention "this runs every morning at 6 AM automatically" |
| Stable architecture | 7-layer separation (UI / API / Orchestration / Agents / LLM / DB / Notifications) | Reference architecture diagram in GitHub README |
| Multi-step web workflows | Each portal agent: open URL → handle cookies → apply filters → paginate → extract | Narrate the steps while showing scrape progress |
| Multiple distinct TinyFish uses | Portal search (×6), Deep RFP scraper, Amendment tracker, Form-fill (P2) | Explicitly name each agent type during demo |

**Target score:** 90th percentile on Technical (aim for a project that visibly cannot work without TinyFish)

---

## Business Viability (30% of Score)

| Sub-criterion | Feature(s) that satisfy it | How to prove in demo |
|---|---|---|
| Compelling reason to exist now | $13T global govt procurement market; no live-agent competitor exists today | State TAM in demo narration: "The $13 trillion market that's completely inaccessible to SMBs" |
| Solves a significant pain | Manual portal monitoring: 10+ hours/week per BD person; missed tenders = lost revenue | "TenderBot found this $2.4M opportunity in 90 seconds. A human would have missed it." |
| Clear path to a business | Freemium → $149/mo Pro → $499/mo Agency pricing model | Mention in X caption and HackerEarth business case write-up |
| ROI articulable | One missed government contract = $100K–$5M lost. TenderBot costs $149/mo. | "The ROI is asymmetric — missing one contract costs more than a year of TenderBot Pro." |
| Defined target customer | 100M+ SMBs, consultancies, NGOs globally priced out of GovWin ($15K/yr) | "Every company below $50M revenue that sells to governments is our customer." |

---

## Market Signal & Building in Public (20% of Score)

| Sub-criterion | Feature(s) that satisfy it | Success target |
|---|---|---|
| Raw demo video on X | 2–3 min OBS recording of live portal navigation + dashboard | Posted before March 29 · tags @Tiny_fish |
| Compelling X caption | One-line value prop + TAM + stack mention | 100+ views · 10+ likes |
| Public GitHub repo | Clean README with architecture diagram, setup guide, and sprint plan | Stars > 5 by submission |
| Build-in-public thread | Optional: X thread documenting Day 1 → Day 13 progress | Strengthens founder-product fit narrative |
| Demo persuasiveness | Storyboard (Deliverable 2) followed precisely | One-take recording · no slides |

---

## Accelerator Partner Usage (bonus credibility)

| Partner | How used | Demo mention |
|---|---|---|
| **TinyFish** | Core browser infrastructure — all portal agents | ✅ Primary — demo centers on it |
| **Fireworks.ai** | Relevance scoring + eligibility analysis | ✅ "Llama 3.1 70B scoring 21 tenders in 8 seconds" |
| **MongoDB Atlas** | Unified tender storage + dedup | ✅ "All data stored in MongoDB Atlas" |
| **Composio** | Slack + email alerts | ✅ "Composio fires the Slack alert instantly" |
| **ElevenLabs** | Daily voice briefing | ✅ (if P1.2 done) Play audio in demo |
| **AgentOps** | Agent run monitoring | ✅ Show /health → "Every run tracked in AgentOps" |
| **Vercel** | Frontend hosting | ✅ Live URL in X post |
| **Railway** | Backend hosting | Mention in README/architecture |

**More partners used meaningfully = stronger judging narrative. Target: 7/8 partners visible in demo.**

---

---

# DELIVERABLE 5 — Demo Checklist (Pass / Fail Criteria)

> Run through this checklist in full **before** pressing record.  
> Target: **15/17 items passing** minimum.

## Infrastructure

- [ ] **I1** — FastAPI backend is running and healthy (`/health` returns 200)
- [ ] **I2** — React frontend loads in < 3 seconds at the Vercel URL
- [ ] **I3** — MongoDB has ≥ 20 scored tenders from a real prior scrape
- [ ] **I4** — ≥ 3 tenders have `enriched: true` with eligibility data populated
- [ ] **I5** — Environment variables are set in Railway (not localhost-only)

## TinyFish Agents

- [ ] **T1** — SAM.gov agent returns ≥ 8 tenders in a manual test run
- [ ] **T2** — TED EU agent returns ≥ 5 tenders in a manual test run
- [ ] **T3** — UNGM agent returns ≥ 3 tenders in a manual test run
- [ ] **T4** — Parallel scrape (all 3+) completes in < 3 minutes without error
- [ ] **T5** — Deep RFP scraper successfully extracts eligibility from ≥ 1 tender

## AI Intelligence

- [ ] **A1** — All tenders in MongoDB have a `relevance_score` between 0–100
- [ ] **A2** — Top tender has `match_reasons` list with ≥ 2 reasons
- [ ] **A3** — At least 1 tender has complete `eligibility_checklist` (pass/fail per criterion)
- [ ] **A4** — `eligibility_action_plan` is readable and actionable (not LLM gibberish)

## Frontend

- [ ] **F1** — Dashboard shows tenders sorted by score descending
- [ ] **F2** — Clicking a tender opens detail view with eligibility section visible
- [ ] **F3** — Health page shows ✅ for at least 3 portals with success rate %

## Notifications & Monitoring

- [ ] **N1** — At least 1 Slack alert has fired to `#procurement-alerts` (can be pre-existing)
- [ ] **N2** — AgentOps dashboard shows recent portal agent sessions

## Demo Flow

- [ ] **D1** — Full storyboard (Deliverable 2, Steps 1–7) rehearsed without blocking issue once
- [ ] **D2** — All pre-loaded demo data looks realistic (not obvious test data like "test_tender_1")
- [ ] **D3** — X caption is written and ready to paste
- [ ] **D4** — HackerEarth submission text is written and ready to paste
- [ ] **D5** — GitHub README has architecture diagram and setup instructions

**Minimum passing score to record: 15/21 items checked (all T and A items must pass)**

---

## Summary: The 30-Second Explanation

> TenderBot Global is an autonomous AI agent that monitors 6 government procurement portals — SAM.gov, TED EU, UNGM, and more — in real time using TinyFish. It scores every tender against your company profile, pre-qualifies your eligibility criterion-by-criterion, and alerts you via Slack the moment an opportunity appears. No public APIs. No static databases. Just an agent that reads the live web for you.

**If you can say that from memory in under 30 seconds — you're ready to record.**
