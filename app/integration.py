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
        
        # Generate unique log file for this extraction
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.project_root / "logs" / f"extraction_{timestamp}.log"
        log_file.parent.mkdir(exist_ok=True)
        self.current_log_file = str(log_file)
        
        # Build command - Use V4 Memory extraction (no intermediate I/O)
        cmd = [
            sys.executable,  # Use same Python interpreter
            "main_v4_memory.py",
            "--entity-id", str(entity_id),
            "--entity-name", entity_name,
            "--regime", regime,
            "--total-pages", str(total_pages),
            "--num-processes", str(effective_processes),
            "--timeout", str(timeout_minutes),
            "--log-file", str(log_file)
        ]
        
        if output_file:
            cmd.extend(["--output", output_file])
        
        if append_mode:
            cmd.append("--append")
        
        logger.info(f"Starting extraction: {' '.join(cmd)}")
        logger.info(f"Log file: {log_file}")
        
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
        
        # Use scraper_v3.log (where workers actually write) with timestamp filtering
        log_file = self.project_root / "logs" / "scraper_v3.log"
        start_str = self.start_time.strftime('%Y-%m-%d %H:%M') if self.start_time else None
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                
                for line in content.split('\n'):
                    # Filter by start time to only get current extraction
                    if start_str:
                        ts_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
                        if ts_match and ts_match.group(1) < start_str:
                            continue
                    
                    # Match: [P1] Page 42/63 (42/63)
                    # The second number in parentheses is pages done by this process
                    page_match = re.search(r'\[P(\d+)\] Page \d+/\d+ \((\d+)/\d+\)', line)
                    if page_match:
                        proc_id = page_match.group(1)
                        pages_by_proc = int(page_match.group(2))
                        process_max_page[proc_id] = max(process_max_page.get(proc_id, 0), pages_by_proc)
                    
                    # Match: [P1] ✅ ... (total: 620)
                    rec_match = re.search(r'\[P(\d+)\].*total: (\d+)\)', line)
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


class AllEntitiesRunner:
    """
    Runs extraction for ALL entities in a single process using main_v5_all_entities.py
    
    This is the recommended approach for full extractions:
    - Single process handles all entities sequentially
    - No intermediate I/O - all data in memory until final save
    - Entities processed in order (largest first)
    - Single CSV/Excel output at the end
    """
    
    def __init__(self):
        self.project_root = get_project_root()
        self.output_dir = get_output_dir()
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[datetime] = None
        self.extraction_info: Optional[Dict] = None
        self.current_log_file: Optional[str] = None
    
    def start_extraction(
        self,
        regime: str,
        num_processes: int = 12,
        timeout_minutes: int = 60,
        entity_ids: List[int] = None,
        skip_entity_ids: List[int] = None,
        output_file: str = None
    ) -> subprocess.Popen:
        """
        Start extraction for all entities as a subprocess
        
        Args:
            regime: 'geral' or 'especial'
            num_processes: Number of parallel workers per entity
            timeout_minutes: Timeout per entity
            entity_ids: Optional list of specific entity IDs to process
            skip_entity_ids: Optional list of entity IDs to skip
            output_file: Optional output file path
        
        Returns:
            subprocess.Popen object
        """
        # Generate unique log file for this extraction
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.project_root / "logs" / f"extraction_v5_{timestamp}.log"
        log_file.parent.mkdir(exist_ok=True)
        self.current_log_file = str(log_file)
        
        # Build command
        cmd = [
            sys.executable,
            "main_v5_all_entities.py",
            "--regime", regime,
            "--num-processes", str(num_processes),
            "--timeout", str(timeout_minutes),
            "--log-file", str(log_file)
        ]
        
        if output_file:
            cmd.extend(["--output", output_file])
        
        if entity_ids:
            cmd.extend(["--entity-ids", ",".join(str(x) for x in entity_ids)])
        
        if skip_entity_ids:
            cmd.extend(["--skip-entity-ids", ",".join(str(x) for x in skip_entity_ids)])
        
        logger.info(f"Starting V5 extraction: {' '.join(cmd)}")
        logger.info(f"Log file: {log_file}")
        
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
            "regime": regime,
            "num_processes": num_processes,
            "timeout_minutes": timeout_minutes
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
        
        Returns progress info including:
        - Current entity being processed
        - Total entities
        - Records extracted so far
        - Worker progress
        """
        if not self.extraction_info:
            return {
                "records": 0,
                "percent": 0,
                "elapsed_seconds": 0,
                "current_entity": None,
                "current_entity_idx": 0,
                "total_entities": 0,
                "is_running": False,
                "workers": {}
            }
        
        elapsed_seconds = 0
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Parse log file
        log_file = self.project_root / "logs" / "scraper_v3.log"
        start_str = self.start_time.strftime('%Y-%m-%d %H:%M') if self.start_time else None
        
        current_entity = None
        current_entity_idx = 0
        total_entities = 0
        total_records = 0
        workers_data = {}
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                
                for line in content.split('\n'):
                    # Filter by start time
                    if start_str:
                        ts_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
                        if ts_match and ts_match.group(1) < start_str:
                            continue
                    
                    # Match entity progress: 📍 ENTITY 1/41: Estado do Rio de Janeiro (with or without emoji)
                    entity_match = re.search(r'ENTITY\s*(\d+)/(\d+):\s*(.+)', line)
                    if entity_match:
                        current_entity_idx = int(entity_match.group(1))
                        total_entities = int(entity_match.group(2))
                        current_entity = entity_match.group(3).strip()
                    
                    # Match worker page progress: [P1] Page 42/63 (42/63)
                    page_match = re.search(r'\[P(\d+)\] Page \d+/\d+ \((\d+)/(\d+)\)', line)
                    if page_match:
                        proc_id = page_match.group(1)
                        pages_done = int(page_match.group(2))
                        pages_total = int(page_match.group(3))
                        if proc_id not in workers_data:
                            workers_data[proc_id] = {'records': 0}
                        workers_data[proc_id].update({
                            'pages_done': pages_done,
                            'pages_total': pages_total,
                            'progress': pages_done / pages_total if pages_total > 0 else 0
                        })
                    
                    # Match worker records: [P1] ✅ 10 records (total: 420)
                    record_match = re.search(r'\[P(\d+)\].*\(total:\s*(\d+)\)', line)
                    if record_match:
                        proc_id = record_match.group(1)
                        records = int(record_match.group(2))
                        if proc_id not in workers_data:
                            workers_data[proc_id] = {}
                        workers_data[proc_id]['records'] = records
                    
                    # Match total progress: Progress: 5/41 entities | 125,000 total records
                    progress_match = re.search(r'Progress:\s*(\d+)/(\d+)\s*entities\s*\|\s*([\d,]+)\s*total records', line)
                    if progress_match:
                        current_entity_idx = int(progress_match.group(1))
                        total_entities = int(progress_match.group(2))
                        total_records = int(progress_match.group(3).replace(',', ''))
                
            except Exception as e:
                logger.warning(f"Error parsing log: {e}")
        
        # Calculate overall percent
        percent = 0
        if total_entities > 0:
            # Base progress on entities completed
            entity_progress = (current_entity_idx - 1) / total_entities if current_entity_idx > 0 else 0
            
            # Add current entity worker progress
            if workers_data:
                avg_worker_progress = sum(w.get('progress', 0) for w in workers_data.values()) / len(workers_data)
                entity_progress += avg_worker_progress / total_entities
            
            percent = entity_progress * 100
        
        return {
            "records": total_records,
            "percent": min(percent, 100),
            "elapsed_seconds": elapsed_seconds,
            "current_entity": current_entity,
            "current_entity_idx": current_entity_idx,
            "total_entities": total_entities,
            "is_running": self.is_running(),
            "workers": workers_data,
            "num_processes": self.extraction_info.get("num_processes", 12)
        }
    
    def get_result(self) -> Dict:
        """Get extraction result after completion"""
        if self.is_running():
            return {"success": False, "error": "Still running"}
        
        if self.process is None:
            return {"success": False, "error": "No process"}
        
        return_code = self.process.returncode
        
        # Find output file
        output_file = None
        records = 0
        
        regime = self.extraction_info.get("regime", "especial") if self.extraction_info else "especial"
        pattern = f"precatorios_{regime}_ALL_*.csv"
        
        files = sorted(
            self.output_dir.glob(pattern),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if files:
            output_file = files[0]
            records = count_csv_records(output_file)
        
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
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("Extraction cancelled")
    
    def cleanup(self):
        """Clean up resources"""
        self.process = None
        self.start_time = None
        self.extraction_info = None


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
