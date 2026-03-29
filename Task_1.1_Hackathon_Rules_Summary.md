# Task 1.1 — Hackathon Rules & Judging Criteria Summary

> **Hackathon:** TinyFish $2M Pre-Accelerator Hackathon (HackerEarth)  
> **Dates:** Feb 25, 2026 → Mar 29, 2026 (11:59 PM IST)  
> **Prize:** Top 3 get cash prizes + **Golden Ticket** to TinyFish Accelerator Phase 2 (bypassing Phase 1 application), backed by a $2M seed fund from Mango Capital.

---

## ✅ What Judges WANT

### Criterion 1 — Product & Technical Maturity (50%)
- The app must be **production-ready**, not a prototype or toy.
- **TinyFish must be the core browser infrastructure** — not just called once in a demo.
- Architecture must be **stable** (not a single fragile script).
- The agent must handle **real-world edge cases**: cookie banners, pagination, login walls, dynamic UIs, session state.
- Every major workflow must pass **through** TinyFish (judges will look for this specifically).

### Criterion 2 — Business Viability (30%)
- There must be a **compelling reason** for the product to exist **right now**.
- It must solve a **significant, real B2B/B2C pain** — not a toy problem.
- The product must have a **clear path to becoming a real business** (pricing model, TAM, customer segment).
- ROI framing matters: "how much time/money does this save?" must be answerable in 1 sentence.

### Criterion 3 — Founder-Product Fit & Building in Public (20%)
- You must **post the demo publicly on X**, tagging `@Tiny_fish`, with a compelling caption.
- The demo video (2–3 min) must show the **agent navigating the live web in real-time** — slides are NOT accepted.
- Authenticity beats polish: a raw, real demo > a fancy slide deck.
- Judges evaluate your **ability to both build AND market** — the X post is the "market" proof.

---

## ❌ What Judges REJECT (Instant Disqualification or Low Score)

| Pattern | Why It Fails |
|---|---|
| Simple summarizer or chatbot | Doesn't use TinyFish; doesn't need a browser |
| Basic RAG application | Operates on a static database, not the live web |
| Thin UI wrapper over an API | No agentic behavior, no multi-step web workflow |
| No browser infrastructure needed | Core disqualifier — TinyFish must be *essential* |
| Mock/static data only | Judges must see real, live portal data |
| Copied idea | Immediate disqualification |
| Work predating Feb 25, 2026 | Immediate disqualification |
| Slides in demo video | Not accepted — must be raw agent demo |

---

## 🔒 Non-Negotiables Checklist

Before submission, every item below must be ticked:

- [ ] **TinyFish as core infra** — all portal navigation goes through TinyFish; cannot be replaced by a static scraper or API.
- [ ] **Live web data** — data comes from real, live portals scraped during the demo, not from pre-populated mock data.
- [ ] **Multi-step web workflow** — agents perform sequences of actions (search → filter → paginate → extract → deep-scrape).
- [ ] **Real-world edge cases handled** — cookie popups, pagination, dynamic UIs, session management.
- [ ] **Demo video on X** — 2–3 min raw recording posted publicly, tagging `@Tiny_fish`, with a compelling caption.
- [ ] **HackerEarth submission complete** — includes X post link, business case write-up, and technical architecture blurb.
- [ ] **Business case articulable** — can explain target customer, pain, ROI, and basic pricing in < 60 seconds.
- [ ] **Original work** — 100% built between Feb 25 and Mar 29, 2026.
- [ ] **Team size compliant** — solo or up to 4 members.

---

## 🎯 Why TenderBot Global Is a Strong Fit (2–3 Sentences)

TenderBot Global is a textbook fit for this hackathon because TinyFish is **irreplaceable** in every core workflow — government procurement portals like SAM.gov, TED EU, and UNGM have zero public APIs, so live browser automation is the only way to access them at all, not a nice-to-have.

Every major build decision maps directly to judging criteria: **6 parallel portal agents** = technical maturity; **$13T global procurement TAM + $149/mo SMB pricing** = business viability; **real-time multi-portal discovery with eligibility, competitor intel, and auto form-fill** = differentiated demo that will be publicly compelling on X.

The "agent vs database" framing is the story — where every competitor (GovWin, BidPrime, Tendium) is a static pre-aggregated database, TenderBot is a live autonomous agent, and TinyFish is what makes that technically possible.

---

## 🗺️ Feature → Judging Criterion Map

| TenderBot Feature | Technical (50%) | Business (30%) | Market Signal (20%) |
|---|:---:|:---:|:---:|
| 6 portal TinyFish agents (parallel) | ✅ Core | ✅ TAM | ✅ Demo moment |
| Real-world edge case handling | ✅ Maturity | | |
| AI relevance scoring (0–100) | ✅ LLM pipeline | ✅ ROI | ✅ Visible in demo |
| Deep RFP enrichment | ✅ Complex agent | ✅ Time saved | ✅ Demo moment |
| Eligibility pre-qualification | ✅ Agent + LLM | ✅ Win rate up | ✅ Demo moment |
| Competitor intel + win probability | ✅ Agent + LLM | ✅ Strategy value | ✅ Demo moment |
| Amendment tracking | ✅ Reliability | ✅ Risk prevention | |
| Auto form-fill | ✅ Multi-step form | ✅ Hours saved | ✅ Demo moment |
| Slack + Email alerts (Composio) | ✅ Integration | ✅ Workflow fit | |
| Daily voice briefing (ElevenLabs) | ✅ Integration | ✅ UX | ✅ Memorable demo |
| AgentOps monitoring | ✅ Production-grade | | |
| APScheduler cron jobs | ✅ Autonomy | ✅ Scalability | |
| Freemium → Pro → Agency pricing | | ✅ Business model | ✅ X post narrative |

**Conclusion:** No planned feature violates hackathon rules. Every feature either strengthens Technical Maturity, Business Viability, or Market Signal. ✅

---

## 📌 Submission Checklist (Day 13)

1. [ ] X post live with demo video + caption tagging `@Tiny_fish`
2. [ ] HackerEarth form submitted with:
   - X post URL
   - Business case paragraph
   - Technical architecture blurb
   - GitHub repo link
   - (Optional) screenshots
3. [ ] Demo video is 2–3 minutes, raw, shows live TinyFish portal navigation
4. [ ] All environment variables confirmed in Railway + Vercel
5. [ ] Backend + frontend publicly accessible via URL
