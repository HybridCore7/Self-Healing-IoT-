"""
Pydantic models for healing actions
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from src.utils.constants import HealingAction, HealingStatus


class HealingActionBase(BaseModel):
    """Base healing action model"""
    device_id: str = Field(..., description="Device identifier")
    healing_action: HealingAction = Field(..., description="Type of healing action")
    anomaly_id: Optional[int] = Field(None, description="Associated anomaly ID")


class HealingActionCreate(HealingActionBase):
    """Model for creating healing action"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HealingActionUpdate(BaseModel):
    """Model for updating healing action"""
    status: HealingStatus
    success: Optional[bool] = None
    error_message: Optional[str] = None


class HealingActionResponse(HealingActionBase):
    """Model for healing action response"""
    id: int
    status: HealingStatus
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Optional[str] = None
    
    class Config:
        from_attributes = True


class HealingCommand(BaseModel):
    """Model for healing command to device"""
    device_id: str
    command: str
    parameters: Dict[str, Any] = {}
    timeout: int = 30


class HealingStats(BaseModel):
    """Model for healing statistics"""
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    pending_actions: int = 0
    success_rate: float = 0.0
    average_duration: Optional[float] = None
