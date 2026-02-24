"""
Pydantic models for IoT devices
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from src.utils.constants import DeviceStatus


class DeviceBase(BaseModel):
    """Base device model with common fields"""
    device_name: str = Field(..., description="Human-readable device name")
    device_type: str = Field(..., description="Type of IoT device")
    location: Optional[str] = Field(None, description="Physical location of device")
    ip_address: Optional[str] = Field(None, description="IP address of device")
    firmware_version: Optional[str] = Field(None, description="Firmware version")


class DeviceCreate(DeviceBase):
    """Model for creating a new device"""
    device_id: str = Field(..., description="Unique device identifier")


class DeviceUpdate(BaseModel):
    """Model for updating device information"""
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[DeviceStatus] = None


class Device(DeviceBase):
    """Complete device model"""
    device_id: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_heartbeat: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceHealth(BaseModel):
    """Device health metrics"""
    device_id: str
    cpu_usage: Optional[float] = Field(None, ge=0, le=100, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, ge=0, le=100, description="Memory usage percentage")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="Battery level percentage")
    signal_strength: Optional[float] = Field(None, description="Signal strength in dBm")
    uptime_seconds: Optional[int] = Field(None, ge=0, description="Uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
