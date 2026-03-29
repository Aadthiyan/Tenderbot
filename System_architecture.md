┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                               │
│   Company Profile → React Dashboard (Vercel v0) → REST API      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    ORCHESTRATION LAYER                           │
│              FastAPI Backend (Python)                            │
│     Routes: /scrape  /tenders  /profile  /alerts  /health       │
└──────┬──────────────────┬───────────────────┬───────────────────┘
       │                  │                   │
┌──────▼──────┐   ┌───────▼──────┐   ┌───────▼────────┐
│  TinyFish   │   │  Fireworks   │   │   APScheduler  │
│ Agent Pool  │   │  LLM Engine  │   │   Cron Jobs    │
└──────┬──────┘   └───────┬──────┘   └───────┬────────┘
       │                  │                   │
┌──────▼──────────────────▼───────────────────▼───────────────────┐
│                      DATA LAYER                                  │
│                  MongoDB Atlas                                   │
│     Collections: tenders / users / portal_logs / alerts         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     NOTIFICATION LAYER                           │
│          Composio (Slack/Email) + ElevenLabs (Voice)            │
└─────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                     MONITORING LAYER                             │
│               AgentOps (Agent run tracking)                     │
└─────────────────────────────────────────────────────────────────┘


Layer 1: User Layer
React Dashboard (Vercel v0) — The single-page app your users interact with.

Pages:
├── /onboard       → Company profile setup (sectors, keywords, budget, portals)
├── /dashboard     → Top tenders sorted by relevance score + deadline urgency
├── /tender/:id    → Full tender detail + eligibility checklist + apply button
├── /alerts        → Slack/email preferences + alert history
└── /health        → Per-portal live status (🟢/🔴)

UI Components:
├── TenderCard     → Title, country flag, agency, score badge, deadline countdown
├── ScoreMeter     → 0–100 relevance gauge (Fireworks.ai output)
├── PortalStatus   → Live scrape status per portal
└── VoicePlayer    → Daily ElevenLabs briefing audio player

Layer 2: Orchestration Layer
FastAPI Backend — Central brain coordinating all agents, scoring, DB, and alerts.

# Core API routes
POST /profile          → Save user company profile
POST /scrape           → Trigger manual multi-portal scrape
GET  /tenders          → Query tenders (filters: score, country, deadline, value)
GET  /tender/:id       → Full tender detail
POST /alerts/config    → Set Slack webhook + email preferences
GET  /health           → Per-portal scrape success rates
GET  /briefing/audio   → Serve today's ElevenLabs voice MP3

Key orchestration logic:

# Parallel portal scraping using asyncio
async def run_full_scrape(user_profile: dict):
    tasks = [
        scrape_portal("sam_gov", user_profile["keywords"]),
        scrape_portal("ted_eu", user_profile["keywords"]),
        scrape_portal("ungm", user_profile["keywords"]),
        scrape_portal("find_a_tender", user_profile["keywords"]),
        scrape_portal("austender", user_profile["keywords"]),
        scrape_portal("canadabuys", user_profile["keywords"]),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    tenders = [t for r in results if isinstance(r, list) for t in r]
    scored = await score_all_tenders(tenders, user_profile)
    await db.tenders.insert_many(deduplicate(scored))

Layer 3: TinyFish Agent Pool (Core)
6 Portal Agents — Each agent is a TinyFish stream configured for its portal's unique UI patterns.

PORTAL_CONFIGS = {
    "sam_gov": {
        "url": "https://sam.gov/search/?index=opp&q={kw}&dateRange=custom&startDate={30d_ago}",
        "goal": """
            Search for active procurement opportunities matching '{kw}'.
            Handle any cookie popups. Navigate through pagination (up to 3 pages).
            For each result extract: title, agency, naics_code, deadline,
            award_value, place_of_performance, solicitation_number, description.
            Return as JSON array.
        """,
        "auth_required": False,
        "handles": ["pagination", "dynamic_filters", "cookie_popups"]
    },
    "ted_eu": {
        "url": "https://ted.europa.eu/en/search?q={kw}&scope=ALL",
        "goal": """
            Search EU tenders for '{kw}'. Accept cookies popup.
            Sort by most recent. Extract from first 2 pages:
            title, contracting_authority, country, cpv_code,
            deadline, estimated_value, procedure_type, language.
            Return as JSON array.
        """,
        "auth_required": False,
        "handles": ["cookie_modal", "multilingual", "pagination"]
    },
    "ungm": {
        "url": "https://www.ungm.org/Public/Notice",
        "goal": """
            Navigate UN procurement notice board. Apply filter for
            open notices only. Search for '{kw}'. Extract:
            reference_number, title, organization, deadline,
            category, description for first 10 notices.
            Return as JSON array.
        """,
        "auth_required": False,
        "handles": ["dynamic_filters", "session_state"]
    },
    "find_a_tender": {
        "url": "https://www.find-a-tender.service.gov.uk/Search?keywords={kw}",
        "goal": """
            Search UK public contracts for '{kw}'. Extract from results:
            title, buyer_name, published_date, closing_date,
            contract_value, cpv_codes, procedure. Return as JSON array.
        """,
        "auth_required": False,
        "handles": ["pagination", "dynamic_UI"]
    },
    "austender": {
        "url": "https://www.tenders.gov.au/?event=public.atm.list",
        "goal": """
            Search AusTender for '{kw}'. Navigate filters for open tenders.
            Extract: atm_id, title, agency, close_date, value,
            category, state for first 10 results. Return as JSON array.
        """,
        "auth_required": False,
        "handles": ["form_fills", "session_management"]
    },
    "canadabuys": {
        "url": "https://canadabuys.canada.ca/en/tender-opportunities?q={kw}",
        "goal": """
            Search CanadaBuys for '{kw}'. Extract open tenders:
            solicitation_number, title, department, closing_date,
            procurement_category, region. Return as JSON array.
        """,
        "auth_required": False,
        "handles": ["pagination", "bilingual_UI"]
    }
}

Deep-Scrape Agent (for score ≥75 tenders):

deep_scrape_goal = """
    Navigate to this specific tender page: {url}
    Extract complete details: full description, eligibility criteria,
    required certifications, evaluation methodology, submission format,
    contact email, pre-bid meeting date, amendment history.
    If there is a 'Download Documents' button, click it and extract
    document names and sizes. Return all as structured JSON.
"""
# Handles: login walls, file dialogs, pop-up detail modals

Layer 4: Fireworks.ai Scoring Engine
LLM Relevance Scorer — Rates each tender 0–100 against user profile. [query]

SCORING_PROMPT = """
You are a procurement analyst. Score this tender's fit for the company.

Company: {company_name}
Sectors: {sectors}
Keywords: {keywords}
Budget: ${min_value}–${max_value}
Countries: {countries}
Certifications: {certs}

Tender:
Title: {title} | Agency: {agency} | Country: {country}
Value: ${value} | CPV/NAICS: {category_code}
Description: {description[:600]}

Return ONLY valid JSON:
{{
  "score": 0-100,
  "match_reasons": ["reason1", "reason2"],
  "disqualifiers": ["reason if any"],
  "action": "apply_now | watch | skip"
}}
"""
# Model: llama-v3p1-70b-instruct (fast + cheap on Fireworks.ai)
# Cost: ~$0.0009 per tender scored

Layer 5: MongoDB Data Layer
4 collections powering the entire app: [query]

// Collection 1: tenders
{
  _id: ObjectId,
  tender_id: "hash(title+agency+deadline)",  // dedup key
  source_portal: "sam_gov",
  title: "Cloud Infrastructure Services",
  agency: "Dept of Defense",
  country: "US",
  deadline: ISODate("2026-04-15"),
  days_until_deadline: 30,
  estimated_value: 2400000,
  description: "...",
  relevance_score: 87,
  match_reasons: ["cloud", "software"],
  action: "apply_now",
  status: "active",
  raw_url: "https://sam.gov/opp/...",
  scraped_at: ISODate,
  enriched: false
}

// Collection 2: users
{
  _id: ObjectId,
  company_name: "TechVentures Inc",
  sectors: ["IT", "Cloud", "AI"],
  keywords: ["cloud", "software", "AI"],
  countries: ["US", "EU", "UK", "AU"],
  min_value: 100000,
  max_value: 5000000,
  portals_enabled: ["sam_gov", "ted_eu", "ungm"],
  portal_credentials: {  // AES-256 encrypted
    sam_gov: { username: "enc...", password: "enc..." }
  },
  slack_webhook: "https://hooks.slack.com/...",
  email: "user@company.com",
  created_at: ISODate
}

// Collection 3: portal_logs
{
  portal: "sam_gov",
  run_at: ISODate,
  status: "success | failed | timeout",
  tenders_found: 14,
  duration_ms: 8400,
  error: null
}

// Collection 4: alerts
{
  tender_id: ObjectId,
  user_id: ObjectId,
  alert_type: "deadline_48h | new_match | status_change",
  sent_at: ISODate,
  channel: "slack | email | voice"
}


Layer 6: Notification Layer
Composio → Slack/Email + ElevenLabs → Voice [query]

# Slack alert (Composio)
def send_deadline_alert(tender, hours_left):
    message = f"""
⚠️ *Deadline Alert — {hours_left}hrs remaining*
📋 *{tender['title']}*
🏢 {tender['agency']} | 🌍 {tender['country']}
💰 ${tender['estimated_value']:,} | 🎯 Score: {tender['score']}/100
🔗 <{tender['raw_url']}|View Tender>
    """
    composio_toolset.execute_action(
        action=Action.SLACK_SEND_MESSAGE,
        params={"channel": "#procurement-alerts", "text": message}
    )

# Daily voice briefing (ElevenLabs)
def generate_daily_briefing(top_tenders):
    script = f"""
Good morning. TenderBot found {len(top_tenders)} high-match tenders today.
Top opportunity: {top_tenders[0]['title']} from {top_tenders[0]['agency']},
valued at {top_tenders[0]['estimated_value'] // 1000}K dollars,
closing in {top_tenders[0]['days_until_deadline']} days.
Relevance score: {top_tenders[0]['score']} out of 100.
Check your dashboard for the full list. Good luck.
    """
    audio = elevenlabs_client.generate(text=script, voice="Rachel")
    save(audio, "briefing_today.mp3")

Layer 7: Monitoring Layer
AgentOps — Tracks every TinyFish agent run for reliability. [query]

import agentops

@agentops.track_agent(name="portal_scraper")
async def scrape_portal(portal_key, keywords):
    with agentops.start_session() as session:
        session.record(agentops.ActionEvent(
            action_type="portal_scrape",
            params={"portal": portal_key, "keywords": keywords}
        ))
        # ... TinyFish call ...
        session.record(agentops.ActionEvent(
            action_type="scrape_complete",
            returns={"tenders_found": len(results)}
        ))

Dashboard shows: Per-portal success rate, avg latency, token usage, error breakdown — gives judges proof of production-grade engineering. [query]

