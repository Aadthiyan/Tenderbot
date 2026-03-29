"""
TenderBot Global — Auto-Submitter Action Agent (Feature 1)
Autonomous TinyFish agent that navigates to a tender application portal,
fills out the web form payload with the drafted proposal, and stops
before the final submission click.
"""
import httpx
import json
import logging
import agentops
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://api.tinyfish.ai"

# We use a generic sandbox target for the Hackathon Demo
# In production, this would be the specific SAM.gov or TED EU submission URL extracted during scraping.
DEMO_SUBMISSION_URL = "https://httpbin.org/forms/post"

AUTO_SUBMIT_GOAL_TEMPLATE = """
You are acting as an autonomous procurement agent. Your goal is to fill out a public tender submission form.

Navigate to the provided submission URL.
You possess the following Proposal Draft for Tender {tender_id} ({tender_title}):

PROPOSAL DRAFT:
{draft_content}

Instructions:
1. Locate the input field for 'Customer name' (or similar primary contact name field) and enter '{company_name}'.
2. Locate the input field for 'Comments' or 'Proposal Payload' and paste the entire PROPOSAL DRAFT.
3. Select any standard default radio buttons or checkboxes if required to unlock the form.
4. DO NOT click the final 'Submit' or 'Post' button. Only populate the form fields.
5. If you successfully fill the form, return a JSON response with status='ready_for_human' and a summary of what fields you filled.
"""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def auto_submit_proposal(tender_id: str, tender_title: str, company_name: str, draft_markdown: str, portal_url: str = DEMO_SUBMISSION_URL) -> dict:
    """
    Executes a TinyFish web agent to physically fill out a web form.
    """
    logger.info(f"🚀 Launching Auto-Submitter Action Agent for {tender_id}")

    goal = AUTO_SUBMIT_GOAL_TEMPLATE.format(
        tender_id=tender_id,
        tender_title=tender_title,
        company_name=company_name,
        draft_content=draft_markdown[:1500]  # Truncate slightly to avoid massive LLM context blowouts
    )

    if not settings.enable_live_submit:
        goal += "\n\nCRITICAL WARNING: THIS IS A DRY RUN. DO NOT CLICK THE FINAL SUBMIT OR POST BUTTON UNDER ANY CIRCUMSTANCES. ONLY FILL THE FORM OUT."

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["auto_submitter", "action_agent"])
        except Exception as e:
            logger.debug(f"AgentOps bypass: {e}")

    try:
        result_data = await _execute_action_tinyfish(portal_url, goal)
        
        if session:
            session.record(agentops.ActionEvent(
                action_type="auto_submit_staged",
                returns={"status": "success", "agent_response": result_data}
            ))
            session.end_session("Success")

        logger.info(f"✅ Auto-Submitter successfully staged proposal for {tender_id}.")
        return {"status": "success", "agent_response": result_data}

    except Exception as e:
        if session:
            session.record(agentops.ActionEvent(
                action_type="auto_submit_failed",
                returns={"error": str(e)}
            ))
            session.end_session("Fail")
        logger.error(f"❌ Auto-Submitter failed for {tender_id}: {e}")
        return {"status": "error", "error": str(e)}


async def _execute_action_tinyfish(url: str, goal: str) -> dict:
    """Handles SSE stream from TinyFish API for Action Tasks."""
    if not settings.tinyfish_api_key:
        logger.warning("TinyFish API Key missing — Returning mock success for Action Agent.")
        import asyncio
        await asyncio.sleep(2)
        return {"status": "ready_for_human", "summary": "Simulated filling 'Customer name' and 'Comments' field."}

    headers = {
        "Authorization": f"Bearer {settings.tinyfish_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "url": url,
        "goal": goal,
        "output_format": "json",
    }

    result_data = {}

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", f"{TINYFISH_BASE_URL}/agent", headers=headers, json=payload) as response:
            if response.status_code == 401:
                raise ValueError("Unauthorized. Check TINYFISH_API_KEY.")
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line.startswith("data:"): continue
                raw = line[5:].strip()
                if raw == "[DONE]": break
                try:
                    event = json.loads(raw)
                    if event.get("type") == "result":
                        content = event.get("content", "")
                        result_data = _parse_json(content)
                        break
                    elif event.get("type") == "error":
                        raise ValueError(f"Agent error: {event.get('message')}")
                except json.JSONDecodeError:
                    pass

    return result_data


def _parse_json(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = "\n".join(l for l in content.split("\n") if not l.startswith("```")).strip()
    try:
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        return {"status": "unknown", "raw_output": content}
