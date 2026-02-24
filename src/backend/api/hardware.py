"""
Hardware Healing API Endpoints
================================
FastAPI routes for managing real hardware devices and sending healing commands.

POST /api/hardware/command/{device_id}   — Send command to real device
GET  /api/hardware/devices               — List all discovered devices
GET  /api/hardware/devices/{device_id}   — Get specific device info
POST /api/hardware/heal/{device_id}      — Trigger manual healing
GET  /api/hardware/commands/log          — Command history
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from src.mqtt.device_discovery import get_device_registry
from src.healing.hardware_commands import get_dispatcher, FAULT_TO_COMMAND, HEALING_COMMANDS
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/hardware", tags=["Hardware"])


# ── Request Models ─────────────────────────
class CommandRequest(BaseModel):
    command:  str
    reason:   Optional[str] = "manual"
    params:   Optional[Dict[str, Any]] = {}

class HealRequest(BaseModel):
    fault_type:  str = "unknown"
    device_type: str = "unknown"
    notes:       Optional[str] = ""


# ══════════════════════════════════════════
# Device Discovery Endpoints
# ══════════════════════════════════════════

@router.get("/devices")
async def list_hardware_devices():
    """
    Return all auto-discovered hardware devices.
    Devices appear here automatically when they connect to MQTT.
    """
    registry = get_device_registry()
    devices  = registry.get_all_devices()
    stats    = registry.get_stats()
    return {
        "devices":    devices,
        "stats":      stats,
        "timestamp":  datetime.utcnow().isoformat(),
    }


@router.get("/devices/{device_id}")
async def get_hardware_device(device_id: str):
    """Get details of a specific hardware device."""
    registry = get_device_registry()
    device   = registry.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404,
                            detail=f"Device '{device_id}' not found. "
                                   "It will appear when it sends a heartbeat.")
    return device


# ══════════════════════════════════════════
# Command Endpoints
# ══════════════════════════════════════════

@router.post("/command/{device_id}")
async def send_hardware_command(device_id: str, request: CommandRequest):
    """
    Send a direct command to a hardware device.

    Commands:  ping | reset | recalibrate | validate | increase_frequency | diagnostic
    """
    valid_commands = set(HEALING_COMMANDS.values()) | {"ping", "diagnostic"}
    if request.command not in valid_commands:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid command '{request.command}'. "
                   f"Valid: {sorted(valid_commands)}"
        )

    dispatcher = get_dispatcher()
    result = dispatcher.send_command(
        device_id=device_id,
        command=request.command,
        healing_reason=request.reason,
        params=request.params,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=503,
            detail="MQTT broker not available. Is Mosquitto running?"
        )

    logger.info(f"Manual command '{request.command}' sent to {device_id}")
    return {
        "status":    "sent",
        "device_id": device_id,
        "command":   request.command,
        "topic":     result["topic"],
        "timestamp": result["timestamp"],
    }


@router.post("/heal/{device_id}")
async def trigger_hardware_healing(device_id: str, request: HealRequest):
    """
    Trigger AI-based self-healing for a specific device.
    The system chooses the best healing action based on fault_type.
    """
    registry = get_device_registry()
    device   = registry.get_device(device_id)
    device_type = request.device_type

    # Auto-detect device type from registry
    if device and device_type == "unknown":
        device_type = device.get("device_type", "unknown")

    dispatcher = get_dispatcher()
    result = dispatcher.dispatch_healing(
        device_id=device_id,
        fault_type=request.fault_type,
        device_type=device_type,
        extra_params={"notes": request.notes} if request.notes else {},
    )

    return {
        "status":       "healing_triggered",
        "device_id":    device_id,
        "fault_type":   request.fault_type,
        "command_sent": result["command"],
        "success":      result["success"],
        "timestamp":    result["timestamp"],
    }


@router.post("/ping/{device_id}")
async def ping_device(device_id: str):
    """Ping a device to check if it's alive."""
    dispatcher = get_dispatcher()
    result = dispatcher.send_ping(device_id)
    return {"status": "ping_sent", "device_id": device_id, "success": result["success"]}


@router.post("/reset/{device_id}")
async def reset_device(device_id: str, reason: str = "manual_reset"):
    """Send hardware reset command to device."""
    dispatcher = get_dispatcher()
    result = dispatcher.send_reset(device_id, reason)
    return {"status": "reset_sent", "device_id": device_id, "success": result["success"]}


# ══════════════════════════════════════════
# Command History
# ══════════════════════════════════════════

@router.get("/commands/log")
async def get_command_log(limit: int = 50):
    """Return recent hardware healing commands."""
    dispatcher = get_dispatcher()
    return {
        "commands":  dispatcher.get_command_log(limit),
        "stats":     dispatcher.get_stats(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/fault-types")
async def list_fault_types():
    """List available fault types and their default healing commands."""
    return {
        "fault_types": FAULT_TO_COMMAND,
        "commands":    list(HEALING_COMMANDS.values()),
    }
