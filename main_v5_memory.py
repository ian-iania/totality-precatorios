"""
TJRJ Precatórios Scraper V5 - Full Memory Mode

Key improvements:
- ALL data accumulated in a single list in memory
- NO intermediate I/O - only one CSV write at the very end
- Validation: expected records vs actual records
- Sorted by (entidade_devedora, ordem) at the end

Usage:
    python main_v5_memory.py --entities-json '[{"id":1,"name":"...","pages":10},...]' --regime geral
"""

import sys
import time
import json
import argparse
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
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
    
    # File output - single file for all
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "scraper_v3.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}",
        level=level,
        rotation="10 MB"
    )


def extract_entity_worker(args: Dict) -> Dict:
    """
    Worker function to extract ALL pages of a single entity.
    Returns all records in memory.
    """
    entity_id = args['entity_id']
    entity_name = args['entity_name']
    regime = args['regime']
    total_pages = args['total_pages']
    headless = args.get('headless', True)
    timeout_minutes = args.get('timeout_minutes', 30)
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    all_records = []
    
    try:
        # Initialize scraper
        config = ScraperConfig(
            headless=headless,
            max_retries=3,
            use_cache=True,
            skip_expanded_details=True
        )
        scraper = TJRJPrecatoriosScraperV3(regime=regime, config=config)
        
        # Create entity object
        entidade = EntidadeDevedora(
            id=entity_id,
            nome=entity_name,
            precatorios_pendentes=total_pages * 10,
            precatorios_pagos=0,
            total=total_pages * 10
        )
        
        logger.info(f"[E{entity_id}] 🌐 Starting {entity_name} ({total_pages} pages)")
        
        with scraper.playwright_context() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to entity page
            url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entity_id}"
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for table
            try:
                page.wait_for_selector("text=/Número.*Precatório/i", timeout=15000)
            except:
                pass
            page.wait_for_timeout(2000)
            
            logger.info(f"[E{entity_id}] ✅ Page loaded")
            
            # Extract all pages
            current_page = 1
            while current_page <= total_pages:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    logger.warning(f"[E{entity_id}] ⏰ Timeout after {timeout_minutes}min")
                    break
                
                # Extract current page
                precatorios = scraper._extract_precatorios_from_page(page, entidade)
                
                for prec in precatorios:
                    all_records.append(prec.model_dump())
                
                if current_page % 10 == 0 or current_page == total_pages:
                    logger.info(f"[E{entity_id}] Page {current_page}/{total_pages} - {len(all_records)} records")
                
                # Navigate to next page if not last
                if current_page < total_pages:
                    next_selectors = [
                        'a[ng-click="vm.ProximaPagina()"]',
                        'text=Próxima',
                        'a:has-text("Próxima")',
                    ]
                    
                    # Wait for overlay
                    try:
                        page.wait_for_selector('.block-ui-overlay', state='hidden', timeout=3000)
                    except:
                        pass
                    
                    clicked = False
                    for selector in next_selectors:
                        try:
                            btn = page.query_selector(selector)
                            if btn and btn.is_visible():
                                btn.click()
                                page.wait_for_timeout(1500)
                                clicked = True
                                break
                        except:
                            continue
                    
                    if not clicked:
                        logger.warning(f"[E{entity_id}] ⚠️ Next button not found on page {current_page}")
                        break
                
                current_page += 1
            
            # Close browser
            try:
                context.close()
                browser.close()
            except:
                pass
        
        elapsed = time.time() - start_time
        logger.info(f"[E{entity_id}] ✅ Complete: {len(all_records)} records in {elapsed/60:.1f}min")
        
        return {
            'entity_id': entity_id,
            'entity_name': entity_name,
            'records': all_records,
            'records_count': len(all_records),
            'expected_records': total_pages * 10,
            'elapsed_seconds': elapsed,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[E{entity_id}] ❌ Failed: {e}")
        return {
            'entity_id': entity_id,
            'entity_name': entity_name,
            'records': all_records,
            'records_count': len(all_records),
            'expected_records': total_pages * 10,
            'elapsed_seconds': elapsed,
            'success': False,
            'error': str(e)
        }


def run_full_extraction(
    entities: List[Dict],
    regime: str,
    max_concurrent: int = 4,
    headless: bool = True,
    timeout_minutes: int = 30,
    output_path: str = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Extract ALL entities, accumulate in memory, write CSV once at the end.
    
    Args:
        entities: List of {"id": int, "name": str, "pages": int}
        regime: 'geral' or 'especial'
        max_concurrent: Max concurrent entity extractions
        headless: Run browsers headless
        timeout_minutes: Timeout per entity
        output_path: Final CSV path
    
    Returns:
        (DataFrame, stats)
    """
    start_time = time.time()
    
    # Calculate totals for validation
    total_expected_records = sum(e['pages'] * 10 for e in entities)
    total_pages = sum(e['pages'] for e in entities)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 V5 FULL MEMORY EXTRACTION - {regime.upper()}")
    logger.info(f"{'='*80}")
    logger.info(f"Entities: {len(entities)}")
    logger.info(f"Total pages: {total_pages:,}")
    logger.info(f"Expected records: {total_expected_records:,}")
    logger.info(f"Concurrent workers: {max_concurrent}")
    logger.info(f"{'='*80}\n")
    
    # Prepare worker args
    worker_args = []
    for entity in entities:
        worker_args.append({
            'entity_id': entity['id'],
            'entity_name': entity['name'],
            'regime': regime,
            'total_pages': entity['pages'],
            'headless': headless,
            'timeout_minutes': timeout_minutes
        })
    
    # Global accumulator - simple list
    all_records = []
    results = []
    
    # Process entities with limited concurrency
    ctx = mp.get_context('spawn')
    worker_timeout = timeout_minutes * 60
    
    with ctx.Pool(processes=max_concurrent) as pool:
        # Submit all entities
        async_results = []
        for args in worker_args:
            async_results.append((args['entity_id'], args['entity_name'], pool.apply_async(extract_entity_worker, (args,))))
        
        # Collect results with polling (avoid deadlocks)
        pending = list(async_results)
        
        while pending:
            still_pending = []
            for entity_id, entity_name, async_result in pending:
                try:
                    result = async_result.get(timeout=1.0)
                    results.append(result)
                    
                    if result['success']:
                        all_records.extend(result['records'])
                        logger.info(f"✅ {result['entity_name']}: {result['records_count']} records")
                    else:
                        logger.error(f"❌ {result['entity_name']}: {result['error']}")
                        # Still add partial records
                        all_records.extend(result['records'])
                        
                except mp.TimeoutError:
                    still_pending.append((entity_id, entity_name, async_result))
                except Exception as e:
                    logger.error(f"❌ {entity_name} ERROR: {e}")
                    results.append({
                        'entity_id': entity_id,
                        'entity_name': entity_name,
                        'records': [],
                        'records_count': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            pending = still_pending
            if pending:
                # Log progress
                done = len(entities) - len(pending)
                logger.info(f"⏳ Progress: {done}/{len(entities)} entities complete, {len(all_records):,} records in memory")
                time.sleep(5)  # Check every 5 seconds
    
    # === VALIDATION ===
    actual_records = len(all_records)
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 VALIDATION")
    logger.info(f"{'='*80}")
    logger.info(f"Expected records: {total_expected_records:,}")
    logger.info(f"Actual records:   {actual_records:,}")
    
    if actual_records == total_expected_records:
        logger.info(f"✅ PERFECT MATCH!")
    elif actual_records > total_expected_records * 0.95:
        logger.warning(f"⚠️ Minor difference: {total_expected_records - actual_records} records missing ({100*actual_records/total_expected_records:.1f}%)")
    else:
        logger.error(f"❌ SIGNIFICANT DIFFERENCE: {total_expected_records - actual_records} records missing ({100*actual_records/total_expected_records:.1f}%)")
    
    # === SORT AND SAVE ===
    logger.info(f"\n📦 Creating DataFrame with {actual_records:,} records...")
    
    if all_records:
        df = pd.DataFrame(all_records)
        
        # Sort by entidade_devedora and ordem
        if 'entidade_devedora' in df.columns and 'ordem' in df.columns:
            try:
                # Convert ordem to sortable int
                df['ordem_sort'] = df['ordem'].str.replace('º', '').str.replace('°', '').astype(int)
                df = df.sort_values(['entidade_devedora', 'ordem_sort'])
                df = df.drop(columns=['ordem_sort'])
                logger.info(f"📊 Sorted by (entidade_devedora, ordem)")
            except Exception as e:
                logger.warning(f"⚠️ Sort failed: {e}")
    else:
        df = pd.DataFrame()
    
    # === SINGLE CSV WRITE ===
    if output_path and not df.empty:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
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
        'total_entities': len(entities),
        'successful_entities': sum(1 for r in results if r['success']),
        'failed_entities': sum(1 for r in results if not r['success']),
        'expected_records': total_expected_records,
        'actual_records': actual_records,
        'match_percent': 100 * actual_records / total_expected_records if total_expected_records > 0 else 0,
        'elapsed_seconds': elapsed,
        'records_per_second': actual_records / elapsed if elapsed > 0 else 0
    }
    
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ EXTRACTION COMPLETE!")
    logger.info(f"{'='*80}")
    logger.info(f"Entities: {stats['successful_entities']}/{stats['total_entities']} successful")
    logger.info(f"Records: {stats['actual_records']:,} ({stats['match_percent']:.1f}% of expected)")
    logger.info(f"Time: {elapsed/60:.1f} min ({stats['records_per_second']:.1f} rec/s)")
    logger.info(f"{'='*80}\n")
    
    return df, stats


def main():
    parser = argparse.ArgumentParser(description='TJRJ Precatórios Scraper V5 - Full Memory Mode')
    
    parser.add_argument('--entities-json', type=str, required=True, 
                       help='JSON array of entities: [{"id":1,"name":"...","pages":10},...]')
    parser.add_argument('--regime', choices=['geral', 'especial'], required=True)
    parser.add_argument('--max-concurrent', type=int, default=4, help='Max concurrent entity extractions')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout per entity (minutes)')
    parser.add_argument('--output', type=str, help='Output CSV path')
    parser.add_argument('--no-headless', action='store_true', help='Show browser')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    # Parse entities
    try:
        entities = json.loads(args.entities_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return 1
    
    # Filter entities with pages > 0
    entities = [e for e in entities if e.get('pages', 0) > 0]
    
    if not entities:
        logger.error("No entities to process")
        return 1
    
    # Generate output path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = args.output or f"output/precatorios_{args.regime}_{timestamp}.csv"
    
    # Run extraction
    df, stats = run_full_extraction(
        entities=entities,
        regime=args.regime,
        max_concurrent=args.max_concurrent,
        headless=not args.no_headless,
        timeout_minutes=args.timeout,
        output_path=output_path
    )
    
    return 0 if stats['failed_entities'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
