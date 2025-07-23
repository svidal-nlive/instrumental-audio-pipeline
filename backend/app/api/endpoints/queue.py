from fastapi import APIRouter, Request, HTTPException, WebSocket
from typing import List
import asyncio
from ...models.schemas import QueueItem, QueueStatus
from ...services.queue_manager import QueueManager

router = APIRouter()


@router.get("/", response_model=List[QueueItem])
async def get_queue(request: Request):
    """Get current queue status"""
    queue_manager: QueueManager = request.app.state.queue_manager
    queue_items = await queue_manager.get_queue()
    return queue_items


@router.get("/status", response_model=QueueStatus)
async def get_queue_status(request: Request):
    """Get queue statistics"""
    queue_manager: QueueManager = request.app.state.queue_manager
    status = await queue_manager.get_status()
    return status


@router.post("/pause")
async def pause_queue(request: Request):
    """Pause queue processing"""
    queue_manager: QueueManager = request.app.state.queue_manager
    await queue_manager.pause()
    return {"message": "Queue paused"}


@router.post("/resume")
async def resume_queue(request: Request):
    """Resume queue processing"""
    queue_manager: QueueManager = request.app.state.queue_manager
    await queue_manager.resume()
    return {"message": "Queue resumed"}


@router.post("/clear")
async def clear_queue(request: Request):
    """Clear the queue (remove pending items)"""
    queue_manager: QueueManager = request.app.state.queue_manager
    await queue_manager.clear()
    return {"message": "Queue cleared"}


@router.delete("/{item_id}")
async def remove_queue_item(request: Request, item_id: str):
    """Remove a specific item from the queue"""
    queue_manager: QueueManager = request.app.state.queue_manager
    success = await queue_manager.remove_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return {"message": "Item removed from queue"}


@router.post("/{item_id}/priority")
async def set_item_priority(request: Request, item_id: str, priority: int):
    """Set priority for a queue item"""
    queue_manager: QueueManager = request.app.state.queue_manager
    success = await queue_manager.set_priority(item_id, priority)
    if not success:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return {"message": "Priority updated"}


@router.websocket("/events")
async def queue_events_websocket(websocket):
    """WebSocket endpoint for real-time queue updates"""
    await websocket.accept()
    
    try:
        # This would integrate with your queue manager's event system
        # For now, send periodic updates
        while True:
            # Send queue status updates
            # Implementation would depend on your event system
            await asyncio.sleep(1)
            
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
