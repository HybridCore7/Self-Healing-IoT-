"""
Telemetry Repository - CRUD operations for telemetry data
"""
from typing import List, Optional
from datetime import datetime, timedelta

from src.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelemetryRepository:
    """Repository for telemetry data operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def insert_telemetry(
        self,
        device_id: str,
        sensor_type: str,
        sensor_value: float,
        unit: Optional[str] = None,
        is_anomaly: bool = False,
        original_value: Optional[float] = None
    ) -> int:
        """
        Insert telemetry data
        
        Args:
            device_id: Device identifier
            sensor_type: Type of sensor
            sensor_value: Sensor reading value
            unit: Unit of measurement
            is_anomaly: Whether this reading is anomalous
            
        Returns:
            Inserted row ID
        """
        query = """
            INSERT INTO telemetry (
                device_id, sensor_type, sensor_value, unit, 
                timestamp, is_anomaly, original_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        parameters = (
            device_id,
            sensor_type,
            sensor_value,
            unit,
            datetime.utcnow(),
            1 if is_anomaly else 0,
            original_value
        )
        
        row_id = await self.db.execute_insert(query, parameters)
        return row_id
    
    async def get_recent_telemetry(
        self,
        device_id: str,
        sensor_type: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Get recent telemetry data for a device
        
        Args:
            device_id: Device identifier
            sensor_type: Optional sensor type filter
            limit: Maximum number of records
            
        Returns:
            List of telemetry records
        """
        if sensor_type:
            query = """
                SELECT * FROM telemetry 
                WHERE device_id = ? AND sensor_type = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            parameters = (device_id, sensor_type, limit)
        else:
            query = """
                SELECT * FROM telemetry 
                WHERE device_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            parameters = (device_id, limit)
        
        return await self.db.execute_query(query, parameters)
    
    async def get_telemetry_range(
        self,
        device_id: str,
        sensor_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[dict]:
        """
        Get telemetry data within time range
        
        Args:
            device_id: Device identifier
            sensor_type: Sensor type
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of telemetry records
        """
        query = """
            SELECT * FROM telemetry 
            WHERE device_id = ? 
            AND sensor_type = ?
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """
        
        parameters = (device_id, sensor_type, start_time, end_time)
        return await self.db.execute_query(query, parameters)
    
    async def get_anomalous_telemetry(
        self,
        device_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[dict]:
        """
        Get anomalous telemetry data
        
        Args:
            device_id: Optional device filter
            hours: Number of hours to look back
            limit: Maximum number of records
            
        Returns:
            List of anomalous telemetry records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if device_id:
            query = """
                SELECT * FROM telemetry 
                WHERE device_id = ? 
                AND is_anomaly = 1 
                AND timestamp > ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            parameters = (device_id, cutoff_time, limit)
        else:
            query = """
                SELECT * FROM telemetry 
                WHERE is_anomaly = 1 
                AND timestamp > ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            parameters = (cutoff_time, limit)
        
        return await self.db.execute_query(query, parameters)
    
    async def mark_as_anomaly(self, telemetry_id: int) -> bool:
        """
        Mark telemetry record as anomalous
        
        Args:
            telemetry_id: Telemetry record ID
            
        Returns:
            True if updated, False otherwise
        """
        query = "UPDATE telemetry SET is_anomaly = 1 WHERE id = ?"
        rows_affected = await self.db.execute_update(query, (telemetry_id,))
        return rows_affected > 0
    
    async def get_latest_value(
        self,
        device_id: str,
        sensor_type: str
    ) -> Optional[dict]:
        """
        Get latest telemetry value for a sensor
        
        Args:
            device_id: Device identifier
            sensor_type: Sensor type
            
        Returns:
            Latest telemetry record or None
        """
        query = """
            SELECT * FROM telemetry 
            WHERE device_id = ? AND sensor_type = ?
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        
        results = await self.db.execute_query(query, (device_id, sensor_type))
        return results[0] if results else None
    
    async def get_statistics(
        self,
        device_id: str,
        sensor_type: str,
        hours: int = 24
    ) -> dict:
        """
        Get statistical summary of telemetry data
        
        Args:
            device_id: Device identifier
            sensor_type: Sensor type
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with min, max, avg, count
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = """
            SELECT 
                MIN(sensor_value) as min_value,
                MAX(sensor_value) as max_value,
                AVG(sensor_value) as avg_value,
                COUNT(*) as count
            FROM telemetry 
            WHERE device_id = ? 
            AND sensor_type = ?
            AND timestamp > ?
        """
        
        results = await self.db.execute_query(query, (device_id, sensor_type, cutoff_time))
        return results[0] if results else {}
    
    async def delete_old_telemetry(self, days: int = 30) -> int:
        """
        Delete telemetry data older than specified days
        
        Args:
            days: Number of days to retain
            
        Returns:
            Number of deleted records
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        query = "DELETE FROM telemetry WHERE timestamp < ?"
        
        rows_affected = await self.db.execute_update(query, (cutoff_time,))
        logger.info(f"Deleted {rows_affected} old telemetry records")
        return rows_affected
