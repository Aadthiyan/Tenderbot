# TenderBot Global: Project Breakdown

## 1. Problem Statement
Companies bidding on government contracts face a highly inefficient, costly, and error-prone procurement process. On average, businesses spend between **$30,000 and $80,000 per month** sustaining dedicated human bid teams. Despite this massive investment, these teams frequently:
- Miss critical submission deadlines.
- Overlook deep compliance and eligibility requirements.
- Submit sub-optimized proposals against unknown competitors.

Consequently, average win rates stagger below **15%**. Adding to the friction is the technological barrier: the global procurement market represents over **$500B+ in annual opportunities** across major portals like SAM.gov, TED EU, and UNGM—yet **none of these platforms provide public APIs** for streamlined programmatic access, forcing companies into manual scraping and data entry.

## 2. Objective of the Project
The core objective of **TenderBot** is to democratize government procurement by replacing the repetitive, error-prone human bid pipeline with a **fully autonomous AI procurement swarm**. 

Specific goals include:
- **Zero-Touch Discovery:** Automatically identifying relevant government contracts across global portals.
- **Intelligent Qualification:** Filtering and scoring tenders based on strict company compliance profiles.
- **Autonomous Drafting:** Generating premium, self-correcting proposals customized to win against competitors.
- **Seamless Execution:** Navigating complex government portals to auto-submit applications.
- **Increasing ROI:** Boosting the average company win rate by 2–3x while drastically eliminating the overhead costs of human bid teams.

## 3. Methodology & AI Architecture
TenderBot solves the problem using an **Autonomous Multi-Agent Swarm** orchestrated via FastAPI. The methodology is broken down into specific agentic phases:

1. **Discovery (Web Browsing Agents):** Unconstrained by the lack of APIs, *TinyFish Scraper Agents* physically navigate and scrape 6 live government portals in parallel.
2. **Intelligence & Qualification (LLM Pipeline):** 
   - A *Scorer Agent* evaluating every tender (using Fireworks.ai Llama 3.1 70B) giving it a 0–100 relevance score against the user's company profile.
   - An *Eligibility Agent* performing deep-scrape compliance checks to produce a precise gap matrix (e.g., *"Missing ISO 27001 certification"*).
3. **Competitive Reconnaissance:** Spawning sub-agents that dynamically search Google for competitors, analyze their websites, and extract tech stacks and value propositions to inform the proposal.
4. **Self-Refining Drafting (Actor-Critic Loop):** A *Drafter Agent* writes the initial proposal, which is immediately strictly graded by an internal *Critic Agent*. If the score is below 90/100, the feedback is routed back for a rewrite (iterating up to 3 times) to ensure premium quality.
5. **Execution (Auto-Submitter):** An action agent physically navigates the target government UI, injects the proposal field-by-field, and stages the final application.
6. **Human-in-the-Loop (HITL) Catch:** If a high-scoring tender has a critical compliance gap, the pipeline halts and sends a Slack alert via Composio, awaiting human exemption or rejection. 

## 4. Scope of the Solution
The scope of TenderBot encompasses the entire lifecycle of a bid, targeting the **$12B Serviceable Market (SMBs + mid-market)**:
- **Platform Coverage:** SAM.gov (US), TED EU (Europe), UNGM (Global), Find-a-Tender (UK), AusTender (Australia), and CanadaBuys (Canada).
- **Backend Orchestration:** Async cron-based pipeline managing MongoDB Atlas state, preventing duplicate drafts via atomic DB upserts, and monitoring agent telemetry via AgentOps.
- **Frontend Dashboard:** A comprehensive Next.js/React interface to monitor Agent telemetry, view the draft queue, and manually confirm staging tasks.
- **Accessibility:** Daily AI-generated voice briefings (via ElevenLabs TTS) summarizing new opportunities directly to stakeholders' mobile devices.

## 5. Additional Relevant Details
- **Safety First:** The system is built with a hard mechanical gate (`ENABLE_LIVE_SUBMIT=False`) to ensure the Auto-Submitter operates in a dry-run phase, strictly preventing unintended multi-million dollar live submissions without explicit human authorization.
- **Resilience:** Integrates strict LLM context truncation to ensure processing 200-page RFP PDFs does not result in Out-of-Memory token crashes.
- **Market Impact:** By addressing the ~70% of the $500B market awarded via portals natively, TenderBot stands to disrupt one of the most bureaucratic and gatekept industries globally.
