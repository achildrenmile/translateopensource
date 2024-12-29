# api/routers/websocket.py
from fastapi import APIRouter, WebSocket
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/translation-progress/{task_id}")
async def translation_progress_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            if task_id in router.translation_progress:
                await websocket.send_json(router.translation_progress[task_id])
                if router.translation_progress[task_id]["status"] in ["completed", "error"]:
                    break
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()