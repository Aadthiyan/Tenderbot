"""
TenderBot Global — WebSocket & Redis Pub/Sub Manager
Bridging Celery workers and FastAPI servers using Redis so React
gets real-time updates when background agents queue new drafts.
"""
import asyncio
import json
import logging
import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis = None
        self.pubsub_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WS client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WS client disconnected. Total: {len(self.active_connections)}")

    async def broadcast_local(self, message: dict):
        """Broadcast an event to all locally connected websockets."""
        if not self.active_connections:
            return
            
        json_msg = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_msg)
            except Exception:
                dead_connections.append(connection)
                
        for dead in dead_connections:
            self.disconnect(dead)

    async def start_redis_listener(self, redis_url: str):
        """Starts a background task listening to Redis 'tender_events'."""
        if self.redis is None:
            self.redis = aioredis.from_url(redis_url)
            pubsub = self.redis.pubsub()
            await pubsub.subscribe("tender_events")
            self.pubsub_task = asyncio.create_task(self._listen(pubsub))
            logger.info("📡 WS Redis listener started on channel: tender_events")

    async def _listen(self, pubsub):
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = message["data"].decode("utf-8")
                    try:
                        data = json.loads(payload)
                        await self.broadcast_local(data)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Redis WS listener error: {e}")

    async def close(self):
        if self.pubsub_task:
            self.pubsub_task.cancel()
        if self.redis:
            await self.redis.close()

manager = ConnectionManager()

# Synchronous + Asynchronous broadcasters for Celery & FastAPI
def publish_ws_event(event_type: str, payload_data: dict, redis_url: str):
    """
    Synchronous Redis publisher for use in standard functions (like Celery).
    """
    import redis
    try:
        r = redis.from_url(redis_url)
        event = {"type": event_type, "data": payload_data}
        r.publish("tender_events", json.dumps(event))
        r.close()
    except Exception as e:
        logger.warning(f"Failed to publish sync WS event: {e}")

async def async_publish_ws_event(event_type: str, payload_data: dict, redis_url: str):
    """
    Asynchronous Redis publisher for use in FastAPI route handlers.
    """
    try:
        r = aioredis.from_url(redis_url)
        event = {"type": event_type, "data": payload_data}
        await r.publish("tender_events", json.dumps(event))
        await r.close()
    except Exception as e:
        logger.warning(f"Failed to publish async WS event: {e}")
