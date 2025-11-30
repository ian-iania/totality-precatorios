"""
Integration module for TJRJ Precatórios Extractor App

This module provides the bridge between the Streamlit UI and the backend scraper.
It does NOT modify any backend code - only calls existing scripts.
"""

import subprocess
import sys
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
from app.utils import (
    get_project_root, get_output_dir, estimate_pages, 
    estimate_time_minutes, list_partial_files, calculate_progress,
    count_csv_records, clean_entity_name
)


class EntityLoader:
    """
    Loads entity list from TJRJ website
    
    This is a lightweight operation (~5-10s) that only fetches the entity cards,
    not the full precatório data.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
    
    def get_entities(self, regime: str) -> List[Dict]:
        """
        Fetch list of entities for a regime
        
        Args:
            regime: 'geral' or 'especial'
        
        Returns:
            List of dicts with: id, nome, precatorios_pendentes, precatorios_pagos, total
        """
        logger.info(f"Loading entities for regime: {regime}")
        
        entities = []
        
        if regime == 'geral':
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral"
        else:
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-especial"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                logger.info(f"Navigating to {url}")
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait for AngularJS to render
                try:
                    page.wait_for_selector("text=Precatórios Pagos", timeout=15000)
                except:
                    logger.warning("Timeout waiting for entity cards")
                
                page.wait_for_timeout(3000)
                
                # Find entity cards using ng-repeat selector
                # The page uses: ng-repeat="ente in vm.EntesDevedores"
                cards = page.query_selector_all('[ng-repeat="ente in vm.EntesDevedores"]')
                logger.info(f"Found {len(cards)} entity cards")
                
                for card in cards:
                    try:
                        entity = self._parse_entity_card(card, regime)
                        if entity:
                            entities.append(entity)
                    except Exception as e:
                        logger.warning(f"Error parsing card: {e}")
                        continue
                
                browser.close()
        
        except Exception as e:
            logger.error(f"Error loading entities: {e}")
            raise
        
        # Sort by total (descending)
        entities.sort(key=lambda x: x['total'], reverse=True)
        
        logger.info(f"Loaded {len(entities)} entities for regime {regime}")
        return entities
    
    def _parse_entity_card(self, card, regime: str) -> Optional[Dict]:
        """
        Parse entity data from card element
        
        Card structure:
        - Entity name (first line)
        - Precatórios Pagos: X
        - Precatórios Pendentes: Y
        - Valor Prioridade: R$ Z
        - etc.
        """
        try:
            card_text = card.inner_text()
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
            
            # Get entity name (first line)
            nome = lines[0] if lines else ''
            if not nome:
                return None
            
            # Get link for ID
            link = card.query_selector('a[href*="idEntidadeDevedora"]')
            if not link:
                return None
            
            href = link.get_attribute('href')
            id_match = re.search(r'idEntidadeDevedora=(\d+)', href)
            if not id_match:
                return None
            
            entity_id = int(id_match.group(1))
            
            # Parse statistics from card text
            precatorios_pagos = 0
            precatorios_pendentes = 0
            
            for i, line in enumerate(lines):
                if 'Precatórios Pagos' in line:
                    # Value is on the next line
                    if i + 1 < len(lines):
                        num = re.sub(r'[^\d]', '', lines[i + 1])
                        precatorios_pagos = int(num) if num else 0
                
                if 'Precatórios Pendentes' in line:
                    # Value is on the next line
                    if i + 1 < len(lines):
                        num = re.sub(r'[^\d]', '', lines[i + 1])
                        precatorios_pendentes = int(num) if num else 0
            
            total = precatorios_pagos + precatorios_pendentes
            
            return {
                "id": entity_id,
                "nome": nome,
                "regime": regime,
                "precatorios_pagos": precatorios_pagos,
                "precatorios_pendentes": precatorios_pendentes,
                "total": total,
                "paginas_estimadas": estimate_pages(total)
            }
        
        except Exception as e:
            logger.warning(f"Error parsing entity card: {e}")
            return None
    
    def _parse_int(self, value: str) -> int:
        """Parse integer from string"""
        if not value:
            return 0
        value = re.sub(r'[^\d]', '', value)
        try:
            return int(value) if value else 0
        except:
            return 0


class ExtractionRunner:
    """
    Runs the extraction process using main_v3_parallel.py
    """
    
    def __init__(self):
        self.project_root = get_project_root()
        self.output_dir = get_output_dir()
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.entity_info: Optional[Dict] = None
    
    def start_extraction(
        self,
        entity_id: int,
        entity_name: str,
        regime: str,
        total_pages: int,
        num_processes: int = 4,
        output_file: str = None,
        append_mode: bool = False
    ) -> subprocess.Popen:
        """
        Start extraction as a subprocess
        
        Args:
            entity_id: Entity ID
            entity_name: Entity name (for logging and filename)
            regime: 'geral' or 'especial'
            total_pages: Total pages to extract
            num_processes: Number of parallel processes (2-6)
            output_file: Path to consolidated output file
            append_mode: If True, append to existing file
        
        Returns:
            subprocess.Popen object
        """
        # Build command - Use V4 fast extraction
        cmd = [
            sys.executable,  # Use same Python interpreter
            "main_v4_fast.py",
            "--entity-id", str(entity_id),
            "--entity-name", entity_name,
            "--regime", regime,
            "--total-pages", str(total_pages),
            "--num-processes", str(num_processes),
            "--timeout", "20"  # 20 min timeout per worker
        ]
        
        if output_file:
            cmd.extend(["--output", output_file])
        
        if append_mode:
            cmd.append("--append")
        
        logger.info(f"Starting extraction: {' '.join(cmd)}")
        
        # Start subprocess
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(self.project_root),
            text=True,
            bufsize=1
        )
        
        self.start_time = datetime.now()
        self.entity_info = {
            "id": entity_id,
            "name": entity_name,
            "regime": regime,
            "total_pages": total_pages,
            "num_processes": num_processes,
            "expected_records": total_pages * 10  # ~10 records per page
        }
        
        return self.process
    
    def is_running(self) -> bool:
        """Check if extraction is still running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_progress(self) -> Dict:
        """
        Get current extraction progress by parsing log file
        
        Returns:
            Dict with: records, percent, elapsed_seconds
        """
        import re
        
        if not self.entity_info:
            return {"records": 0, "percent": 0, "elapsed_seconds": 0, "is_running": False}
        
        expected = self.entity_info.get("expected_records", 1)
        total_pages = self.entity_info.get("total_pages", 0)
        num_processes = self.entity_info.get("num_processes", 4)
        
        # Calculate elapsed time
        elapsed_seconds = 0
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Parse log file to get current progress - ONLY lines after start_time
        total_records = 0
        pages_done = 0
        
        if not self.start_time:
            return {
                "records": 0,
                "expected_records": expected,
                "percent": 0,
                "elapsed_seconds": elapsed_seconds,
                "is_running": self.is_running()
            }
        
        # Format start time for comparison
        start_str = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        log_file = self.project_root / "logs" / "scraper_v3.log"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Only check lines AFTER our start time
                for line in lines:
                    # Extract timestamp from line (format: 2025-11-30 15:14:34 | INFO |)
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        line_time = match.group(1)
                        if line_time < start_str:
                            continue  # Skip old lines
                    
                    # Match: [P1]   ✅ 10 records (total: 620)
                    match = re.search(r'\[P\d\].*total: (\d+)\)', line)
                    if match:
                        records = int(match.group(1))
                        if records > total_records:
                            total_records = records
                    
                    # Match: [P1] Page 42/63 (42/63)
                    match = re.search(r'\[P\d\] Page (\d+)/(\d+)', line)
                    if match:
                        page = int(match.group(1))
                        if page > pages_done:
                            pages_done = page
            except Exception:
                pass
        
        # Estimate: each process reports its own total
        # Multiply by num_processes and divide by 2 (rough average)
        estimated_total = total_records * num_processes // 2
        
        # Calculate percent based on records
        percent = min(99, (estimated_total / expected * 100)) if expected > 0 else 0
        
        return {
            "records": estimated_total,
            "expected_records": expected,
            "percent": percent,
            "elapsed_seconds": elapsed_seconds,
            "pages_done": pages_done,
            "is_running": self.is_running()
        }
    
    def get_result(self) -> Dict:
        """
        Get extraction result after completion
        
        Returns:
            Dict with: success, output_file, records, duration_seconds, error
        """
        if self.is_running():
            return {"success": False, "error": "Still running"}
        
        if self.process is None:
            return {"success": False, "error": "No process"}
        
        # Get return code
        return_code = self.process.returncode
        
        # Find output file
        output_file = None
        records = 0
        
        if self.entity_info:
            entity_name_clean = clean_entity_name(self.entity_info["name"])
            pattern = f"precatorios_{entity_name_clean}_*.csv"
            
            # Find most recent matching file
            files = sorted(
                self.output_dir.glob(pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if files:
                output_file = files[0]
                records = count_csv_records(output_file)
        
        # Calculate duration
        duration_seconds = 0
        if self.start_time:
            duration_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "success": return_code == 0,
            "return_code": return_code,
            "output_file": str(output_file) if output_file else None,
            "output_filename": output_file.name if output_file else None,
            "records": records,
            "duration_seconds": duration_seconds,
            "error": None if return_code == 0 else f"Process exited with code {return_code}"
        }
    
    def cancel(self):
        """Cancel running extraction"""
        if self.process and self.is_running():
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("Extraction cancelled")
    
    def cleanup(self):
        """Clean up resources"""
        self.process = None
        self.start_time = None
        self.entity_info = None


def get_entity_page_count(entity_id: int, regime: str, headless: bool = True) -> int:
    """
    Get the actual page count for an entity by navigating to its page
    
    This is more accurate than estimating from precatório count.
    """
    if regime == 'geral':
        # For geral, we need to check the actual page
        pass
    
    url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entity_id}"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)
            
            # Try to find pagination info
            # Look for "Página X de Y" or similar
            page_text = page.inner_text('body')
            
            # Try to find total pages from pagination
            # Pattern: "de 2984" or "/ 2984"
            match = re.search(r'(?:de|/)\s*(\d+)\s*(?:páginas?)?', page_text, re.IGNORECASE)
            if match:
                total_pages = int(match.group(1))
                browser.close()
                return total_pages
            
            # Fallback: count rows and estimate
            rows = page.query_selector_all('tbody tr[ng-repeat-start]')
            if rows:
                # If we have 10 rows per page, we need to find total
                # This is less accurate
                pass
            
            browser.close()
            return 0
    
    except Exception as e:
        logger.error(f"Error getting page count: {e}")
        return 0
