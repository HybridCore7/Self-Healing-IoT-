"""
Custom logging configuration using loguru
Provides structured logging for the entire application
"""
from loguru import logger
import sys
from pathlib import Path
from config.settings import settings


def setup_logger():
    """
    Configure application-wide logging
    """
    # Remove default handler
    logger.remove()
    
    # Console handler (with colors)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler (general logs)
    log_path = Path(settings.log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        settings.log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )
    
    # MQTT specific logs
    logger.add(
        "logs/mqtt.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        filter=lambda record: "mqtt" in record["name"].lower(),
        rotation="5 MB",
        retention="3 days",
    )
    
    # Healing specific logs
    logger.add(
        "logs/healing.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        filter=lambda record: "healing" in record["name"].lower(),
        rotation="5 MB",
        retention="7 days",
    )
    
    logger.info("Logger initialized successfully")
    return logger


# Initialize logger
app_logger = setup_logger()


def get_logger(name: str):
    """
    Get a logger instance for a specific module
    
    Args:
        name: Name of the module
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)
