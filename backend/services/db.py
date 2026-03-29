"""
TenderBot Global — MongoDB Connection & Collection References
Single connection shared across the entire app via FastAPI lifespan.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from backend.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# Module-level client (set during lifespan startup)
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Call once at FastAPI startup. NEVER raises — logs and continues on failure."""
    global _client, _db
    try:
        import ssl
        import certifi

        # Python 3.13 ships OpenSSL 3.x which disabled legacy TLS renegotiation
        # by default. MongoDB Atlas requires it → fix with OP_LEGACY_SERVER_CONNECT.
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        ssl_ctx.check_hostname = True
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
            ssl_ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT

        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
        )
        _db = _client[settings.mongodb_db_name]
        try:
            await _ensure_indexes()
            logger.info(f"✅ MongoDB connected → database: '{settings.mongodb_db_name}'")
        except Exception as idx_err:
            logger.warning(f"⚠️  Index creation skipped: {idx_err}")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        logger.warning("⚠️  Running in DEGRADED mode — DB unavailable.")







async def close_db() -> None:
    """Call once at FastAPI shutdown."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency — returns the active database."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db


# ── Collection helpers ────────────────────────────────────────────────────────

def tenders_col():
    return get_db()["tenders"]

def users_col():
    return get_db()["users"]

def portal_logs_col():
    return get_db()["portal_logs"]

def alerts_col():
    return get_db()["alerts"]

def knowledge_base_col():
    return get_db()["knowledge_base"]

def audit_logs_col():
    return get_db()["audit_logs"]

def draft_queue_col():
    return get_db()["draft_queue"]

def bid_outcomes_col():
    return get_db()["bid_outcomes"]

def agent_runs_col():
    return get_db()["agent_runs"]


# ── Index creation ────────────────────────────────────────────────────────────

async def _ensure_indexes() -> None:
    db = get_db()

    # tenders — fast dashboard queries
    await db["tenders"].create_indexes([
        IndexModel([("tender_id", ASCENDING)], unique=True, name="tender_id_unique"),
        IndexModel([("relevance_score", DESCENDING)], name="score_desc"),
        IndexModel([("deadline", ASCENDING)], name="deadline_asc"),
        IndexModel([("status", ASCENDING)], name="status"),
        IndexModel([("country", ASCENDING)], name="country"),
        IndexModel([("source_portal", ASCENDING)], name="portal"),
        IndexModel([("enriched", ASCENDING)], name="enriched"),
    ])

    # users
    await db["users"].create_indexes([
        IndexModel([("email", ASCENDING)], unique=True, sparse=True, name="email_unique"),
    ])

    # portal_logs — for /health queries
    await db["portal_logs"].create_indexes([
        IndexModel([("portal", ASCENDING), ("run_at", DESCENDING)], name="portal_run_at"),
    ])

    # audit_logs - for security transparency
    await db["audit_logs"].create_indexes([
        IndexModel([("company_name", ASCENDING), ("accessed_at", DESCENDING)], name="company_audits"),
    ])

    # alerts — deduplication
    await db["alerts"].create_indexes([
        IndexModel(
            [("user_id", ASCENDING), ("tender_id", ASCENDING), ("alert_type", ASCENDING)],
            name="alert_dedup",
        ),
    ])

    # draft_queue — approval pipeline
    await db["draft_queue"].create_indexes([
        IndexModel([("tender_id", ASCENDING), ("company_name", ASCENDING)], unique=True, name="draft_queue_unique"),
        IndexModel([("status", ASCENDING)], name="draft_status"),
        IndexModel([("queued_at", DESCENDING)], name="draft_queued_at"),
    ])

    # bid_outcomes — feedback loop
    await db["bid_outcomes"].create_indexes([
        IndexModel([("tender_id", ASCENDING), ("company_name", ASCENDING)], unique=True, name="outcome_unique"),
        IndexModel([("agency", ASCENDING)], name="outcome_agency"),
        IndexModel([("category_code", ASCENDING)], name="outcome_category"),
    ])

    # agent_runs — live terminal
    await db["agent_runs"].create_indexes([
        IndexModel([("run_at", DESCENDING)], name="agent_run_at"),
        IndexModel([("agent_name", ASCENDING), ("run_at", DESCENDING)], name="agent_name_time"),
    ])

    logger.info("✅ MongoDB indexes ensured.")



# ── Handy upsert helper ───────────────────────────────────────────────────────

async def upsert_tender(tender_doc: dict) -> str:
    """Upsert a tender by tender_id. Returns 'inserted' or 'updated'."""
    result = await tenders_col().update_one(
        {"tender_id": tender_doc["tender_id"]},
        {"$set": tender_doc},
        upsert=True,
    )
    return "inserted" if result.upserted_id else "updated"


async def test_connection() -> bool:
    """Ping MongoDB — used in health endpoint."""
    try:
        await get_db().command("ping")
        return True
    except Exception:
        return False
