"""
Healing Repository - CRUD operations for healing logs
"""
from typing import List, Optional
from datetime import datetime

from src.database.db_manager import DatabaseManager
from src.utils.constants import HealingAction, HealingStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealingRepository:
    """Repository for healing action logs"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def log_healing_action(
        self,
        device_id: str,
        healing_action: HealingAction,
        anomaly_id: Optional[int] = None,
        metadata: Optional[str] = None
    ) -> int:
        """
        Log a new healing action
        
        Args:
            device_id: Device identifier
            healing_action: Type of healing action
            anomaly_id: Optional associated anomaly ID
            metadata: Optional JSON metadata
            
        Returns:
            Healing log ID
        """
        query = """
            INSERT INTO healing_logs (
                device_id, anomaly_id, healing_action, status,
                initiated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        parameters = (
            device_id,
            anomaly_id,
            healing_action.value,
            HealingStatus.PENDING.value,
            datetime.utcnow(),
            metadata
        )
        
        log_id = await self.db.execute_insert(query, parameters)
        logger.info(f"Logged healing action {log_id}: {healing_action.value} for device {device_id}")
        return log_id
    
    async def update_healing_status(
        self,
        log_id: int,
        status: HealingStatus,
        success: Optional[bool] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update healing action status
        
        Args:
            log_id: Healing log ID
            status: New status
            success: Whether action succeeded
            error_message: Optional error message
            
        Returns:
            True if updated, False otherwise
        """
        # Calculate duration if completing
        if status in [HealingStatus.SUCCESS, HealingStatus.FAILED, HealingStatus.TIMEOUT]:
            # Get initiated_at time
            query_time = "SELECT initiated_at FROM healing_logs WHERE id = ?"
            results = await self.db.execute_query(query_time, (log_id,))
            
            if results:
                initiated_at = datetime.fromisoformat(results[0]['initiated_at'])
                completed_at = datetime.utcnow()
                duration = (completed_at - initiated_at).total_seconds()
                
                query = """
                    UPDATE healing_logs 
                    SET status = ?, success = ?, error_message = ?,
                        completed_at = ?, duration_seconds = ?
                    WHERE id = ?
                """
                parameters = (status.value, success, error_message, completed_at, duration, log_id)
            else:
                return False
        else:
            query = """
                UPDATE healing_logs 
                SET status = ?, error_message = ?
                WHERE id = ?
            """
            parameters = (status.value, error_message, log_id)
        
        rows_affected = await self.db.execute_update(query, parameters)
        
        if rows_affected > 0:
            logger.info(f"Updated healing log {log_id} status to {status.value}")
            return True
        
        return False
    
    async def get_healing_log(self, log_id: int) -> Optional[dict]:
        """
        Get healing log by ID
        
        Args:
            log_id: Healing log ID
            
        Returns:
            Healing log record or None
        """
        query = "SELECT * FROM healing_logs WHERE id = ?"
        results = await self.db.execute_query(query, (log_id,))
        return results[0] if results else None
    
    async def get_healing_history(
        self,
        device_id: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Get healing action history
        
        Args:
            device_id: Optional device filter
            limit: Maximum number of records
            
        Returns:
            List of healing logs
        """
        if device_id:
            query = """
                SELECT * FROM healing_logs 
                WHERE device_id = ?
                ORDER BY initiated_at DESC 
                LIMIT ?
            """
            parameters = (device_id, limit)
        else:
            query = """
                SELECT * FROM healing_logs 
                ORDER BY initiated_at DESC 
                LIMIT ?
            """
            parameters = (limit,)
        
        return await self.db.execute_query(query, parameters)
    
    async def get_pending_actions(self) -> List[dict]:
        """
        Get pending healing actions
        
        Returns:
            List of pending healing logs
        """
        query = """
            SELECT * FROM healing_logs 
            WHERE status IN (?, ?)
            ORDER BY initiated_at ASC
        """
        
        parameters = (HealingStatus.PENDING.value, HealingStatus.IN_PROGRESS.value)
        return await self.db.execute_query(query, parameters)
    
    async def get_success_rate(
        self,
        device_id: Optional[str] = None,
        hours: int = 24
    ) -> dict:
        """
        Calculate healing success rate
        
        Args:
            device_id: Optional device filter
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with success rate statistics
        """
        if device_id:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
                FROM healing_logs 
                WHERE device_id = ?
                AND datetime(initiated_at, '+' || ? || ' hours') > datetime('now')
                AND status IN (?, ?)
            """
            parameters = (device_id, hours, HealingStatus.SUCCESS.value, HealingStatus.FAILED.value)
        else:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
                FROM healing_logs 
                WHERE datetime(initiated_at, '+' || ? || ' hours') > datetime('now')
                AND status IN (?, ?)
            """
            parameters = (hours, HealingStatus.SUCCESS.value, HealingStatus.FAILED.value)
        
        results = await self.db.execute_query(query, parameters)
        
        if results and results[0]['total'] > 0:
            total = results[0]['total']
            successful = results[0]['successful'] or 0
            return {
                'total': total,
                'successful': successful,
                'failed': results[0]['failed'] or 0,
                'success_rate': (successful / total) * 100 if total > 0 else 0
            }
        
        return {'total': 0, 'successful': 0, 'failed': 0, 'success_rate': 0}
    
    async def get_average_duration(
        self,
        healing_action: Optional[HealingAction] = None
    ) -> Optional[float]:
        """
        Get average healing action duration
        
        Args:
            healing_action: Optional action type filter
            
        Returns:
            Average duration in seconds or None
        """
        if healing_action:
            query = """
                SELECT AVG(duration_seconds) as avg_duration 
                FROM healing_logs 
                WHERE healing_action = ?
                AND duration_seconds IS NOT NULL
            """
            parameters = (healing_action.value,)
        else:
            query = """
                SELECT AVG(duration_seconds) as avg_duration 
                FROM healing_logs 
                WHERE duration_seconds IS NOT NULL
            """
            parameters = ()
        
        results = await self.db.execute_query(query, parameters)
        return results[0]['avg_duration'] if results and results[0]['avg_duration'] else None
