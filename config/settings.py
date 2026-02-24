"""
Application Settings and Configuration Management
Loads configuration from environment variables and provides typed settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MQTT Configuration
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_keepalive: int = 60
    
    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug_mode: bool = True
    
    # Database
    database_path: str = "data/iot_system.db"
    
    # ML Model Configuration
    anomaly_contamination: float = 0.1
    anomaly_window_size: int = 50
    model_retrain_interval: int = 3600
    
    # Healing Configuration
    heartbeat_timeout: int = 30
    max_healing_attempts: int = 3
    healing_cooldown: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_file_path: str = "logs/system.log"
    
    # Dashboard
    dashboard_port: int = 8501
    dashboard_refresh_interval: int = 2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings
