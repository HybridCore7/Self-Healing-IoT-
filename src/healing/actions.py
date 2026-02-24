"""
Healing Actions - Execute healing actions on devices
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from src.mqtt.publisher import get_publisher
from src.utils.constants import HealingAction
from src.utils.logger import get_logger
from src.healing.policies import get_healing_policies

logger = get_logger(__name__)


class HealingActionExecutor:
    """Executes healing actions on devices"""
    
    def __init__(self):
        self.publisher = get_publisher()
        self.policies = get_healing_policies()
        logger.info("Initialized healing action executor")
    
    async def execute_action(
        self,
        device_id: str,
        action: HealingAction,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> tuple[bool, Optional[str]]:
        """
        Execute healing action on device
        
        Args:
            device_id: Device identifier
            action: Healing action to execute
            parameters: Action parameters
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Executing {action.value} on device {device_id}")
        
        # Get action configuration from policies
        action_config = self.policies.get_action_config(action.value)
        
        if action_config:
            command = action_config.get('command', action.value)
            default_params = action_config.get('parameters', {})
            
            # Merge parameters
            if parameters:
                params = {**default_params, **parameters}
            else:
                params = default_params
        else:
            command = action.value
            params = parameters or {}
        
        # Execute specific action
        try:
            if action == HealingAction.VALIDATE_READING:
                return await self._validate_reading(device_id, params, timeout)
            
            elif action == HealingAction.SWITCH_SENSOR:
                return await self._switch_sensor(device_id, params, timeout)
            
            elif action == HealingAction.RESET_SENSOR:
                return await self._reset_sensor(device_id, params, timeout)
            
            elif action == HealingAction.RESTART_DEVICE:
                return await self._restart_device(device_id, params, timeout)
            
            elif action == HealingAction.ISOLATE_DEVICE:
                return await self._isolate_device(device_id, params, timeout)
            
            elif action == HealingAction.CALIBRATE_SENSOR:
                return await self._calibrate_sensor(device_id, params, timeout)
            
            elif action == HealingAction.RECONNECT_MQTT:
                return await self._reconnect_mqtt(device_id, params, timeout)
            
            elif action == HealingAction.PING_DEVICE:
                return await self._ping_device(device_id, params, timeout)
            
            else:
                return await self._generic_action(device_id, command, params, timeout)
        
        except asyncio.TimeoutError:
            error_msg = f"Action {action.value} timed out after {timeout}s"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Error executing {action.value}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def _validate_reading(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Request device to validate sensor reading"""
        success = self.publisher.publish_command(
            device_id,
            'validate',
            parameters=params
        )
        
        if success:
            # Wait for validation
            await asyncio.sleep(params.get('interval', 2) * params.get('sample_count', 5))
            return True, None
        
        return False, "Failed to send validation command"
    
    async def _switch_sensor(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Switch to backup sensor"""
        success = self.publisher.publish_command(
            device_id,
            'switch_sensor',
            parameters=params
        )
        
        if success:
            await asyncio.sleep(2)
            return True, None
        
        return False, "Failed to send switch sensor command"
    
    async def _reset_sensor(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Reset sensor to default state"""
        success = self.publisher.publish_command(
            device_id,
            'reset',
            parameters=params
        )
        
        if success:
            await asyncio.sleep(3)
            return True, None
        
        return False, "Failed to send reset command"
    
    async def _restart_device(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Restart the device"""
        success = self.publisher.publish_command(
            device_id,
            'restart',
            parameters=params
        )
        
        if success:
            # Wait for device to restart
            await asyncio.sleep(min(timeout, 30))
            return True, None
        
        return False, "Failed to send restart command"
    
    async def _isolate_device(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Isolate device from network"""
        success = self.publisher.publish_command(
            device_id,
            'isolate',
            parameters=params
        )
        
        if success:
            logger.warning(f"Device {device_id} isolated for {params.get('duration', 300)}s")
            return True, None
        
        return False, "Failed to send isolate command"
    
    async def _calibrate_sensor(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Calibrate sensor"""
        success = self.publisher.publish_command(
            device_id,
            'calibrate',
            parameters=params
        )
        
        if success:
            await asyncio.sleep(10)
            return True, None
        
        return False, "Failed to send calibrate command"
    
    async def _reconnect_mqtt(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Reconnect device to MQTT broker"""
        success = self.publisher.publish_command(
            device_id,
            'reconnect',
            parameters=params
        )
        
        if success:
            await asyncio.sleep(5)
            return True, None
        
        return False, "Failed to send reconnect command"
    
    async def _ping_device(
        self,
        device_id: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Ping device to check connectivity"""
        success = self.publisher.publish_command(
            device_id,
            'ping',
            parameters=params
        )
        
        if success:
            await asyncio.sleep(params.get('timeout', 5))
            return True, None
        
        return False, "Failed to send ping command"
    
    async def _generic_action(
        self,
        device_id: str,
        command: str,
        params: Dict,
        timeout: int
    ) -> tuple[bool, Optional[str]]:
        """Execute generic healing action"""
        success = self.publisher.publish_command(
            device_id,
            command,
            parameters=params
        )
        
        if success:
            await asyncio.sleep(min(timeout, 10))
            return True, None
        
        return False, f"Failed to send {command} command"


# Global executor instance
_executor: Optional[HealingActionExecutor] = None


def get_action_executor() -> HealingActionExecutor:
    """Get global healing action executor"""
    global _executor
    if _executor is None:
        _executor = HealingActionExecutor()
    return _executor
