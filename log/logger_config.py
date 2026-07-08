import os
from loguru import logger
from datetime import datetime
import sys
from django.conf import settings


current_date = datetime.now().strftime("%Y-%m-%d")
log_filename = f"app-{current_date}.log"
logs_file_path = os.path.join(settings.BASE_DIR, "log", "logs", log_filename)

handlers = [
    {
        "sink": logs_file_path,
        "level": "TRACE",  # Logs all levels to a file
        "format": "[{time:YYYY-MM-DD HH:mm:ss} UTC] - [{level:8}] - [{name:10}:{line}] - {message}",
        "colorize": False,  # Disable color for file output
        "rotation": "2 MB",  # Rotate logs when file size reaches 2 MB
        "catch": True,  # Handle logging errors gracefully
    },
    {
        "sink": sys.stdout,
        "level": "TRACE",  # Logs all levels to the console
        "format": "<level>[{time:YYYY-MM-DD HH:mm:ss} UTC] - [{level:8}] - [{name:10}:{line}] - {message}</level>",
        "colorize": True,  # Enable color for console output
        "catch": True,  # Handle logging errors gracefully
    }
]

logger.configure(handlers=handlers)
logger = logger

logger.success("Logger configured successfully")
