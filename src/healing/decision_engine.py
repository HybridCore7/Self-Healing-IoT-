"""
Decision Engine - Root cause analysis and healing action selection
"""
from typing import List, Dict, Optional, Tuple

from src.utils.constants import AnomalyType, Severity, HealingAction
from src.healing.policies import get_healing_policies
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """Analyzes anomalies and selects appropriate healing actions"""
    
    def __init__(self):
        self.policies = get_healing_policies()
        logger.info("Initialized decision engine")
    
    def analyze_anomaly(
        self,
        device_id: str,
        anomaly_type: AnomalyType,
        sensor_type: Optional[str] = None,
        anomaly_score: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[str, Severity, List[HealingAction]]:
        """
        Analyze anomaly and determine healing strategy
        
        Args:
            device_id: Device identifier
            anomaly_type: Type of anomaly
            sensor_type: Sensor type if applicable
            anomaly_score: Anomaly score (0-1)
            metadata: Additional context
            
        Returns:
            Tuple of (fault_type, severity, recommended_actions)
        """
        # Map anomaly type to fault type
        fault_type = self._map_anomaly_to_fault(anomaly_type, metadata)
        
        # Get policy for fault type
        policy = self.policies.get_policy(fault_type)
        
        if not policy:
            logger.warning(f"No policy found for fault type: {fault_type}")
            return fault_type, Severity.MEDIUM, []
        
        # Get severity
        severity_str = policy.get('severity', 'medium')
        severity = Severity(severity_str)
        
        # Get recommended actions
        actions_config = policy.get('actions', [])
        recommended_actions = self._select_actions(
            actions_config,
            device_id,
            metadata or {}
        )
        
        logger.info(f"Analyzed anomaly for {device_id}: fault={fault_type}, severity={severity.value}, actions={len(recommended_actions)}")
        
        return fault_type, severity, recommended_actions
    
    def _map_anomaly_to_fault(
        self,
        anomaly_type: AnomalyType,
        metadata: Optional[Dict]
    ) -> str:
        """Map anomaly type to fault type from policies"""
        # Direct mapping
        mapping = {
            AnomalyType.SENSOR_FAULT: 'sensor_anomaly',
            AnomalyType.SENSOR_DRIFT: 'sensor_drift',
            AnomalyType.OUT_OF_RANGE: 'sensor_anomaly',
            AnomalyType.STUCK_VALUE: 'sensor_anomaly',
            AnomalyType.SUDDEN_SPIKE: 'sensor_anomaly',
            AnomalyType.COMMUNICATION_ERROR: 'communication_failure'
        }
        
        fault_type = mapping.get(anomaly_type, 'sensor_anomaly')
        
        # Check for device offline condition
        if metadata and metadata.get('device_offline'):
            fault_type = 'device_offline'
        
        return fault_type
    
    def _select_actions(
        self,
        actions_config: List[Dict],
        device_id: str,
        metadata: Dict
    ) -> List[HealingAction]:
        """
        Select applicable actions based on conditions
        
        Args:
            actions_config: List of action configurations
            device_id: Device identifier
            metadata: Context metadata
            
        Returns:
            List of healing actions
        """
        selected_actions = []
        
        for action_config in actions_config:
            action_name = action_config.get('action')
            conditions = action_config.get('conditions', [])
            
            # Check if all conditions are met
            if self._check_conditions(conditions, metadata):
                try:
                    action = HealingAction(action_name)
                    selected_actions.append(action)
                except ValueError:
                    logger.warning(f"Unknown healing action: {action_name}")
        
        # Sort by priority
        actions_config_dict = {ac['action']: ac for ac in actions_config}
        selected_actions.sort(
            key=lambda a: actions_config_dict.get(a.value, {}).get('priority', 999)
        )
        
        return selected_actions
    
    def _check_conditions(
        self,
        conditions: List[Dict],
        metadata: Dict
    ) -> bool:
        """
        Check if all conditions are met
        
        Args:
            conditions: List of condition dictionaries
            metadata: Context metadata
            
        Returns:
            True if all conditions met
        """
        if not conditions:
            return True
        
        for condition in conditions:
            for key, expected_value in condition.items():
                actual_value = metadata.get(key)
                
                if actual_value != expected_value:
                    return False
        
        return True
    
    def get_next_action(
        self,
        fault_type: str,
        attempted_actions: List[HealingAction]
    ) -> Optional[HealingAction]:
        """
        Get next action to try based on previous attempts
        
        Args:
            fault_type: Type of fault
            attempted_actions: Actions already attempted
            
        Returns:
            Next action to try or None
        """
        policy = self.policies.get_policy(fault_type)
        
        if not policy:
            return None
        
        actions_config = policy.get('actions', [])
        
        # Find first action not yet attempted
        for action_config in sorted(actions_config, key=lambda x: x.get('priority', 999)):
            action_name = action_config.get('action')
            
            try:
                action = HealingAction(action_name)
                if action not in attempted_actions:
                    return action
            except ValueError:
                continue
        
        return None
    
    def should_escalate(
        self,
        fault_type: str,
        attempt_count: int,
        severity: Severity
    ) -> bool:
        """
        Determine if fault should be escalated
        
        Args:
            fault_type: Type of fault
            attempt_count: Number of healing attempts
            severity: Fault severity
            
        Returns:
            True if should escalate
        """
        max_attempts = self.policies.get_max_attempts(fault_type)
        
        # Escalate if max attempts reached
        if attempt_count >= max_attempts:
            return True
        
        # Escalate critical faults faster
        if severity == Severity.CRITICAL and attempt_count >= 2:
            return True
        
        return False


# Global decision engine instance
_decision_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Get global decision engine instance"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine
