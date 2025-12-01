"""
TJRJ Precatórios Scraper V4 - Optimized Fast Extraction

Improvements over V3:
- Uses imap_unordered for non-blocking parallel processing
- Timeout protection per worker
- Direct memory consolidation (no intermediate CSV files)
- Progress callback support
- Graceful error handling per worker

Usage:
    python main_v4_fast.py --entity-id 1 --total-pages 2984 --num-processes 4
"""

import sys
import time
import argparse
import multiprocessing as mp
from multiprocessing import Manager
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from loguru import logger
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper_v3 import TJRJPrecatoriosScraperV3
from src.models import ScraperConfig, EntidadeDevedora


def setup_logging(level: str = "INFO"):
    """Configure logging"""
    logger.remove()
    
    # Console output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
        level=level,
        colorize=True
    )
    
    # File output
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}",
        level="DEBUG",
        rotation="10 MB"
    )


def divide_pages_into_ranges(total_pages: int, num_processes: int) -> List[Tuple[int, int]]:
    """Divide total pages into ranges for parallel processing"""
    pages_per_process = total_pages // num_processes
    remainder = total_pages % num_processes
    
    ranges = []
    start = 1
    
    for i in range(num_processes):
        extra = 1 if i < remainder else 0
        end = start + pages_per_process - 1 + extra
        ranges.append((start, end))
        start = end + 1
    
    return ranges


def extract_worker(args: Dict) -> Dict:
    """
    Worker function for parallel extraction
    
    Returns dict with results directly in memory (no CSV file)
    """
    from playwright.sync_api import sync_playwright
    
    entity_id = args['entity_id']
    entity_name = args['entity_name']
    regime = args['regime']
    start_page = args['start_page']
    end_page = args['end_page']
    process_id = args['process_id']
    skip_expanded = args.get('skip_expanded', True)
    headless = args.get('headless', True)
    timeout_minutes = args.get('timeout_minutes', 30)
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    try:
        logger.info(f"[P{process_id}] Starting: pages {start_page}-{end_page}")
        
        # Create scraper
        config = ScraperConfig(headless=headless)
        scraper = TJRJPrecatoriosScraperV3(config=config, skip_expanded=skip_expanded)
        
        # Create entity
        entidade = EntidadeDevedora(
            id_entidade=entity_id,
            nome_entidade=entity_name,
            regime=regime,
            precatorios_pagos=0,
            precatorios_pendentes=0,
            valor_prioridade=0,
            valor_rpv=0
        )
        
        # Extract with timeout check
        precatorios_data = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to entity
            entity_url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entity_id}"
            page.goto(entity_url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(3000)
            
            # Go to start page
            if start_page > 1:
                if not scraper.goto_page_direct(page, start_page):
                    raise Exception(f"Failed to navigate to page {start_page}")
            
            # Extract pages
            current_page = start_page
            total_pages_in_range = end_page - start_page + 1
            
            while current_page <= end_page:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    logger.warning(f"[P{process_id}] Timeout after {elapsed/60:.1f}min")
                    break
                
                page_in_range = current_page - start_page + 1
                logger.info(f"[P{process_id}] Page {current_page}/{end_page} ({page_in_range}/{total_pages_in_range})")
                
                # Extract precatórios from current page
                precatorios = scraper._extract_precatorios_from_page(page, entidade)
                
                # Convert to dicts
                for prec in precatorios:
                    precatorios_data.append(prec.model_dump())
                
                logger.info(f"[P{process_id}]   ✅ {len(precatorios)} records (total: {len(precatorios_data)})")
                
                # Next page
                if current_page < end_page:
                    next_btn = page.query_selector('a[ng-click="vm.ProximaPagina()"]')
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(2000)
                
                current_page += 1
            
            browser.close()
        
        elapsed = time.time() - start_time
        logger.info(f"[P{process_id}] ✅ Complete: {len(precatorios_data)} records in {elapsed/60:.1f}min")
        
        return {
            'process_id': process_id,
            'start_page': start_page,
            'end_page': end_page,
            'records': precatorios_data,  # Data in memory!
            'records_count': len(precatorios_data),
            'elapsed_seconds': elapsed,
            'success': True,
            'error': None
        }
    
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[P{process_id}] ❌ Failed: {e}")
        
        return {
            'process_id': process_id,
            'start_page': start_page,
            'end_page': end_page,
            'records': [],
            'records_count': 0,
            'elapsed_seconds': elapsed,
            'success': False,
            'error': str(e)
        }


def run_parallel_extraction(
    entity_id: int,
    entity_name: str,
    regime: str,
    total_pages: int,
    num_processes: int = 4,
    skip_expanded: bool = True,
    headless: bool = True,
    timeout_minutes: int = 30,
    output_path: Optional[str] = None,
    append_mode: bool = False
) -> Tuple[pd.DataFrame, Dict]:
    """
    Run parallel extraction with optimized memory handling
    
    Args:
        append_mode: If True, append to existing CSV file
    
    Returns:
        Tuple of (DataFrame with all records, stats dict)
    """
    start_time = time.time()
    
    # Divide pages
    ranges = divide_pages_into_ranges(total_pages, num_processes)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 V4 Fast Extraction - {entity_name}")
    logger.info(f"{'='*80}")
    logger.info(f"Pages: {total_pages} | Processes: {num_processes} | Skip expanded: {skip_expanded}")
    
    for i, (start, end) in enumerate(ranges, 1):
        logger.info(f"  P{i}: pages {start:,}-{end:,} ({end-start+1:,} pages)")
    
    # Prepare worker args
    worker_args = []
    for i, (start, end) in enumerate(ranges, 1):
        worker_args.append({
            'entity_id': entity_id,
            'entity_name': entity_name,
            'regime': regime,
            'start_page': start,
            'end_page': end,
            'process_id': i,
            'skip_expanded': skip_expanded,
            'headless': headless,
            'timeout_minutes': timeout_minutes
        })
    
    # Run with apply_async for timeout control per worker
    all_records = []
    results = []
    
    # Use timeout_minutes passed from CLI (already calculated dynamically in integration.py)
    # Convert to seconds for apply_async
    worker_timeout = timeout_minutes * 60
    
    logger.info(f"\n🔄 Starting extraction (worker timeout: {worker_timeout}s = {timeout_minutes}min)...")
    
    with mp.Pool(processes=num_processes) as pool:
        # Submit all workers
        async_results = []
        for args in worker_args:
            async_results.append((args['process_id'], pool.apply_async(extract_worker, (args,))))
        
        # Collect results with timeout
        for process_id, async_result in async_results:
            try:
                result = async_result.get(timeout=worker_timeout)
                results.append(result)
                
                if result['success']:
                    all_records.extend(result['records'])
                    logger.info(f"✅ P{result['process_id']} done: {result['records_count']} records")
                else:
                    logger.error(f"❌ P{result['process_id']} failed: {result['error']}")
            except mp.TimeoutError:
                logger.error(f"❌ P{process_id} TIMEOUT after {worker_timeout}s - skipping")
                results.append({
                    'process_id': process_id,
                    'records': [],
                    'records_count': 0,
                    'success': False,
                    'error': f'Timeout after {worker_timeout}s'
                })
            except Exception as e:
                logger.error(f"❌ P{process_id} ERROR: {e}")
                results.append({
                    'process_id': process_id,
                    'records': [],
                    'records_count': 0,
                    'success': False,
                    'error': str(e)
                })
    
    # Create DataFrame
    logger.info(f"\n📦 Consolidating {len(all_records)} records...")
    
    if all_records:
        df = pd.DataFrame(all_records)
    else:
        df = pd.DataFrame()
    
    # Save to CSV
    if output_path and not df.empty:
        import os
        
        if append_mode and os.path.exists(output_path):
            # Append without header
            df.to_csv(
                output_path,
                mode='a',
                header=False,
                index=False,
                encoding='utf-8-sig',
                sep=';',
                decimal=','
            )
            logger.info(f"📎 Appended to: {output_path}")
        else:
            # Write new file with header
            df.to_csv(
                output_path,
                index=False,
                encoding='utf-8-sig',
                sep=';',
                decimal=','
            )
            logger.info(f"💾 Saved: {output_path}")
    
    elapsed = time.time() - start_time
    
    stats = {
        'total_records': len(df),
        'elapsed_seconds': elapsed,
        'successful_processes': sum(1 for r in results if r['success']),
        'failed_processes': sum(1 for r in results if not r['success']),
        'records_per_second': len(df) / elapsed if elapsed > 0 else 0
    }
    
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ COMPLETE!")
    logger.info(f"{'='*80}")
    logger.info(f"Records: {stats['total_records']:,}")
    logger.info(f"Time: {elapsed/60:.1f} min ({stats['records_per_second']:.1f} rec/s)")
    logger.info(f"Processes: {stats['successful_processes']}/{num_processes} successful")
    
    return df, stats


def main():
    parser = argparse.ArgumentParser(description='TJRJ Precatórios Scraper V4 - Fast Extraction')
    
    parser.add_argument('--entity-id', type=int, required=True, help='Entity ID')
    parser.add_argument('--entity-name', type=str, default='Unknown', help='Entity name')
    parser.add_argument('--regime', choices=['geral', 'especial'], default='especial')
    parser.add_argument('--total-pages', type=int, required=True, help='Total pages')
    parser.add_argument('--num-processes', type=int, default=4, help='Parallel processes (2-6)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout per worker (minutes)')
    parser.add_argument('--output', type=str, help='Output CSV path')
    parser.add_argument('--append', action='store_true', help='Append to existing file')
    parser.add_argument('--no-headless', action='store_true', help='Show browser')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    # Generate output path - use regime name, not entity name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = args.output or f"output/precatorios_regime_{args.regime}_{timestamp}.csv"
    
    # Run extraction
    df, stats = run_parallel_extraction(
        entity_id=args.entity_id,
        entity_name=args.entity_name,
        regime=args.regime,
        total_pages=args.total_pages,
        num_processes=args.num_processes,
        skip_expanded=True,  # Always fast mode
        headless=not args.no_headless,
        timeout_minutes=args.timeout,
        output_path=output_path,
        append_mode=args.append
    )
    
    return 0 if stats['failed_processes'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
