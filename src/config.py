"""
Configuration management using environment variables and .env files
"""

from pathlib import Path
from dotenv import load_dotenv
import os
from src.models import ScraperConfig

# Load environment variables from .env file
load_dotenv()


def get_config() -> ScraperConfig:
    """
    Loads configuration from environment variables

    Returns:
        ScraperConfig instance with all settings
    """
    return ScraperConfig(
        base_url=os.getenv('TJRJ_BASE_URL', 'https://www.tjrj.jus.br/web/precatorios'),
        regime=os.getenv('TJRJ_REGIME', 'geral'),
        max_retries=int(os.getenv('TJRJ_MAX_RETRIES', '3')),
        retry_delay=float(os.getenv('TJRJ_RETRY_DELAY', '2.0')),
        page_load_timeout=int(os.getenv('TJRJ_PAGE_LOAD_TIMEOUT', '30000')),
        enable_cache=os.getenv('TJRJ_ENABLE_CACHE', 'true').lower() == 'true',
        cache_dir=os.getenv('TJRJ_CACHE_DIR', 'data/cache'),
        output_dir=os.getenv('TJRJ_OUTPUT_DIR', 'data/processed'),
        log_level=os.getenv('TJRJ_LOG_LEVEL', 'INFO'),
        headless=os.getenv('TJRJ_HEADLESS', 'true').lower() == 'true'
    )
