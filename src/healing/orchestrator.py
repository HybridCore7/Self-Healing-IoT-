"""
Healing Orchestrator - Main coordinator for self-healing system
Monitors anomalies and triggers healing workflows
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from src.database.db_manager import get_db_manager
from src.database.repositories.anomaly_repo import AnomalyRepository
from src.database.repositories.healing_repo import HealingRepository
from src.healing.decision_engine import get_decision_engine
from src.healing.actions import get_action_executor
from src.healing.policies import get_healing_policies
from src.utils.constants import HealingStatus, HealingAction, AnomalyType, Severity
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealingOrchestrator:
    """Coordinates the self-healing process"""
    
    def __init__(self):
        self.decision_engine = get_decision_engine()
        self.action_executor = get_action_executor()
        self.policies = get_healing_policies()
        
        # Repositories
        self.anomaly_repo: Optional[AnomalyRepository] = None
        self.healing_repo: Optional[HealingRepository] = None
        
        # Tracking
        self.active_healings: Dict[str, Dict] = {}  # device_id -> healing info
        self.cooldown_tracker: Dict[str, datetime] = {}  # device_id -> cooldown_until
        
        # Running state
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        logger.info("Initialized healing orchestrator")
    
    async def initialize(self):
        """Initialize orchestrator with database connections"""
        db_manager = await get_db_manager()
        self.anomaly_repo = AnomalyRepository(db_manager)
        self.healing_repo = HealingRepository(db_manager)
        logger.info("Healing orchestrator initialized with database")
    
    async def start(self):
        """Start the healing orchestrator"""
        if self.running:
            logger.warning("Healing orchestrator already running")
            return
        
        if not self.anomaly_repo or not self.healing_repo:
            await self.initialize()
        
        self.running = True
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._monitor_anomalies()),
            asyncio.create_task(self._monitor_pending_actions())
        ]
        
        logger.info("Healing orchestrator started")
    
    async def stop(self):
        """Stop the healing orchestrator"""
        self.running = False
        
        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        
        logger.info("Healing orchestrator stopped")
    
    async def _monitor_anomalies(self):
        """Monitor for new anomalies and trigger healing"""
        while self.running:
            try:
                # Get active anomalies
                anomalies = await self.anomaly_repo.get_active_anomalies()
                
                for anomaly in anomalies:
                    device_id = anomaly['device_id']
                    anomaly_id = anomaly['id']
                    
                    # Skip if already being healed
                    if device_id in self.active_healings:
                        continue
                    
                    # Check cooldown
                    if self._is_in_cooldown(device_id):
                        continue
                    
                    # Trigger healing
                    asyncio.create_task(
                        self._heal_anomaly(anomaly)
                    )
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in anomaly monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_pending_actions(self):
        """Monitor pending healing actions"""
        while self.running:
            try:
                pending_actions = await self.healing_repo.get_pending_actions()
                
                # Clean up stale pending actions (older than 5 minutes)
                cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                
                for action in pending_actions:
                    initiated_at = datetime.fromisoformat(action['initiated_at'])
                    
                    if initiated_at < cutoff_time:
                        # Mark as timeout
                        await self.healing_repo.update_healing_status(
                            action['id'],
                            HealingStatus.TIMEOUT,
                            success=False,
                            error_message="Action timed out"
                        )
                
                await asyncio.sleep(30)  # Check every 30 seconds
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring pending actions: {e}")
                await asyncio.sleep(30)
    
    async def _heal_anomaly(self, anomaly: Dict):
        """
        Execute healing workflow for anomaly
        
        Args:
            anomaly: Anomaly record from database
        """
        device_id = anomaly['device_id']
        anomaly_id = anomaly['id']
        anomaly_type = AnomalyType(anomaly['anomaly_type'])
        
        logger.info(f"Starting healing workflow for anomaly {anomaly_id} on device {device_id}")
        
        # Mark as active
        self.active_healings[device_id] = {
            'anomaly_id': anomaly_id,
            'start_time': datetime.utcnow(),
            'attempts': 0,
            'attempted_actions': []
        }
        
        try:
            # Analyze anomaly and get healing strategy
            fault_type, severity, recommended_actions = self.decision_engine.analyze_anomaly(
                device_id,
                anomaly_type,
                sensor_type=anomaly.get('sensor_type'),
                anomaly_score=anomaly.get('anomaly_score')
            )
            
            max_attempts = self.policies.get_max_attempts(fault_type)
            
            # Try healing actions
            for action in recommended_actions:
                if self.active_healings[device_id]['attempts'] >= max_attempts:
                    logger.warning(f"Max healing attempts reached for device {device_id}")
                    break
                
                # Execute action
                success = await self._execute_healing_action(
                    device_id,
                    anomaly_id,
                    action
                )
                
                self.active_healings[device_id]['attempts'] += 1
                self.active_healings[device_id]['attempted_actions'].append(action)
                
                if success:
                    # Healing successful
                    logger.info(f"Healing successful for device {device_id} using {action.value}")
                    
                    # Resolve anomaly
                    await self.anomaly_repo.resolve_anomaly(anomaly_id)
                    break
                else:
                    logger.warning(f"Healing action {action.value} failed for device {device_id}")
            
            # Set cooldown
            cooldown_seconds = self.policies.get_cooldown(fault_type)
            self.cooldown_tracker[device_id] = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
        
        except Exception as e:
            logger.error(f"Error in healing workflow for device {device_id}: {e}")
        
        finally:
            # Remove from active healings
            if device_id in self.active_healings:
                del self.active_healings[device_id]
    
    async def _execute_healing_action(
        self,
        device_id: str,
        anomaly_id: int,
        action: HealingAction
    ) -> bool:
        """
        Execute single healing action
        
        Args:
            device_id: Device identifier
            anomaly_id: Anomaly ID
            action: Healing action to execute
            
        Returns:
            True if successful
        """
        # Log healing action
        log_id = await self.healing_repo.log_healing_action(
            device_id,
            action,
            anomaly_id=anomaly_id
        )
        
        # Update status to in progress
        await self.healing_repo.update_healing_status(
            log_id,
            HealingStatus.IN_PROGRESS
        )
        
        try:
            # Execute action
            success, error_message = await self.action_executor.execute_action(
                device_id,
                action
            )
            
            # Update status
            if success:
                await self.healing_repo.update_healing_status(
                    log_id,
                    HealingStatus.SUCCESS,
                    success=True
                )
            else:
                await self.healing_repo.update_healing_status(
                    log_id,
                    HealingStatus.FAILED,
                    success=False,
                    error_message=error_message
                )
            
            return success
        
        except Exception as e:
            error_message = str(e)
            await self.healing_repo.update_healing_status(
                log_id,
                HealingStatus.FAILED,
                success=False,
                error_message=error_message
            )
            return False
    
    def _is_in_cooldown(self, device_id: str) -> bool:
        """Check if device is in cooldown period"""
        if device_id not in self.cooldown_tracker:
            return False
        
        cooldown_until = self.cooldown_tracker[device_id]
        
        if datetime.utcnow() < cooldown_until:
            return True
        
        # Cooldown expired, remove from tracker
        del self.cooldown_tracker[device_id]
        return False
    
    async def trigger_manual_healing(
        self,
        device_id: str,
        action: HealingAction
    ) -> bool:
        """
        Manually trigger healing action
        
        Args:
            device_id: Device identifier
            action: Healing action to execute
            
        Returns:
            True if successful
        """
        logger.info(f"Manual healing triggered: {action.value} on device {device_id}")
        
        success, error_message = await self.action_executor.execute_action(
            device_id,
            action
        )
        
        # Log the action
        log_id = await self.healing_repo.log_healing_action(
            device_id,
            action
        )
        
        if success:
            await self.healing_repo.update_healing_status(
                log_id,
                HealingStatus.SUCCESS,
                success=True
            )
        else:
            await self.healing_repo.update_healing_status(
                log_id,
                HealingStatus.FAILED,
                success=False,
                error_message=error_message
            )
        
        return success
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            'running': self.running,
            'active_healings': len(self.active_healings),
            'devices_in_cooldown': len(self.cooldown_tracker),
            'active_healing_devices': list(self.active_healings.keys())
        }


# Global orchestrator instance
_orchestrator: Optional[HealingOrchestrator] = None


def get_healing_orchestrator() -> HealingOrchestrator:
    """Get global healing orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HealingOrchestrator()
    return _orchestrator
