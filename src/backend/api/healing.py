"""
Healing Actions API Endpoints
Handles self-healing operations and logs
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from src.database.db_manager import get_db_manager
from src.database.repositories.healing_repo import HealingRepository
from src.healing.orchestrator import get_healing_orchestrator
from src.utils.constants import HealingAction, HealingStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ManualHealingRequest(BaseModel):
    """Request model for manual healing trigger"""
    action: str
    parameters: Optional[dict] = None


@router.get("/logs")
async def get_healing_logs(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    status: Optional[str] = Query(None, description="Filter by healing status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs")
):
    """
    Get healing action logs with optional filtering
    
    - **device_id**: Filter logs for specific device
    - **status**: Filter by status (pending, in_progress, success, failed, timeout)
    - **limit**: Maximum number of logs to return
    """
    logger.info(f"Fetching healing logs: device={device_id}, status={status}, limit={limit}")
    
    try:
        db_manager = await get_db_manager()
        repo = HealingRepository(db_manager)
        
        # Get healing history
        logs = await repo.get_healing_history(device_id, limit)
        
        # Filter by status if provided
        if status:
            logs = [log for log in logs if log.get('status') == status]
        
        return {
            "count": len(logs),
            "logs": logs
        }
    
    except Exception as e:
        logger.error(f"Error fetching healing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{device_id}")
async def get_device_healing_logs(
    device_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of logs")
):
    """
    Get healing logs for a specific device
    """
    logger.info(f"Fetching healing logs for device: {device_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = HealingRepository(db_manager)
        
        logs = await repo.get_healing_history(device_id, limit)
        
        return {
            "device_id": device_id,
            "count": len(logs),
            "logs": logs
        }
    
    except Exception as e:
        logger.error(f"Error fetching device healing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_healing_statistics(
    device_id: Optional[str] = Query(None, description="Filter by device ID")
):
    """
    Get healing statistics
    
    Returns overall or device-specific healing statistics including:
    - Total healing actions
    - Success/failure counts
    - Success rate
    - Average duration
    """
    logger.info(f"Fetching healing statistics for device: {device_id}")
    
    try:
        db_manager = await get_db_manager()
        repo = HealingRepository(db_manager)
        
        # Get success rate
        success_rate_data = await repo.get_success_rate(device_id)
        success_rate = success_rate_data.get('success_rate', 0) if success_rate_data else 0
        
        # Get recent logs for additional stats
        logs = await repo.get_healing_history(device_id, limit=1000)
        
        total_actions = len(logs)
        successful = sum(1 for log in logs if log.get('success') is True)
        failed = sum(1 for log in logs if log.get('success') is False)
        pending = sum(1 for log in logs if log.get('status') in ['pending', 'in_progress'])
        
        # Calculate average duration
        durations = [log.get('duration_seconds', 0) for log in logs if log.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Group by action type
        action_counts = {}
        for log in logs:
            action = log.get('healing_action')
            if action:
                action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "device_id": device_id,
            "total_actions": total_actions,
            "successful_actions": successful,
            "failed_actions": failed,
            "pending_actions": pending,
            "success_rate": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "actions_by_type": action_counts
        }
    
    except Exception as e:
        logger.error(f"Error fetching healing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_healings():
    """
    Get currently active healing workflows
    """
    logger.info("Fetching active healing workflows")
    
    try:
        orchestrator = get_healing_orchestrator()
        status = orchestrator.get_status()
        
        # Get pending actions from database
        db_manager = await get_db_manager()
        repo = HealingRepository(db_manager)
        pending_actions = await repo.get_pending_actions()
        
        return {
            "orchestrator_running": status['running'],
            "active_healing_count": status['active_healings'],
            "devices_in_cooldown": status['devices_in_cooldown'],
            "active_devices": status['active_healing_devices'],
            "pending_actions": pending_actions
        }
    
    except Exception as e:
        logger.error(f"Error fetching active healings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/{device_id}")
async def trigger_manual_healing(
    device_id: str,
    request: ManualHealingRequest
):
    """
    Manually trigger a healing action for a device
    
    - **device_id**: Target device identifier
    - **action**: Healing action to execute (e.g., "reset", "restart", "calibrate")
    - **parameters**: Optional action parameters
    """
    logger.info(f"Manual healing triggered for device: {device_id}, action: {request.action}")
    
    try:
        # Validate action
        try:
            action_enum = HealingAction(request.action)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid healing action: {request.action}"
            )
        
        # Trigger healing via orchestrator
        orchestrator = get_healing_orchestrator()
        success = await orchestrator.trigger_manual_healing(device_id, action_enum)
        
        if success:
            return {
                "success": True,
                "message": "Healing action triggered successfully",
                "device_id": device_id,
                "action": request.action
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to execute healing action"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual healing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions")
async def list_available_actions():
    """
    List all available healing actions
    """
    actions = [
        {
            "action": action.value,
            "description": action.name.replace('_', ' ').title()
        }
        for action in HealingAction
    ]
    
    return {
        "count": len(actions),
        "actions": actions
    }
