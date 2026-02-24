"""
Device Management API Endpoints
Handles device registration, status, and configuration
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from src.backend.models.device import Device, DeviceCreate, DeviceUpdate
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[Device])
async def get_devices(
    status: Optional[str] = Query(None, description="Filter by device status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of devices to return")
):
    """
    Get list of all registered IoT devices
    
    Query Parameters:
    - status: Filter by device status (online, offline, isolated, etc.)
    - limit: Maximum number of devices to return
    """
    logger.info(f"Fetching devices with status={status}, limit={limit}")
    
    try:
        from src.database.db_manager import get_db_manager
        from src.database.repositories.device_repo import DeviceRepository
        from src.utils.constants import DeviceStatus
        
        db_manager = await get_db_manager()
        repo = DeviceRepository(db_manager)
        
        device_status = DeviceStatus(status) if status else None
        devices = await repo.list_devices(device_status, limit)
        return devices
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str):
    """
    Get details of a specific device by ID
    """
    logger.info(f"Fetching device: {device_id}")
    
    try:
        from src.database.db_manager import get_db_manager
        from src.database.repositories.device_repo import DeviceRepository
        
        db_manager = await get_db_manager()
        repo = DeviceRepository(db_manager)
        
        device = await repo.get_device(device_id)
        if device:
            return device
        raise HTTPException(status_code=404, detail="Device not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Device, status_code=201)
async def register_device(device: DeviceCreate):
    """
    Register a new IoT device in the system
    """
    logger.info(f"Registering new device: {device.device_id}")
    
    try:
        from src.database.db_manager import get_db_manager
        from src.database.repositories.device_repo import DeviceRepository
        
        db_manager = await get_db_manager()
        repo = DeviceRepository(db_manager)
        
        created_device = await repo.create_device(device)
        return created_device
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{device_id}", response_model=Device)
async def update_device(device_id: str, device_update: DeviceUpdate):
    """
    Update device information
    """
    logger.info(f"Updating device: {device_id}")
    
    try:
        from src.database.db_manager import get_db_manager
        from src.database.repositories.device_repo import DeviceRepository
        
        db_manager = await get_db_manager()
        repo = DeviceRepository(db_manager)
        
        updated_device = await repo.update_device(device_id, device_update)
        if updated_device:
            return updated_device
        raise HTTPException(status_code=404, detail="Device not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: str):
    """
    Remove a device from the system
    """
    logger.info(f"Deleting device: {device_id}")
    
    try:
        from src.database.db_manager import get_db_manager
        from src.database.repositories.device_repo import DeviceRepository
        
        db_manager = await get_db_manager()
        repo = DeviceRepository(db_manager)
        
        deleted = await repo.delete_device(device_id)
        if deleted:
            return
        raise HTTPException(status_code=404, detail="Device not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/status")
async def get_device_status(device_id: str):
    """
    Get current status and health of a device
    """
    logger.info(f"Fetching status for device: {device_id}")
    
    try:
        from src.database.db_manager import get_db_manager
        from src.database.repositories.device_repo import DeviceRepository
        
        db_manager = await get_db_manager()
        repo = DeviceRepository(db_manager)
        
        device = await repo.get_device(device_id)
        if device:
            return {
                "device_id": device.device_id,
                "status": device.status.value,
                "last_heartbeat": device.last_heartbeat,
                "device_name": device.device_name
            }
        raise HTTPException(status_code=404, detail="Device not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching device status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
