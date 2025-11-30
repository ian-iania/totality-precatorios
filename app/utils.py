"""
Utility functions for TJRJ Precatórios Extractor App
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


def get_project_root() -> Path:
    """Get the project root directory (Charles/)"""
    # app/utils.py -> Charles/
    return Path(__file__).parent.parent


def get_output_dir() -> Path:
    """Get the output directory for CSV files"""
    return get_project_root() / "output"


def format_number(n: int) -> str:
    """Format number with thousands separator (Brazilian style)"""
    return f"{n:,}".replace(",", ".")


def format_currency(value: float) -> str:
    """Format currency in Brazilian Real"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}min {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}min"


def format_time(dt: datetime) -> str:
    """Format datetime as HH:MM"""
    return dt.strftime("%H:%M")


def format_datetime(dt: datetime) -> str:
    """Format datetime as DD/MM/YYYY HH:MM"""
    return dt.strftime("%d/%m/%Y %H:%M")


def format_filesize(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def estimate_pages(total_records: int, records_per_page: int = 10) -> int:
    """Estimate number of pages based on total records"""
    return (total_records + records_per_page - 1) // records_per_page


def estimate_time_minutes(total_pages: int, num_processes: int = 4, seconds_per_page: float = 5.0) -> float:
    """
    Estimate extraction time in minutes
    
    Args:
        total_pages: Total pages to extract
        num_processes: Number of parallel processes
        seconds_per_page: Seconds per page (5s with skip-expanded)
    
    Returns:
        Estimated time in minutes
    """
    pages_per_process = total_pages / num_processes
    total_seconds = pages_per_process * seconds_per_page
    return total_seconds / 60


def count_csv_records(filepath: Path) -> int:
    """Count records in a CSV file (excluding header)"""
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            return sum(1 for _ in f) - 1  # Subtract header
    except Exception:
        return 0


def list_csv_files(directory: Path, pattern: str = "*.csv") -> List[Dict]:
    """
    List CSV files in directory with metadata
    
    Returns:
        List of dicts with: name, path, size, modified, records
    """
    files = []
    
    if not directory.exists():
        return files
    
    for filepath in sorted(directory.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True):
        if filepath.is_file():
            stat = filepath.stat()
            files.append({
                "name": filepath.name,
                "path": str(filepath),
                "size": stat.st_size,
                "size_formatted": format_filesize(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "modified_formatted": format_datetime(datetime.fromtimestamp(stat.st_mtime)),
                "records": count_csv_records(filepath)
            })
    
    return files


def list_partial_files(output_dir: Path, session_id: str = None) -> List[Path]:
    """List partial CSV files from extraction"""
    pattern = "partial_*.csv"
    return sorted(output_dir.glob(pattern), key=lambda x: x.stat().st_mtime)


def calculate_progress(partial_files: List[Path], expected_total: int) -> Dict:
    """
    Calculate extraction progress from partial files
    
    Returns:
        Dict with: records, percent, pages_done
    """
    total_records = sum(count_csv_records(f) for f in partial_files)
    percent = min(100, (total_records / expected_total * 100)) if expected_total > 0 else 0
    
    return {
        "records": total_records,
        "percent": percent,
        "files_count": len(partial_files)
    }


def clean_entity_name(name: str) -> str:
    """Clean entity name for use in filenames"""
    # Remove special characters, keep alphanumeric and spaces
    import re
    cleaned = re.sub(r'[^\w\s-]', '', name)
    cleaned = re.sub(r'\s+', '_', cleaned)
    return cleaned[:50]  # Limit length
