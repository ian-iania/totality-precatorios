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
        # Optimize: Don't create more workers than pages
        # Many entities have very few pages (1-5), no need for 8 workers
        effective_processes = min(num_processes, total_pages)
        if effective_processes < num_processes:
            logger.info(f"Optimized: {total_pages} pages → {effective_processes} workers (instead of {num_processes})")
        
        # Calculate dynamic timeout based on pages per worker
        # ~3 seconds per page + 5 min margin, minimum 30 min, maximum 120 min
        pages_per_worker = total_pages // effective_processes if effective_processes > 0 else total_pages
        timeout_minutes = max(30, min(120, (pages_per_worker * 3) // 60 + 5))
        
        logger.info(f"Dynamic timeout: {timeout_minutes} min for {pages_per_worker} pages/worker")
        
        # Build command - Use V4 fast extraction
        cmd = [
            sys.executable,  # Use same Python interpreter
            "main_v4_fast.py",
            "--entity-id", str(entity_id),
            "--entity-name", entity_name,
            "--regime", regime,
            "--total-pages", str(total_pages),
            "--num-processes", str(effective_processes),
            "--timeout", str(timeout_minutes)
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
            "num_processes": effective_processes,  # Use optimized count
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
            Dict with: records, percent, elapsed_seconds, pages_done, total_pages
        """
        import re
        
        if not self.entity_info:
            return {"records": 0, "percent": 0, "elapsed_seconds": 0, "pages_done": 0, "total_pages": 0, "is_running": False}
        
        expected = self.entity_info.get("expected_records", 1)
        total_pages = self.entity_info.get("total_pages", 0)
        num_processes = self.entity_info.get("num_processes", 4)
        
        # Calculate elapsed time
        elapsed_seconds = 0
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        if not self.start_time:
            return {
                "records": 0,
                "expected_records": expected,
                "percent": 0,
                "elapsed_seconds": elapsed_seconds,
                "pages_done": 0,
                "total_pages": total_pages,
                "is_running": self.is_running()
            }
        
        # Parse log file to get current progress
        # Track max page seen per process (pages are sequential within each process)
        process_max_page = {}  # {process_id: max_page_seen}
        process_records = {}  # {process_id: total_records}
        
        start_str = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        log_file = self.project_root / "logs" / "scraper_v3.log"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    # Read entire file to not miss any progress
                    content = f.read()
                
                # Only process lines after start time
                for line in content.split('\n'):
                    # Extract timestamp from line
                    ts_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if ts_match:
                        line_time = ts_match.group(1)
                        if line_time < start_str:
                            continue
                    
                    # Match: [P1] Page 42/63 (42/63)
                    # The second number in parentheses is pages done by this process
                    page_match = re.search(r'\[P(\d)\] Page \d+/\d+ \((\d+)/\d+\)', line)
                    if page_match:
                        proc_id = page_match.group(1)
                        pages_by_proc = int(page_match.group(2))
                        process_max_page[proc_id] = max(process_max_page.get(proc_id, 0), pages_by_proc)
                    
                    # Match: [P1] ✅ ... (total: 620)
                    rec_match = re.search(r'\[P(\d)\].*total: (\d+)\)', line)
                    if rec_match:
                        proc_id = rec_match.group(1)
                        records = int(rec_match.group(2))
                        process_records[proc_id] = max(process_records.get(proc_id, 0), records)
            except Exception:
                pass
        
        # Sum pages done across all processes
        pages_done = sum(process_max_page.values())
        
        # Sum records across all processes
        total_records = sum(process_records.values())
        
        # Calculate percent based on pages (more accurate)
        percent = min(99, (pages_done / total_pages * 100)) if total_pages > 0 else 0
        
        # Build worker details for UI
        workers_data = []
        pages_per_process = total_pages // num_processes if num_processes > 0 else 0
        
        for i in range(1, num_processes + 1):
            proc_id = str(i)
            pages_done_proc = process_max_page.get(proc_id, 0)
            records_proc = process_records.get(proc_id, 0)
            
            # Calculate page range for this worker
            start_page = (i - 1) * pages_per_process + 1
            end_page = i * pages_per_process if i < num_processes else total_pages
            current_page = start_page + pages_done_proc - 1 if pages_done_proc > 0 else start_page
            
            progress_pct = (pages_done_proc / pages_per_process * 100) if pages_per_process > 0 else 0
            
            workers_data.append({
                "id": f"P{i}",
                "current_page": current_page,
                "end_page": end_page,
                "pages_done": pages_done_proc,
                "pages_total": pages_per_process,
                "progress": min(100, progress_pct),
                "records": records_proc
            })
        
        return {
            "records": total_records,
            "expected_records": expected,
            "percent": percent,
            "elapsed_seconds": elapsed_seconds,
            "pages_done": pages_done,
            "total_pages": total_pages,
            "is_running": self.is_running(),
            "workers": workers_data,
            "num_processes": num_processes
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


class FullMemoryExtractionRunner:
    """
    V5 - Full Memory Mode Extraction Runner
    
    Processes ALL entities at once, accumulates everything in memory,
    writes a single CSV at the very end.
    """
    
    def __init__(self):
        self.project_root = get_project_root()
        self.output_dir = get_output_dir()
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.extraction_info: Optional[Dict] = None
    
    def start_full_extraction(
        self,
        entities: List[Dict],
        regime: str,
        max_concurrent: int = 4,
        timeout_minutes: int = 30,
        output_file: str = None
    ) -> subprocess.Popen:
        """
        Start extraction of ALL entities as a single subprocess.
        
        Args:
            entities: List of {"id": int, "nome": str, "precatorios_pendentes": int}
            regime: 'geral' or 'especial'
            max_concurrent: Max concurrent entity extractions
            timeout_minutes: Timeout per entity
            output_file: Final CSV path
        
        Returns:
            subprocess.Popen object
        """
        import json
        
        # Convert entities to simplified format for JSON
        entities_json = []
        total_pages = 0
        total_expected = 0
        
        for e in entities:
            pendentes = e.get('precatorios_pendentes', 0)
            pages = (pendentes + 9) // 10
            if pages > 0:
                entities_json.append({
                    "id": e['id'],
                    "name": e['nome'],
                    "pages": pages
                })
                total_pages += pages
                total_expected += pages * 10
        
        if not entities_json:
            raise ValueError("No entities with pages to process")
        
        # Build command
        cmd = [
            sys.executable,
            "main_v5_memory.py",
            "--entities-json", json.dumps(entities_json),
            "--regime", regime,
            "--max-concurrent", str(max_concurrent),
            "--timeout", str(timeout_minutes)
        ]
        
        if output_file:
            cmd.extend(["--output", output_file])
        
        logger.info(f"Starting V5 full memory extraction: {len(entities_json)} entities, {total_pages} pages")
        
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
        self.extraction_info = {
            "total_entities": len(entities_json),
            "total_pages": total_pages,
            "expected_records": total_expected,
            "regime": regime,
            "max_concurrent": max_concurrent
        }
        
        return self.process
    
    def is_running(self) -> bool:
        """Check if extraction is still running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_progress(self) -> Dict:
        """Get extraction progress from log file with entity status"""
        import re
        
        if not self.extraction_info:
            return {"records": 0, "percent": 0, "entities_done": 0, "entity_status": {}}
        
        # Parse log for progress
        log_file = Path("logs/scraper_v3.log")
        records = 0
        entities_done = 0
        entity_status = {}  # {entity_id: 'processing'|'done'|'error', entity_id_records: count}
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-500:]  # Last 500 lines for more context
                    
                    for line in lines:
                        # Detect entity starting: [E107] 🌐 Starting
                        match_start = re.search(r'\[E(\d+)\].*🌐 Starting', line)
                        if match_start:
                            eid = int(match_start.group(1))
                            entity_status[eid] = 'processing'
                        
                        # Detect entity complete: [E107] ✅ Complete: X records
                        match_complete = re.search(r'\[E(\d+)\].*✅ Complete:\s*(\d+)\s*records', line)
                        if match_complete:
                            eid = int(match_complete.group(1))
                            rec_count = int(match_complete.group(2))
                            entity_status[eid] = 'done'
                            entity_status[f"{eid}_records"] = rec_count
                            entities_done += 1
                        
                        # Detect entity error: [E107] ❌ Failed
                        match_error = re.search(r'\[E(\d+)\].*❌', line)
                        if match_error:
                            eid = int(match_error.group(1))
                            if entity_status.get(eid) != 'done':  # Don't override done
                                entity_status[eid] = 'error'
                        
                        # Get latest record count from progress line
                        if "records in memory" in line:
                            match = re.search(r'(\d+(?:,\d+)?)\s*records in memory', line)
                            if match:
                                records = int(match.group(1).replace(',', ''))
            except:
                pass
        
        expected = self.extraction_info.get("expected_records", 1)
        percent = min(100, (records / expected) * 100) if expected > 0 else 0
        
        elapsed_seconds = 0
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "records": records,
            "percent": percent,
            "entities_done": entities_done,
            "total_entities": self.extraction_info.get("total_entities", 0),
            "expected_records": expected,
            "elapsed_seconds": elapsed_seconds,
            "is_running": self.is_running(),
            "entity_status": entity_status
        }
    
    def stop(self):
        """Stop the extraction process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except:
                self.process.kill()
