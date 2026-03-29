1. TinyFish Web Agent API
What it is: Enterprise‑grade API for AI web agents that navigate real websites, handle sessions, dynamic UIs, logins, and return structured results.

Why used here:

Core requirement of the hackathon: the app must use TinyFish as the browser infrastructure.

Only practical way to automate multi‑step workflows on SAM.gov, TED EU, UNGM, Find‑a‑Tender, AusTender, CanadaBuys, and prime contractor portals.
​

Handles JavaScript SPAs, pagination, pop‑ups, and authenticated sessions, which standard scrapers or APIs cannot reliably cover.
​

Purpose in TenderBot:

Power all portal agents: search agents, deep RFP scraper, amendment tracker, subcontractor radar, and auto form‑fill.

Provide live, real‑time tender data directly from official portals, satisfying “live web, not static DB” criteria.

2. FastAPI (Python)
What it is: High‑performance Python web framework designed for async APIs.
​

Why used here:

Async async/await support lets you run multiple TinyFish agents in parallel using asyncio.gather, critical for scraping 6 portals in one job.
​

Built‑in OpenAPI/Swagger docs give you automatic API documentation for judges and for your own testing.

Python aligns with your skills and integrates easily with PyMongo, Fireworks, Composio, etc. [user-information]

Purpose in TenderBot:

Acts as the orchestrator: exposes routes (/scrape, /tenders, /auto-fill, /alerts, /health), coordinates TinyFish calls, triggers scoring and eligibility, and sends data to MongoDB and the frontend.

3. MongoDB Atlas + PyMongo
What it is: Cloud NoSQL document database; PyMongo is its Python client.
​

Why used here:

Flexible JSON document model fits tender data from different portals with varying fields.

Easy to store nested structures like eligibility checklists, amendment histories, competitor intel arrays.

Atlas free tier is enough for hackathon‑scale data and is known to work well with TinyFish‑style workloads.
​

Purpose in TenderBot:

Persistent storage for tenders, users, portal_logs, and alerts.

Enables fast querying of tenders by relevance_score, deadline, country, and status to power dashboard and alerts.

4. Fireworks.ai (Llama‑3.x Models)
What it is: LLM hosting platform with OpenAI‑compatible API and optimized Llama models.

Why used here:

Very low latency and cost for large models like Llama 3.1 70B, ideal for batch scoring tens of tenders after each scrape.
​

Supports JSON‑friendly outputs, which you need for structured fields (scores, reasons, eligibility checklist).

Purpose in TenderBot:

Relevance scoring: compute 0–100 match scores + reasons for each tender vs company profile.

Eligibility pre‑qualification: compare RFP requirements against user profile and output pass/fail per criterion + action plan.

Competitor analysis: summarize past award data and estimate win probability and patterns.

5. React (with Vercel v0) for Frontend
What it is: Popular component‑based frontend framework; v0 is Vercel’s AI‑powered UI generator.

Why used here:

React makes it easy to build dynamic dashboards (cards, filters, tabs) that react to real‑time data.

v0 can auto‑generate layouts and components (tender cards, detail views) from text prompts, saving front‑end time during the hackathon.

Purpose in TenderBot:

Implement the user layer:

Dashboard of top tenders (score, deadline, country).

Tender detail view (eligibility, competitor intel, amendments, auto‑fill status).

Sub‑opportunities tab and Alerts feed.

Profile onboarding & portal selection.

6. Vercel (Frontend Hosting)
What it is: Frontend hosting platform optimized for React/Next apps.

Why used here:

One‑click deploy from GitHub, free tier is enough for the hackathon.

Integrated with v0 and good DX for environment variables and preview URLs.

Purpose in TenderBot:

Host the public demo UI that judges and users access via browser.

Provide stable URL for your HackerEarth submission and for the X post.

7. Railway (Backend Hosting)
What it is: Cloud platform for easily deploying backend services (containers, web apps) on free credit.

Why used here:

Very simple to deploy a FastAPI app from GitHub; handles build, run, and env vars.

Supports always‑on services, so APScheduler cron jobs can run inside the container.

Purpose in TenderBot:

Run the FastAPI backend that orchestrates agents, LLM calls, database operations, and notifications.

8. Composio
What it is: Integration platform that exposes 100+ SaaS tools (Slack, Gmail, Notion, etc.) as agent‑callable actions.

Why used here:

Provides ready‑made Slack and email actions without building custom OAuth flows or webhooks.
​

Built with agents in mind, so it fits the “agentic” narrative well and is part of the TinyFish partner ecosystem.

Purpose in TenderBot:

Send Slack alerts for:

New high‑score tenders.

Approaching deadlines.

Amendments or cancellations.

New subcontractor opportunities.

Optionally send email digests of daily matches.

9. ElevenLabs
What it is: State‑of‑the‑art text‑to‑speech platform with high‑quality voices.

Why used here:

Enables a unique, memorable feature: daily voice briefing summarizing top tenders—great for the “market signal” and originality aspect.

Simple HTTP API and Python SDK; can generate MP3s from dynamic text quickly.

Purpose in TenderBot:

Produce a short audio report each morning per user: number of new tenders, top opportunity details, eligibility score, win probability, and any critical amendments.

10. AgentOps
What it is: Observability and analytics platform for AI agents and LLM workflows.

Why used here:

Automatically instruments LLM calls and tool invocations after initialization; gives you a dashboard of sessions, costs, errors, and latency.
​

Shows you and the judges that TenderBot is production‑grade, with metrics and traceability.

Purpose in TenderBot:

Monitor TinyFish agent runs for each portal, deep scraper, eligibility agent, etc.

Measure success rates per portal, identify flaky sites, and show system health in the /health endpoint and in your narrative.

11. APScheduler
What it is: Python scheduling library for cron‑like background jobs.

Why used here:

Lets you run jobs (multi‑portal scrapes, amendment checks, deadline alerts, voice brief generation) on fixed schedules inside the FastAPI process.

No separate cron server required, perfect for a hackathon deployment.

Purpose in TenderBot:

Automate all recurring workflows:

Daily multi‑portal scraping.

Periodic amendment detection.

Regular deadline alert scans.

Daily voice report creation.

12. GitHub (Code Hosting & Version Control)
What it is: Standard git‑based source hosting platform.

Why used here:

Required for clean dev workflow and easy deployment to Vercel/Railway.

Judges can inspect code and architecture easily via the repo link.

Purpose in TenderBot:

Store the full codebase and documentation (README, sprint plan, references).

Serve as integration point for CI/CD (optional).

13. Supporting Libraries / Tools
Python (3.10+)

Base language for all backend logic, TinyFish calls, LLM integration, scheduling, and notifications.

requests / httpx (if used)

For any non‑TinyFish HTTP calls (e.g., service health checks, metadata queries).

dotenv / environment management

To securely load API keys (TinyFish, Fireworks, Composio, ElevenLabs, AgentOps, MongoDB, Railway, Vercel) from environment variables, not hard‑coded.

How All Pieces Work Together
User configures company profile and preferences via React UI (Vercel).

FastAPI backend receives profile, stores in MongoDB, and schedules daily scrapes through APScheduler.

Each day, TinyFish agents parallel‑scrape 6+ portals, normalize results, store them into MongoDB.

Fireworks.ai scores tenders and runs eligibility + competitor analysis; results enrich tender documents.

React dashboard fetches from FastAPI and shows top tenders, eligibility, win probability, amendments, subcontractor opportunities.

Composio sends Slack/email alerts for new/growing opportunities and amendments; ElevenLabs generates the daily voice briefing.
​

Every agent run is tracked in AgentOps, giving metrics and traces to prove robustness.

This stack is deliberately chosen to maximize alignment with the hackathon theme (agentic web via TinyFish), showcase multi‑tool integration, and still be realistic for a solo builder to ship a polished, demo‑ready product.