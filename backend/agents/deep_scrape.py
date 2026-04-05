"""
TenderBot Global — TinyFish Deep RFP Scraper Agent
For high-score tenders: opens the full tender page and extracts eligibility data.
"""
import json
import logging
import httpx
import agentops
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.config import get_settings
from backend.agents.portal_configs import DEEP_SCRAPE_GOAL

logger = logging.getLogger(__name__)
settings = get_settings()

TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=5, max=20),
    reraise=True,
)
async def deep_scrape_tender(tender_url: str) -> dict:
    """
    Opens the full tender detail page with TinyFish and extracts RFP intelligence.
    Returns a dict of enrichment fields to be merged into the tender document.
    """
    if not tender_url:
        return {}

    goal = DEEP_SCRAPE_GOAL.format(url=tender_url)
    logger.info(f"Deep scraping: {tender_url[:80]}…")

    session = None
    if settings.agentops_api_key:
        try:
            session = agentops.start_session(tags=["deep_scrape"])
        except Exception:
            pass

    if not settings.tinyfish_api_key:
        import asyncio
        await asyncio.sleep(2)
        return {
            "eligibility_requirements": ["ISO 27001", "Security Clearance", "Local Headquarters"],
            "required_certifications": ["ISO 27001"],
            "evaluation_criteria": "Price 40%, Technical 60%",
            "submission_format": "PDF via Email",
            "contact_email": "procurement@example.gov",
            "page_snapshot": "<html><body>Mock deep scrape payload...</body></html>"
        }

    try:
        headers = {
            "X-API-Key": settings.tinyfish_api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "url": tender_url,
            "goal": goal,
            "output_format": "json",
        }

        result = {}
        async with httpx.AsyncClient(timeout=settings.agent_timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{TINYFISH_BASE_URL}/automation/run-sse",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        event = json.loads(raw)
                        if event.get("type") == "result":
                            content = event.get("content", "{}")
                            result = _parse_deep_result(content)
                            break
                        elif event.get("type") == "error":
                            raise ValueError(f"TinyFish error: {event.get('message')}")
                    except (json.JSONDecodeError, KeyError):
                        continue

        if session:
            session.record(agentops.ActionEvent(
                action_type="deep_scrape_complete",
                returns={"url": tender_url[:80], "fields_extracted": len(result)}
            ))
            session.end_session(end_state="Success")

        logger.info(f"Deep scrape complete — {len(result)} fields extracted")

        pdf_links = result.get("pdf_attachments", [])
        if pdf_links:
            logger.info(f"Downloading & parsing {len(pdf_links)} PDF attachments via unstructured.io...")
            parsed_text_blocks = []
            try:
                from unstructured.partition.auto import partition
                import tempfile
                import os
                
                async with httpx.AsyncClient() as dl_client:
                    for pdf_url in pdf_links:
                        try:
                            # Download PDF to temp file
                            pdf_resp = await dl_client.get(pdf_url, follow_redirects=True, timeout=30.0)
                            pdf_resp.raise_for_status()
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                tmp.write(pdf_resp.content)
                                tmp_path = tmp.name
                                
                            # Extract text
                            elements = partition(filename=tmp_path)
                            text = "\n".join([str(el) for el in elements])
                            parsed_text_blocks.append(f"--- PDF APPEND: {pdf_url} ---\n{text[:5000]}") # Truncate to save tokens
                            
                            os.remove(tmp_path)
                        except Exception as e:
                            logger.warning(f"Failed to parse PDF {pdf_url}: {e}")
            except ImportError:
                logger.warning("unstructured library not installed for PDF parsing.")
            
            if parsed_text_blocks:
                existing_snap = result.get("page_snapshot", "")
                result["page_snapshot"] = existing_snap + "\n\n" + "\n\n".join(parsed_text_blocks)

        return result

    except Exception as e:
        if session:
            session.end_session(end_state="Fail")
        logger.error(f"Deep scrape failed for {tender_url[:80]}: {e}")
        return {}


def _parse_deep_result(content) -> dict:
    """Parse and sanitise the deep scrape JSON result."""
    if isinstance(content, dict):
        return _sanitise(content)
    if isinstance(content, str):
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(l for l in lines if not l.startswith("```")).strip()
        try:
            return _sanitise(json.loads(content))
        except json.JSONDecodeError:
            return {}
    return {}


def _sanitise(raw: dict) -> dict:
    """Keep only expected enrichment fields; coerce types."""
    return {
        "eligibility_requirements": _to_list(raw.get("eligibility_requirements")),
        "required_certifications": _to_list(raw.get("required_certifications")),
        "evaluation_criteria": raw.get("evaluation_criteria"),
        "submission_format": raw.get("submission_format"),
        "contact_email": raw.get("contact_email"),
        "contact_name": raw.get("contact_name"),
        "pre_bid_meeting": raw.get("pre_bid_meeting"),
        "amendment_notes": raw.get("amendment_notes"),
        "page_snapshot": (raw.get("page_snapshot") or "")[:2000],
    }


def _to_list(val) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val:
        return [val]
    return []
