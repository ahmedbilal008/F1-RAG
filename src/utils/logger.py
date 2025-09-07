"""
Logging configuration for the F1 RAG Chatbot
"""

import sys
from loguru import logger
from src.utils.config import config

def setup_logger():
    """Setup logger configuration"""
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler if in debug mode
    if config.DEBUG:
        logger.add(
            "logs/f1_rag_chatbot.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days"
        )
    
    return logger

# Initialize logger
app_logger = setup_logger()