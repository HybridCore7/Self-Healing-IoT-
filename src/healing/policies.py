"""
Healing Policies - Load and manage healing policies from YAML configuration
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealingPolicies:
    """Manages healing policies loaded from YAML configuration"""
    
    def __init__(self, config_path: str = "config/healing_policies.yaml"):
        """
        Initialize healing policies
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.policies: Dict = {}
        self.actions: Dict = {}
        self.thresholds: Dict = {}
        self.validation: Dict = {}
        
        self.load_policies()
    
    def load_policies(self):
        """Load policies from YAML file"""
        if not self.config_path.exists():
            logger.error(f"Healing policies file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.policies = config.get('policies', {})
            self.actions = config.get('actions', {})
            self.thresholds = config.get('thresholds', {})
            self.validation = config.get('validation', {})
            
            logger.info(f"Loaded {len(self.policies)} healing policies from {self.config_path}")
        
        except Exception as e:
            logger.error(f"Error loading healing policies: {e}")
    
    def get_policy(self, fault_type: str) -> Optional[Dict]:
        """
        Get policy for fault type
        
        Args:
            fault_type: Type of fault
            
        Returns:
            Policy configuration or None
        """
        return self.policies.get(fault_type)
    
    def get_actions_for_fault(self, fault_type: str) -> List[Dict]:
        """
        Get healing actions for fault type
        
        Args:
            fault_type: Type of fault
            
        Returns:
            List of action configurations
        """
        policy = self.get_policy(fault_type)
        if policy:
            return policy.get('actions', [])
        return []
    
    def get_action_config(self, action_name: str) -> Optional[Dict]:
        """
        Get action configuration
        
        Args:
            action_name: Name of action
            
        Returns:
            Action configuration or None
        """
        return self.actions.get(action_name)
    
    def get_threshold(self, threshold_name: str) -> Optional[float]:
        """
        Get threshold value
        
        Args:
            threshold_name: Name of threshold
            
        Returns:
            Threshold value or None
        """
        return self.thresholds.get(threshold_name)
    
    def get_max_attempts(self, fault_type: str) -> int:
        """
        Get maximum healing attempts for fault type
        
        Args:
            fault_type: Type of fault
            
        Returns:
            Maximum attempts (default: 3)
        """
        policy = self.get_policy(fault_type)
        if policy:
            return policy.get('max_attempts', 3)
        return 3
    
    def get_cooldown(self, fault_type: str) -> int:
        """
        Get cooldown period for fault type
        
        Args:
            fault_type: Type of fault
            
        Returns:
            Cooldown in seconds (default: 60)
        """
        policy = self.get_policy(fault_type)
        if policy:
            return policy.get('cooldown', 60)
        return 60
    
    def get_severity(self, fault_type: str) -> str:
        """
        Get severity level for fault type
        
        Args:
            fault_type: Type of fault
            
        Returns:
            Severity level (default: 'medium')
        """
        policy = self.get_policy(fault_type)
        if policy:
            return policy.get('severity', 'medium')
        return 'medium'
    
    def list_fault_types(self) -> List[str]:
        """Get list of all configured fault types"""
        return list(self.policies.keys())
    
    def reload(self):
        """Reload policies from file"""
        logger.info("Reloading healing policies")
        self.load_policies()


# Global policies instance
_policies: Optional[HealingPolicies] = None


def get_healing_policies() -> HealingPolicies:
    """Get global healing policies instance"""
    global _policies
    if _policies is None:
        _policies = HealingPolicies()
    return _policies
