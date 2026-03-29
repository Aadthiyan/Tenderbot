# TenderBot Global – Reference Guide

This file lists **all external references** you can use while building TenderBot Global, with a short note on **what each reference is for**.

---

## 1. TinyFish – Core Web Agent

1. **TinyFish Main Docs**  
   **URL:** https://docs.tinyfish.ai  
   **For:** Overall understanding of TinyFish concepts, capabilities, limits, and best practices for building autonomous web agents.

2. **TinyFish Quick Start**  
   **URL:** https://docs.tinyfish.ai/quick-start  
   **For:** Step‑by‑step guide to sending your first agent request, understanding streaming responses, and authenticating correctly.

3. **TinyFish Authentication**  
   **URL:** https://docs.tinyfish.ai/authentication  
   **For:** Setting up API keys securely and configuring headers/env vars so all TinyFish calls work from your backend.

4. **TinyFish Key Concepts & Endpoints**  
   **URL:** https://docs.tinyfish.ai/key-concepts/endpoints  
   **For:** Understanding available endpoints (e.g., `/agent`), request/response structure, and how to control goals, URLs, and session behavior.

5. **TinyFish Cookbook (GitHub)**  
   **URL:** https://github.com/tinyfish-io/tinyfish-cookbook  
   **For:** Concrete examples of TinyFish agents navigating real sites, handling multi‑step workflows, and streaming events; good starting point for portal agents.

---

## 2. Backend & API – FastAPI

6. **FastAPI Official Docs**  
   **URL:** https://fastapi.tiangolo.com  
   **For:** Building the backend orchestrator, defining routes (`/scrape`, `/tenders`, etc.), request/response models, and dependency injection.

7. **FastAPI – Async and Performance**  
   **URL:** https://fastapi.tiangolo.com/async  
   **For:** Learning how to use `async`/`await` correctly so you can run multiple TinyFish agents in parallel using `asyncio.gather`.

8. **FastAPI Bigger Applications Tutorial**  
   **URL:** https://fastapi.tiangolo.com/tutorial/bigger-applications  
   **For:** Structuring your project into modules (routers, services) when building a non‑trivial app like TenderBot.

9. **FastAPI + MongoDB Example**  
   **URL:** https://www.mongodb.com/developer/languages/python/python-quickstart-fastapi  
   **For:** Reference on connecting FastAPI to MongoDB, basic CRUD operations, and organizing DB access.

---

## 3. Database – MongoDB Atlas

10. **MongoDB Atlas Getting Started**  
    **URL:** https://www.mongodb.com/docs/atlas/getting-started  
    **For:** Creating a free cloud cluster, connecting from Python, and managing database users.

11. **PyMongo Documentation**  
    **URL:** https://pymongo.readthedocs.io  
    **For:** Using MongoDB from Python: inserts, updates, queries, indexes; implementing deduplication and filtering for tenders.

12. **MongoDB Indexing Overview**  
    **URL:** https://www.mongodb.com/docs/manual/indexes  
    **For:** Designing indexes on fields like `relevance_score`, `deadline`, `status`, and `country` to keep queries fast.

---

## 4. LLM Engine – Fireworks.ai

13. **Fireworks.ai Docs Home**  
    **URL:** https://docs.fireworks.ai  
    **For:** General overview of Fireworks, authentication, rate limits, and supported models.

14. **Fireworks Python Client**  
    **URL:** https://docs.fireworks.ai/tools-sdks/python-client/installation  
    **For:** Installing and using the Python SDK to call models like Llama 3.1 70B for scoring, eligibility, and competitor analysis.

15. **Fireworks Getting Started**  
    **URL:** https://docs.fireworks.ai/getting-started/quickstart  
    **For:** Example of sending prompts, reading JSON responses, and understanding model parameters.

---

## 5. Frontend – React & Vercel v0

16. **React Official Documentation**  
    **URL:** https://react.dev  
    **For:** Building the dashboard UI, managing state (tender lists, filters), and structuring components.

17. **Vercel v0 (AI UI Builder)**  
    **URL:** https://v0.dev  
    **For:** Rapidly generating React component boilerplate (cards, tables, layouts) from natural language prompts to speed up UI work.

18. **Vercel Deployment Guide**  
    **URL:** https://vercel.com/docs  
    **For:** Deploying the React frontend, configuring environment variables, and setting production build settings.

19. **shadcn/ui Component Library**  
    **URL:** https://ui.shadcn.com  
    **For:** Prebuilt, clean UI components (cards, tabs, badges) to make the dashboard look polished with minimal design time.

---

## 6. Notifications – Composio

20. **Composio Docs Home**  
    **URL:** https://docs.composio.dev  
    **For:** Understanding how Composio connects to 3rd‑party apps (Slack, email) and how to register your integration.

21. **Composio Python SDK Guide**  
    **URL:** https://docs.composio.dev/sdk/python  
    **For:** Using Composio from Python to send Slack messages and emails when new tenders or amendments appear.

22. **Composio Slack Integration Docs**  
    **URL:** https://docs.composio.dev/apps/slack  
    **For:** Configuring Slack as an action target, choosing channels, and formatting messages.

---

## 7. Voice – ElevenLabs

23. **ElevenLabs API Docs**  
    **URL:** https://elevenlabs.io/docs  
    **For:** Understanding how to authenticate, choose voices, and generate voice audio from text.

24. **ElevenLabs Python SDK (GitHub)**  
    **URL:** https://github.com/elevenlabs/elevenlabs-python  
    **For:** Examples of generating MP3 files in Python, which you can serve as the daily tender briefing.

---

## 8. Monitoring – AgentOps

25. **AgentOps Documentation**  
    **URL:** https://docs.agentops.ai  
    **For:** Setting up AgentOps, instrumenting your agents, and understanding what telemetry is available.

26. **AgentOps Quickstart**  
    **URL:** https://docs.agentops.ai/v1/quickstart  
    **For:** Minimal steps to start tracking TinyFish runs, including session creation and event logging.

27. **AgentOps Examples (GitHub)**  
    **URL:** https://github.com/AgentOps-AI/agentops/tree/main/examples  
    **For:** Reference patterns on how to wrap agent calls so they show clearly in the AgentOps dashboard.

---

## 9. Scheduling – APScheduler

28. **APScheduler User Guide**  
    **URL:** https://apscheduler.readthedocs.io/en/stable/userguide.html  
    **For:** Understanding different job types (cron, interval), configuring the scheduler, and adding jobs for scrapes and alerts.

29. **APScheduler + FastAPI Example Article**  
    **URL:** https://apscheduler.readthedocs.io/en/stable/userguide.html#running-apscheduler-in-a-web-application  
    **For:** Best practices for running APScheduler in a web app context so it doesn’t block requests.

---

## 10. Hosting – Railway & Vercel

30. **Railway Docs**  
    **URL:** https://docs.railway.app  
    **For:** Deploying your FastAPI backend, configuring environment variables, and connecting to MongoDB Atlas.

31. **Railway Python Guide**  
    **URL:** https://docs.railway.app/guides/python  
    **For:** Step‑by‑step instructions for packaging and running a Python web app on Railway.

32. **Vercel Getting Started**  
    **URL:** https://vercel.com/docs/getting-started-with-vercel  
    **For:** Creating the project, linking your GitHub repo, and deploying the React app.

---

## 11. Domain & Market References

33. **Tender Management Software Overview**  
    **URL:** https://www.sparrowgenie.com/blog/tender-management-software  
    **For:** Understanding existing tools in the tender management space and how they position themselves.

34. **GovWin Alternatives Article**  
    **URL:** https://www.pursuit.us/blog/govwin-alternatives-and-competitors  
    **For:** Competitive landscape (GovWin, BidPrime, etc.) and inspiration for how to differentiate TenderBot.

35. **Tender Software Comparison (EU‑focused)**  
    **URL:** https://www.tenderbolt.ai/en/post/logiciel-appel-d-offres-comparatif-10-meilleures-solutions  
    **For:** Examples of EU tender tools and the limitations of static databases vs live agents.

36. **Monitoring SAM.gov Article**  
    **URL:** https://monity.ai/guides/monitor-sam-gov-solicitations  
    **For:** How traditional tools monitor SAM.gov and why a web‑agent approach is more flexible.

37. **AI‑Powered Procurement Platforms Overview**  
    **URL:** https://www.ioscm.com/blog/top-6-ai-powered-procurement-platforms-transforming-supply-chain-management  
    **For:** Context on how AI is currently used in procurement (usually not with browser agents), helping position TenderBot as next‑generation.

---

## 12. General Agentic AI & Browser Automation

38. **Industries Where Browser‑Level Agents Excel**  
    **URL:** https://www.linkedin.com/pulse/industries-where-browser-level-ai-agents-outshine-tyler-mcgregory-uighe  
    **For:** Background on why browser‑level agents beat traditional automation tools in certain industries; useful for pitch framing.

39. **AI Browser Agents for Web Automation (Blog)**  
    **URL:** https://www.amplework.com/blog/ai-browser-agents-web-automation  
    **For:** Conceptual understanding of browser agents and example use cases similar to what TinyFish enables.

---

Use this reference guide as your **single index** while building TenderBot Global. Each link has a clearly defined purpose so you can quickly look up the right documentation or market research when you need it.
