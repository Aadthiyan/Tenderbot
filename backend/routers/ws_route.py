from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.ws import manager
import logging

router = APIRouter(tags=["WebSockets"])
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, though TenderBot is uni-directional server-to-client
            data = await websocket.receive_text()
            # We don't expect client messages for now
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
