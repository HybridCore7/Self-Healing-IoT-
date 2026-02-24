"""
Anomaly Repository - CRUD operations for anomalies table
"""
from typing import List, Optional
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.utils.constants import AnomalyType, Severity
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyRepository:
    """Repository for anomaly data operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_anomaly(
        self,
        device_id: str,
        anomaly_type: AnomalyType,
        severity: Severity,
        sensor_type: Optional[str] = None,
        anomaly_score: Optional[float] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Create a new anomaly record
        
        Args:
            device_id: Device identifier
            anomaly_type: Type of anomaly
            severity: Severity level
            sensor_type: Optional sensor type
            anomaly_score: Optional anomaly score
            description: Optional description
            
        Returns:
            Created anomaly ID
        """
        query = """
            INSERT INTO anomalies (
                device_id, anomaly_type, severity, sensor_type,
                anomaly_score, description, detected_at, is_resolved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """
        
        parameters = (
            device_id,
            anomaly_type.value,
            severity.value,
            sensor_type,
            anomaly_score,
            description,
            datetime.utcnow()
        )
        
        anomaly_id = await self.db.execute_insert(query, parameters)
        logger.info(f"Created anomaly {anomaly_id} for device {device_id}: {anomaly_type.value}")
        return anomaly_id
    
    async def get_anomaly(self, anomaly_id: int) -> Optional[dict]:
        """
        Get anomaly by ID
        
        Args:
            anomaly_id: Anomaly identifier
            
        Returns:
            Anomaly record or None
        """
        query = "SELECT * FROM anomalies WHERE id = ?"
        results = await self.db.execute_query(query, (anomaly_id,))
        return results[0] if results else None
    
    async def get_active_anomalies(
        self,
        device_id: Optional[str] = None,
        severity: Optional[Severity] = None
    ) -> List[dict]:
        """
        Get active (unresolved) anomalies
        
        Args:
            device_id: Optional device filter
            severity: Optional severity filter
            
        Returns:
            List of active anomalies
        """
        conditions = ["is_resolved = 0"]
        parameters = []
        
        if device_id:
            conditions.append("device_id = ?")
            parameters.append(device_id)
        
        if severity:
            conditions.append("severity = ?")
            parameters.append(severity.value)
        
        query = f"""
            SELECT * FROM anomalies 
            WHERE {' AND '.join(conditions)}
            ORDER BY detected_at DESC
        """
        
        return await self.db.execute_query(query, tuple(parameters))
    
    async def resolve_anomaly(
        self,
        anomaly_id: int,
        resolved_at: Optional[datetime] = None
    ) -> bool:
        """
        Mark anomaly as resolved
        
        Args:
            anomaly_id: Anomaly identifier
            resolved_at: Resolution timestamp (defaults to now)
            
        Returns:
            True if updated, False otherwise
        """
        if resolved_at is None:
            resolved_at = datetime.utcnow()
        
        query = """
            UPDATE anomalies 
            SET is_resolved = 1, resolved_at = ?
            WHERE id = ?
        """
        
        rows_affected = await self.db.execute_update(query, (resolved_at, anomaly_id))
        
        if rows_affected > 0:
            logger.info(f"Resolved anomaly {anomaly_id}")
            return True
        
        return False
    
    async def get_anomaly_history(
        self,
        device_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get anomaly history for a device
        
        Args:
            device_id: Device identifier
            limit: Maximum number of records
            
        Returns:
            List of anomalies
        """
        query = """
            SELECT * FROM anomalies 
            WHERE device_id = ?
            ORDER BY detected_at DESC 
            LIMIT ?
        """
        
        return await self.db.execute_query(query, (device_id, limit))
    
    async def get_anomaly_count_by_type(self, hours: int = 24) -> dict:
        """
        Get anomaly count grouped by type
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with anomaly type counts
        """
        query = """
            SELECT anomaly_type, COUNT(*) as count 
            FROM anomalies 
            WHERE datetime(detected_at, '+' || ? || ' hours') > datetime('now')
            GROUP BY anomaly_type
        """
        
        results = await self.db.execute_query(query, (hours,))
        return {row['anomaly_type']: row['count'] for row in results}
    
    async def get_anomaly_count_by_severity(self) -> dict:
        """
        Get anomaly count grouped by severity
        
        Returns:
            Dictionary with severity counts
        """
        query = """
            SELECT severity, COUNT(*) as count 
            FROM anomalies 
            WHERE is_resolved = 0
            GROUP BY severity
        """
        
        results = await self.db.execute_query(query)
        return {row['severity']: row['count'] for row in results}
    
    async def get_recent_anomalies(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[dict]:
        """
        Get recent anomalies across all devices
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records
            
        Returns:
            List of recent anomalies
        """
        query = """
            SELECT * FROM anomalies 
            WHERE datetime(detected_at, '+' || ? || ' hours') > datetime('now')
            ORDER BY detected_at DESC 
            LIMIT ?
        """
        
        return await self.db.execute_query(query, (hours, limit))
    
    # Alias methods for API compatibility
    async def get_anomaly_counts_by_severity(self) -> dict:
        """Alias for get_anomaly_count_by_severity (plural form)"""
        return await self.get_anomaly_count_by_severity()
    
    async def get_anomaly_counts_by_type(self, hours: int = 24) -> dict:
        """Alias for get_anomaly_count_by_type (plural form)"""
        return await self.get_anomaly_count_by_type(hours)
