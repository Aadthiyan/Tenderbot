"""
TenderBot Global — Tender Normalizer
Converts raw portal-specific JSON into the canonical tender schema.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Portal-specific field mappings: raw_key -> canonical_key
FIELD_MAPS: dict[str, dict[str, str]] = {
    "sam_gov": {
        "title": "title",
        "agency": "agency",
        "naics_code": "category_code",
        "deadline": "deadline",
        "award_value": "estimated_value",
        "place_of_performance": "country",
        "solicitation_number": "reference_id",
        "description": "description",
        "url": "raw_url",
    },
    "ted_eu": {
        "title": "title",
        "contracting_authority": "agency",
        "country": "country",
        "cpv_code": "category_code",
        "deadline": "deadline",
        "estimated_value": "estimated_value",
        "procedure_type": "procedure_type",
        "url": "raw_url",
    },
    "ungm": {
        "title": "title",
        "organization": "agency",
        "deadline": "deadline",
        "category": "category_code",
        "description": "description",
        "reference_number": "reference_id",
        "url": "raw_url",
    },
    "find_a_tender": {
        "title": "title",
        "buyer_name": "agency",
        "closing_date": "deadline",
        "contract_value": "estimated_value",
        "cpv_codes": "category_code",
        "url": "raw_url",
    },
    "austender": {
        "title": "title",
        "agency": "agency",
        "close_date": "deadline",
        "value": "estimated_value",
        "category": "category_code",
        "atm_id": "reference_id",
        "url": "raw_url",
    },
    "canadabuys": {
        "title": "title",
        "department": "agency",
        "closing_date": "deadline",
        "procurement_category": "category_code",
        "solicitation_number": "reference_id",
        "url": "raw_url",
    },
}

# Default country per portal (fallback when portal doesn't include country)
PORTAL_COUNTRIES: dict[str, str] = {
    "sam_gov": "US",
    "ted_eu": "EU",
    "ungm": "UN",
    "find_a_tender": "UK",
    "austender": "AU",
    "canadabuys": "CA",
}


def normalize_tender(raw: dict) -> dict:
    """
    Maps a raw portal-specific tender dict into the canonical schema.
    Computes tender_id from hash(title + agency + deadline).
    """
    portal = raw.get("_source_portal", "unknown")
    field_map = FIELD_MAPS.get(portal, {})

    canonical: dict[str, Any] = {
        "source_portal": portal,
        "status": "active",
        "enriched": False,
        "relevance_score": None,
        "match_reasons": [],
        "disqualifiers": [],
        "action": None,
        "eligibility_requirements": [],
        "eligibility_score": None,
        "eligibility_checklist": [],
        "eligibility_action_plan": [],
        "amendment_history": [],
        "top_competitors": [],
        "scraped_at": datetime.utcnow(),
        "last_checked": datetime.utcnow(),
    }

    # Map raw fields → canonical fields
    for raw_key, canon_key in field_map.items():
        val = raw.get(raw_key)
        if val is not None:
            canonical[canon_key] = val

    # Fill any remaining fields from raw using raw key directly
    for k, v in raw.items():
        if k not in canonical and k != "_source_portal":
            canonical.setdefault(k, v)

    # ── Field coercions ───────────────────────────────────────────────────────

    # Ensure title exists
    canonical["title"] = _str(canonical.get("title", "Untitled Tender"))

    # Ensure agency
    canonical["agency"] = _str(canonical.get("agency", "Unknown Agency"))

    # Country fallback
    if not canonical.get("country"):
        canonical["country"] = PORTAL_COUNTRIES.get(portal, "UNKNOWN")

    # Normalise deadline → ISO datetime
    canonical["deadline"] = _parse_date(canonical.get("deadline"))

    # Days until deadline
    if canonical["deadline"]:
        delta = canonical["deadline"] - datetime.utcnow().replace(tzinfo=timezone.utc)
        canonical["days_until_deadline"] = max(0, delta.days)
    else:
        canonical["days_until_deadline"] = None

    # Normalise value → float USD
    canonical["estimated_value"] = _parse_value(canonical.get("estimated_value"))

    # Ensure raw_url exists
    if not canonical.get("raw_url"):
        canonical["raw_url"] = raw.get("url", raw.get("link", ""))

    # Truncate description for storage efficiency
    if canonical.get("description") and len(canonical["description"]) > 1000:
        canonical["description"] = canonical["description"][:1000] + "…"

    # ── Compute tender_id (deduplication key) ─────────────────────────────────
    id_str = f"{canonical['title']}|{canonical['agency']}|{canonical.get('deadline', '')}"
    canonical["tender_id"] = hashlib.sha256(id_str.encode()).hexdigest()[:24]

    return canonical


# ── Helpers ───────────────────────────────────────────────────────────────────

def _str(val: Any) -> str:
    return str(val).strip() if val else ""


def _parse_date(val: Any) -> datetime | None:
    """Try to parse various date string formats globally."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=timezone.utc) if val.tzinfo is None else val
    if not isinstance(val, str):
        return None
    val = val.strip()
    try:
        from dateutil import parser
        parsed_date = parser.parse(val, fuzzy=True)
        return parsed_date.replace(tzinfo=timezone.utc) if parsed_date.tzinfo is None else parsed_date
    except Exception as e:
        logger.debug(f"Could not parse date: '{val}' ({e})")
        return None


def _parse_value(val: Any) -> float | None:
    """Convert a value string like '$2,400,000' or '2.4M' → float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val = str(val).strip().replace(",", "").replace("$", "").replace("£", "").replace("€", "")
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    lower = val.lower()
    for suffix, mult in multipliers.items():
        if lower.endswith(suffix):
            try:
                return float(lower[:-1]) * mult
            except ValueError:
                return None
    try:
        return float(val)
    except ValueError:
        return None
