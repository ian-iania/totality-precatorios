#!/usr/bin/env python3
"""
Fill missing pages identified by check_gaps.py
Uses a single browser to extract only the missing pages.
"""

import sys
import csv
import time
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper_v3 import TJRJPrecatoriosScraperV3
from models import EntidadeDevedora
from config import ScraperConfig


def load_gaps() -> tuple:
    """Load gaps from file created by check_gaps.py"""
    gaps_file = Path('logs/missing_pages.txt')
    if not gaps_file.exists():
        logger.error("❌ No gaps file found. Run check_gaps.py first.")
        sys.exit(1)
    
    entity = ""
    entity_id = "1"  # Default Estado do RJ
    total = 0
    pages = []
    
    with open(gaps_file, 'r') as f:
        for line in f:
            if line.startswith('entity='):
                entity = line.split('=', 1)[1].strip()
            elif line.startswith('entity_id='):
                entity_id = line.split('=', 1)[1].strip()
            elif line.startswith('total='):
                total = int(line.split('=', 1)[1].strip())
            elif line.startswith('pages='):
                pages_str = line.split('=', 1)[1].strip()
                if pages_str:
                    pages = [int(p) for p in pages_str.split(',')]
    
    return entity, entity_id, total, pages


def fill_gaps():
    """Extract only the missing pages"""
    entity_name, entity_id, total_pages, missing_pages = load_gaps()
    
    if not missing_pages:
        logger.info("✅ No gaps to fill!")
        return
    
    logger.info(f"🔧 Filling {len(missing_pages)} missing pages for: {entity_name}")
    logger.info(f"📄 Pages to process: {missing_pages}")
    
    # Determine regime based on entity
    regime = "especial"  # Default for Estado do RJ
    
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
    
    # Initialize scraper
    config = ScraperConfig(headless=True)
    scraper = TJRJPrecatoriosScraperV3(config=config, skip_expanded=True)
    
    all_records = []
    failed_pages = []
    
    with sync_playwright() as p:
        logger.info("🌐 Starting browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        page.set_default_timeout(15000)  # 15s timeout for gap filling
        
        try:
            # Navigate to entity page (same as main_v5)
            entity_url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entity_id}"
            logger.info(f"🔍 Navigating to: {entity_url}")
            page.goto(entity_url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(3000)
            logger.info("✅ Entity page loaded")
            
            # Process each missing page
            for i, page_num in enumerate(missing_pages):
                logger.info(f"📄 Processing page {page_num} ({i+1}/{len(missing_pages)})")
                
                start_time = time.time()
                
                try:
                    # Navigate to page
                    if not scraper.goto_page_direct(page, page_num):
                        logger.warning(f"⚠️ Failed to navigate to page {page_num}")
                        failed_pages.append(page_num)
                        continue
                    
                    # Extract records
                    records = scraper._extract_precatorios_from_page(page, entidade)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"✅ Page {page_num}: {len(records)} records [{elapsed:.1f}s]")
                    
                    for rec in records:
                        all_records.append(rec.model_dump())
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.warning(f"⚠️ Error on page {page_num} after {elapsed:.1f}s: {e}")
                    failed_pages.append(page_num)
                    
                    # Try to recover
                    if elapsed > 10:
                        logger.info("🔄 Attempting recovery...")
                        try:
                            page.reload()
                            page.wait_for_timeout(2000)
                        except:
                            pass
            
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            browser.close()
    
    # Save results
    if all_records:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = Path(f'output/partial/gaps_{timestamp}.csv')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
            writer.writeheader()
            writer.writerows(all_records)
        
        logger.info(f"💾 Saved {len(all_records)} records to: {output_file}")
    
    # Report
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 Gap filling complete!")
    logger.info(f"   Pages processed: {len(missing_pages) - len(failed_pages)}/{len(missing_pages)}")
    logger.info(f"   Records extracted: {len(all_records)}")
    
    if failed_pages:
        logger.warning(f"   ⚠️ Still missing: {failed_pages}")
        with open('logs/still_missing.txt', 'w') as f:
            f.write(','.join(map(str, failed_pages)))
    else:
        logger.info(f"   ✅ All gaps filled!")


if __name__ == '__main__':
    fill_gaps()
