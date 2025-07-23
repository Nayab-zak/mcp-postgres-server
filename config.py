"""
config.py

Central configuration module for the FastMCP servers:
- Loads environment variables from a .env file
- Exposes application settings (DB_URL, LOG_PATH)
- Sets up structured, file‑based logging via dictConfig
"""
import os
from dotenv import load_dotenv
import logging
from logging.config import dictConfig

# --- Load environment variables ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# --- Application settings ---
DB_URL = os.getenv("DB_URL")  # e.g. postgresql://user:pass@host:port/dbname
LOG_PATH = os.getenv(
    "LOG_PATH",
    os.path.join(os.path.dirname(__file__), "logs", "app.log")
)

# --- Centralized logging configuration ---
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': LOG_PATH,
            'mode': 'a',
        }
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    }
}

# Apply logging configuration
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()