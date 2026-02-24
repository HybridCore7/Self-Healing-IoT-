"""
Pydantic models for anomaly detection
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from src.utils.constants import AnomalyType, Severity


class AnomalyBase(BaseModel):
    """Base anomaly model"""
    device_id: str = Field(..., description="Device identifier")
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly")
    severity: Severity = Field(..., description="Severity level")
    sensor_type: Optional[str] = Field(None, description="Sensor type if applicable")
    description: Optional[str] = Field(None, description="Anomaly description")


class AnomalyCreate(AnomalyBase):
    """Model for creating anomaly"""
    anomaly_score: Optional[float] = Field(None, ge=0, le=1, description="Anomaly score (0-1)")


class AnomalyUpdate(BaseModel):
    """Model for updating anomaly"""
    is_resolved: Optional[bool] = None
    resolved_at: Optional[datetime] = None


class AnomalyResponse(AnomalyBase):
    """Model for anomaly response"""
    id: int
    anomaly_score: Optional[float] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool
    
    class Config:
        from_attributes = True


class AnomalyStats(BaseModel):
    """Model for anomaly statistics"""
    total_anomalies: int = 0
    active_anomalies: int = 0
    resolved_anomalies: int = 0
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
