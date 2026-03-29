"""
TenderBot Global — Composio Alert Engine (Phase 7.1)
Delivers structured Slack messages for 3 alert types:
  1. NEW_TENDER    — a high-score tender just appeared
  2. DEADLINE_WARN — a tracked tender's deadline is < 7 days away
  3. AMENDMENT     — a monitored tender just changed (deadline/doc/cancel)

All sent via Composio SLACK_SEND_MESSAGE action.
Mock-safe: falls back to pretty console output when COMPOSIO_API_KEY is missing.
"""
import json
import logging
from datetime import datetime
from typing import Literal
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

AlertType = Literal["new_tender", "deadline_warn", "amendment", "clarification_needed"]


# ── Slack Block Formatters ────────────────────────────────────────────────────

def _new_tender_blocks(tender: dict) -> list[dict]:
    score = tender.get("relevance_score", "?")
    title = tender.get("title", "Untitled Tender")
    agency = tender.get("agency", "Unknown Agency")
    value = tender.get("estimated_value")
    value_str = f"${value / 1_000_000:.1f}M" if value else "TBD"
    days = tender.get("days_until_deadline")
    deadline_str = f"{days} days" if days is not None else "TBD"
    country = tender.get("country", "?")
    url = tender.get("raw_url", "#")
    reasons = tender.get("match_reasons", [])

    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"🚀 New High-Priority Tender — Score {score}/100"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*{title}*\n_{agency}_"},
            {"type": "mrkdwn", "text": f"*Value:* {value_str}\n*Deadline:* {deadline_str}\n*Country:* {country}"}
        ]},
        *([{"type": "section", "text": {"type": "mrkdwn", "text": ":white_check_mark: *Why it matches:*\n" + "\n".join(f"• {r}" for r in reasons[:3])}}] if reasons else []),
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "📋 View Tender"}, "url": url, "style": "primary"},
        ]},
        {"type": "divider"},
    ]


def _deadline_warn_blocks(tender: dict) -> list[dict]:
    title = tender.get("title", "Untitled Tender")
    days = tender.get("days_until_deadline", "?")
    deadline = tender.get("deadline", "Unknown")
    score = tender.get("relevance_score", "?")
    url = tender.get("raw_url", "#")
    urgency_emoji = "🔴" if (isinstance(days, int) and days <= 3) else "🟡"

    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"{urgency_emoji} Deadline Warning — {days} Days Left"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"Your tracked tender is approaching its deadline.\n\n*{title}*\n\n:calendar: Deadline: *{deadline}*\n:bar_chart: Relevance Score: *{score}/100*"}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "⚡ Take Action Now"}, "url": url, "style": "danger"},
        ]},
        {"type": "divider"},
    ]


def _amendment_blocks(tender: dict, amendment: dict) -> list[dict]:
    title = tender.get("title", "Untitled Tender")
    change_type = amendment.get("change_type", "update").replace("_", " ").title()
    summary = amendment.get("changes_summary", "Changes detected on this tender.")
    new_deadline = amendment.get("new_deadline")
    is_cancelled = amendment.get("is_cancelled", False)
    url = tender.get("raw_url", "#")

    type_emoji = {
        "Deadline Extension": "📅",
        "New Document": "📄",
        "Scope Change": "🔄",
        "Cancellation": "❌",
        "Clarification": "💬",
    }.get(change_type, "⚠️")

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"{type_emoji} Amendment Alert: {change_type}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*\n\n{summary}"}},
    ]

    if new_deadline:
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": f":calendar: *New Deadline:* {new_deadline}"}})

    if is_cancelled:
        blocks.append({"type": "section", "text": {"type": "mrkdwn",
            "text": ":x: *This tender has been CANCELLED. Remove from your pipeline.*"}})

    blocks += [
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🔍 Review Changes"}, "url": url},
        ]},
        {"type": "divider"},
    ]
    return blocks

def _clarification_blocks(tender: dict) -> list[dict]:
    score = tender.get("relevance_score", "?")
    title = tender.get("title", "Untitled Tender")
    url = tender.get("raw_url", "#")
    
    # Extract the failing requirement
    checklist = tender.get("eligibility_checklist", [])
    gap_req = next((c for c in checklist if c.get("status") == "fail"), None)
    req_text = gap_req.get("requirement", "Unknown Requirement") if gap_req else "Unknown Requirement Gap"
    gap_desc = gap_req.get("gap", "Needs human verification") if gap_req else "Needs human verification"

    return [
        {"type": "header", "text": {"type": "plain_text", "text": "🛑 Action Required: Eligibility Gap detected"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*\nScore: {score}/100. This is a high-value bid, but you are currently ineligible. Should I try to draft a waiver?"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Failed Requirement:* {req_text}"},
            {"type": "mrkdwn", "text": f"*AI Diagnosis:* {gap_desc}"}
        ]},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "✅ Proceed with Waiver"}, "url": "http://localhost:3000/tenders", "style": "primary"},
            {"type": "button", "text": {"type": "plain_text", "text": "❌ Abort Bid"}, "url": "http://localhost:3000/tenders", "style": "danger"},
        ]},
        {"type": "divider"},
    ]


# ── Core send function ────────────────────────────────────────────────────────

async def send_alert(
    alert_type: AlertType,
    tender: dict,
    amendment: dict | None = None
) -> dict:
    """
    Send a formatted Slack alert via Composio.
    Falls back to console print if COMPOSIO_API_KEY is not set.
    """
    channel = settings.slack_channel or "#procurement-alerts"

    if alert_type == "new_tender":
        blocks = _new_tender_blocks(tender)
        text = f"🚀 New tender: {tender.get('title')} — Score {tender.get('relevance_score')}/100"
    elif alert_type == "deadline_warn":
        blocks = _deadline_warn_blocks(tender)
        text = f"⚠️ DEADLINE WARNING: {tender.get('title')} — {tender.get('days_until_deadline')} days left"
    elif alert_type == "amendment" and amendment:
        blocks = _amendment_blocks(tender, amendment)
        text = f"📋 Amendment: {tender.get('title')} — {amendment.get('change_type')}"
    elif alert_type == "clarification_needed":
        blocks = _clarification_blocks(tender)
        text = f"🛑 Clarification Needed for {tender.get('title')}."
    else:
        logger.warning(f"Unknown alert type or missing amendment data: {alert_type}")
        return {"status": "skipped"}

    if not settings.composio_api_key:
        _mock_console_alert(alert_type, text, blocks)
        return {"status": "mock_sent", "channel": channel, "alert_type": alert_type}

    try:
        from composio_openai import ComposioToolSet, App, Action
        toolset = ComposioToolSet(api_key=settings.composio_api_key)
        result = toolset.execute_action(
            action=Action.SLACK_SEND_MESSAGE,
            params={
                "channel": channel,
                "text": text,
                "blocks": json.dumps(blocks),
            }
        )
        logger.info(f"✅ Slack alert sent: {alert_type} → {channel}")
        return {"status": "sent", "channel": channel, "alert_type": alert_type, "result": result}

    except Exception as e:
        logger.error(f"Composio Slack alert failed: {e}")
        _mock_console_alert(alert_type, text, blocks)
        return {"status": "fallback_mock", "error": str(e)}


def _mock_console_alert(alert_type: str, text: str, blocks: list) -> None:
    """Pretty-print a simulated Slack alert to the console."""
    ts = datetime.utcnow().strftime("%H:%M:%S UTC")
    width = 65
    print()
    print("=" * width)
    print(f"  📬 SLACK ALERT SIMULATION [{ts}]")
    print(f"  Type: {alert_type.upper()}")
    print(f"  Text: {text[:60]}...")
    print("-" * width)
    for block in blocks:
        btype = block.get("type")
        if btype == "header":
            print(f"  ▶ {block['text']['text']}")
        elif btype == "section":
            txt = block.get("text", {}).get("text") or ""
            for field in block.get("fields", []):
                txt = field.get("text", "")
                print(f"    {txt[:60]}")
            if txt and not block.get("fields"):
                print(f"    {txt[:75]}")
        elif btype == "actions":
            for el in block.get("elements", []):
                btn_text = el.get("text", {}).get("text", "")
                print(f"    [ {btn_text} ]")
    print("=" * width)
    print()
