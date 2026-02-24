"""
Pydantic models for telemetry data
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TelemetryBase(BaseModel):
    """Base telemetry model"""
    device_id: str = Field(..., description="Device identifier")
    sensor_type: str = Field(..., description="Type of sensor")
    sensor_value: float = Field(..., description="Sensor reading value")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class TelemetryCreate(TelemetryBase):
    """Model for creating telemetry data"""
    is_anomaly: bool = Field(default=False, description="Whether reading is anomalous")


class TelemetryResponse(TelemetryBase):
    """Model for telemetry response"""
    id: int
    timestamp: datetime
    is_anomaly: bool
    
    class Config:
        from_attributes = True


class TelemetryBatch(BaseModel):
    """Model for batch telemetry data"""
    device_id: str
    readings: list[TelemetryCreate]
    
    class Config:
        from_attributes = True


class TelemetryStats(BaseModel):
    """Model for telemetry statistics"""
    device_id: str
    sensor_type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    count: int = 0
    period_hours: int = 24
