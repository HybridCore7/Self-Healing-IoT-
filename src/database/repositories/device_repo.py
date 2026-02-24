"""
Device Repository - CRUD operations for devices table
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.backend.models.device import Device, DeviceCreate, DeviceUpdate
from src.utils.constants import DeviceStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DeviceRepository:
    """Repository for device data operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_device(self, device: DeviceCreate) -> Device:
        """
        Create a new device
        
        Args:
            device: Device creation data
            
        Returns:
            Created device
        """
        query = """
            INSERT INTO devices (
                device_id, device_name, device_type, status, 
                ip_address, firmware_version, location, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.utcnow()
        parameters = (
            device.device_id,
            device.device_name,
            device.device_type,
            DeviceStatus.OFFLINE.value,
            device.ip_address,
            device.firmware_version,
            device.location,
            now,
            now
        )
        
        await self.db.execute_insert(query, parameters)
        logger.info(f"Created device: {device.device_id}")
        
        # Fetch and return the created device
        return await self.get_device(device.device_id)
    
    async def get_device(self, device_id: str) -> Optional[Device]:
        """
        Get device by ID
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device if found, None otherwise
        """
        query = "SELECT * FROM devices WHERE device_id = ?"
        results = await self.db.execute_query(query, (device_id,))
        
        if results:
            return Device(**results[0])
        return None
    
    async def list_devices(
        self, 
        status: Optional[DeviceStatus] = None, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Device]:
        """
        List devices with optional filtering
        
        Args:
            status: Filter by device status
            limit: Maximum number of devices to return
            offset: Number of devices to skip
            
        Returns:
            List of devices
        """
        if status:
            query = """
                SELECT * FROM devices 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            parameters = (status.value, limit, offset)
        else:
            query = """
                SELECT * FROM devices 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            parameters = (limit, offset)
        
        results = await self.db.execute_query(query, parameters)
        return [Device(**row) for row in results]
    
    async def update_device(
        self, 
        device_id: str, 
        device_update: DeviceUpdate
    ) -> Optional[Device]:
        """
        Update device information
        
        Args:
            device_id: Device identifier
            device_update: Fields to update
            
        Returns:
            Updated device if found, None otherwise
        """
        # Build dynamic update query based on provided fields
        update_fields = []
        parameters = []
        
        update_data = device_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                if isinstance(value, DeviceStatus):
                    parameters.append(value.value)
                else:
                    parameters.append(value)
        
        if not update_fields:
            return await self.get_device(device_id)
        
        # Add updated_at timestamp
        update_fields.append("updated_at = ?")
        parameters.append(datetime.utcnow())
        
        # Add device_id for WHERE clause
        parameters.append(device_id)
        
        query = f"""
            UPDATE devices 
            SET {', '.join(update_fields)}
            WHERE device_id = ?
        """
        
        rows_affected = await self.db.execute_update(query, tuple(parameters))
        
        if rows_affected > 0:
            logger.info(f"Updated device: {device_id}")
            return await self.get_device(device_id)
        
        return None
    
    async def delete_device(self, device_id: str) -> bool:
        """
        Delete a device
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if deleted, False otherwise
        """
        query = "DELETE FROM devices WHERE device_id = ?"
        rows_affected = await self.db.execute_update(query, (device_id,))
        
        if rows_affected > 0:
            logger.info(f"Deleted device: {device_id}")
            return True
        
        return False
    
    async def update_heartbeat(self, device_id: str) -> bool:
        """
        Update device heartbeat timestamp
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if updated, False otherwise
        """
        query = """
            UPDATE devices 
            SET last_heartbeat = ?, status = ?, updated_at = ?
            WHERE device_id = ?
        """
        now = datetime.utcnow()
        parameters = (now, DeviceStatus.ONLINE.value, now, device_id)
        
        rows_affected = await self.db.execute_update(query, parameters)
        return rows_affected > 0
    
    async def get_offline_devices(self, timeout_seconds: int = 30) -> List[Device]:
        """
        Get devices that haven't sent heartbeat within timeout
        
        Args:
            timeout_seconds: Heartbeat timeout in seconds
            
        Returns:
            List of offline devices
        """
        query = """
            SELECT * FROM devices 
            WHERE status = ? 
            AND (
                last_heartbeat IS NULL 
                OR datetime(last_heartbeat, '+' || ? || ' seconds') < datetime('now')
            )
        """
        parameters = (DeviceStatus.ONLINE.value, timeout_seconds)
        results = await self.db.execute_query(query, parameters)
        
        return [Device(**row) for row in results]
    
    async def get_device_count(self) -> Dict[str, int]:
        """
        Get device count by status
        
        Returns:
            Dictionary with status counts
        """
        query = """
            SELECT status, COUNT(*) as count 
            FROM devices 
            GROUP BY status
        """
        results = await self.db.execute_query(query)
        
        return {row['status']: row['count'] for row in results}
