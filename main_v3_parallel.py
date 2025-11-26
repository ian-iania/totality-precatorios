"""
Command-line interface for TJRJ Precatórios Scraper V3 (with page range parallelization)

This script orchestrates parallel extraction of precatórios by dividing large entities
into page ranges and processing them concurrently using multiprocessing.

V3 Features:
- Parallel extraction by page ranges (76-91% time reduction for Estado RJ)
- Multi-process orchestration using multiprocessing.Pool
- Automatic CSV merging with deduplication
- Gap/duplicate validation
- Compatible with V2's --skip-expanded flag (COMBO strategy)

Usage:
    # Extract Estado RJ with 4 parallel processes (complete with expanded fields)
    python main_v3_parallel.py --entity-id 1 --num-processes 4

    # Extract Estado RJ with 4 processes + skip-expanded (FASTEST - 91% reduction)
    python main_v3_parallel.py --entity-id 1 --num-processes 4 --skip-expanded

    # Extract specific page range (for manual parallelization)
    python main_v3_parallel.py --entity-id 1 --start-page 1 --end-page 746 --process-id 1

    # Custom output and visible browser
    python main_v3_parallel.py --entity-id 1 --num-processes 2 --output estado_rj_fast.csv --no-headless

Performance (Estado RJ - 2,984 pages):
    - V1 Sequential:           ~15h  (baseline)
    - V2 Sequential + skip:    ~7h   (53% reduction)
    - V3 Parallel (4 proc):    ~3.6h (76% reduction)
    - V3 Parallel + skip:      ~1.4h (91% reduction) ⭐ BEST
"""

import argparse
import sys
import os
from pathlib import Path
from loguru import logger
import pandas as pd
from datetime import datetime
import time
from typing import List, Tuple
import multiprocessing as mp
from playwright.sync_api import sync_playwright

from src.scraper_v3 import TJRJPrecatoriosScraperV3
from src.config import get_config
from src.models import ScraperConfig, EntidadeDevedora


def setup_logging(log_level: str):
    """Configure logging"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )


def divide_pages_into_ranges(total_pages: int, num_processes: int) -> List[Tuple[int, int]]:
    """
    Divide total pages into ranges for parallel processing

    Args:
        total_pages: Total number of pages (e.g., 2984 for Estado RJ)
        num_processes: Number of parallel processes (e.g., 2, 4)

    Returns:
        List of (start_page, end_page) tuples

    Example:
        >>> divide_pages_into_ranges(2984, 4)
        [(1, 746), (747, 1492), (1493, 2238), (2239, 2984)]
    """
    pages_per_process = total_pages // num_processes
    remainder = total_pages % num_processes

    ranges = []
    current_page = 1

    for i in range(num_processes):
        # Distribute remainder across first processes
        extra = 1 if i < remainder else 0
        pages_in_range = pages_per_process + extra

        start_page = current_page
        end_page = current_page + pages_in_range - 1

        ranges.append((start_page, end_page))
        current_page = end_page + 1

    return ranges


def extract_page_range_worker(args: dict) -> dict:
    """
    Worker function for multiprocessing.Pool

    This function runs in a separate process and extracts a specific page range.

    Args:
        args: Dictionary with keys:
            - entity_id: int
            - entity_name: str
            - regime: str
            - start_page: int
            - end_page: int
            - process_id: int
            - skip_expanded: bool
            - headless: bool
            - output_dir: str

    Returns:
        Dictionary with extraction results and metadata
    """
    entity_id = args['entity_id']
    entity_name = args['entity_name']
    regime = args['regime']
    start_page = args['start_page']
    end_page = args['end_page']
    process_id = args['process_id']
    skip_expanded = args['skip_expanded']
    headless = args['headless']
    output_dir = args['output_dir']

    logger.info(f"[P{process_id}] Worker started: pages {start_page}-{end_page}")

    start_time = time.time()
    precatorios_data = []

    try:
        # Create config for this process
        config = get_config()
        config.regime = regime
        config.headless = headless

        # Create scraper instance
        scraper = TJRJPrecatoriosScraperV3(config=config, skip_expanded=skip_expanded)

        # Create entidade object (needed for scraper methods)
        # Note: We don't have full entity stats here, just ID and name
        entidade = EntidadeDevedora(
            id_entidade=entity_id,
            nome_entidade=entity_name,
            regime=regime,
            precatorios_pagos=0,
            precatorios_pendentes=0,
            valor_prioridade=0,
            valor_rpv=0
        )

        # Launch browser and extract
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            try:
                # Navigate to entity page
                url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entity_id}"
                logger.info(f"[P{process_id}] Navigating to: {url}")
                page.goto(url, wait_until='networkidle', timeout=60000)

                # Wait for table to load (generous timeouts for AngularJS)
                logger.info(f"[P{process_id}] Waiting for table to load...")
                page.wait_for_timeout(5000)  # Initial wait for AngularJS
                try:
                    page.wait_for_selector("text=/Número.*Precatório/i", timeout=30000)
                    page.wait_for_selector("tbody tr td", timeout=30000)
                except:
                    logger.warning(f"[P{process_id}] Warning: table selectors not found, but continuing...")
                page.wait_for_timeout(3000)  # Extra stabilization

                # Extract page range
                precatorios = scraper.extract_page_range(
                    page=page,
                    entidade=entidade,
                    start_page=start_page,
                    end_page=end_page,
                    process_id=process_id
                )

                # Convert to dict for DataFrame
                for prec in precatorios:
                    precatorios_data.append(prec.model_dump())

                logger.info(f"[P{process_id}] ✅ Extracted {len(precatorios_data)} precatórios")

            finally:
                browser.close()

        # Save partial CSV
        elapsed = time.time() - start_time
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        partial_filename = f"partial_p{process_id}_{start_page}-{end_page}_{timestamp}.csv"
        partial_path = Path(output_dir) / partial_filename

        df = pd.DataFrame(precatorios_data)
        df.to_csv(partial_path, index=False, encoding='utf-8-sig', sep=';', decimal=',')

        logger.info(f"[P{process_id}] 💾 Saved partial CSV: {partial_path}")
        logger.info(f"[P{process_id}] ⏱️  Time: {elapsed/60:.1f}min ({len(precatorios_data)/elapsed:.2f} rec/s)")

        return {
            'process_id': process_id,
            'start_page': start_page,
            'end_page': end_page,
            'records_extracted': len(precatorios_data),
            'elapsed_seconds': elapsed,
            'partial_csv': str(partial_path),
            'success': True,
            'error': None
        }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[P{process_id}] ❌ Worker failed: {e}")

        return {
            'process_id': process_id,
            'start_page': start_page,
            'end_page': end_page,
            'records_extracted': 0,
            'elapsed_seconds': elapsed,
            'partial_csv': None,
            'success': False,
            'error': str(e)
        }


def merge_partial_csvs(partial_paths: List[str], output_path: str) -> pd.DataFrame:
    """
    Merge partial CSVs from parallel processes

    Args:
        partial_paths: List of paths to partial CSV files
        output_path: Path for final merged CSV

    Returns:
        Merged DataFrame
    """
    logger.info(f"\n{'='*80}")
    logger.info("📦 Merging partial CSVs...")
    logger.info(f"{'='*80}")

    dfs = []
    total_records = 0

    for i, path in enumerate(partial_paths, 1):
        if not path or not Path(path).exists():
            logger.warning(f"Skipping missing file: {path}")
            continue

        logger.info(f"[{i}/{len(partial_paths)}] Reading: {Path(path).name}")
        df = pd.read_csv(path, sep=';', decimal=',', encoding='utf-8-sig')
        dfs.append(df)
        total_records += len(df)
        logger.info(f"  Records: {len(df)}")

    if not dfs:
        logger.error("❌ No partial CSVs to merge!")
        return pd.DataFrame()

    # Merge all DataFrames
    merged_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"\n✅ Total records before deduplication: {len(merged_df)}")

    # Remove duplicates by numero_precatorio (should be unique)
    if 'numero_precatorio' in merged_df.columns:
        before_dedup = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['numero_precatorio'], keep='first')
        after_dedup = len(merged_df)
        duplicates = before_dedup - after_dedup

        if duplicates > 0:
            logger.warning(f"⚠️  Removed {duplicates} duplicate records")
        else:
            logger.info("✅ No duplicates found")

    # Save merged CSV
    merged_df.to_csv(
        output_path,
        index=False,
        encoding='utf-8-sig',
        sep=';',
        decimal=',',
        date_format='%Y-%m-%d'
    )

    logger.info(f"💾 Saved merged CSV: {output_path}")
    logger.info(f"   Final records: {len(merged_df)}")
    logger.info(f"   Size: {Path(output_path).stat().st_size / 1024:.1f} KB")

    return merged_df


def validate_data(df: pd.DataFrame):
    """
    Validate extracted data for gaps and inconsistencies

    Checks:
    - No duplicate numero_precatorio
    - ordem sequence is reasonable
    - No large gaps in data
    """
    logger.info(f"\n{'='*80}")
    logger.info("🔍 Validating data...")
    logger.info(f"{'='*80}")

    if df.empty:
        logger.error("❌ DataFrame is empty!")
        return

    # Check for duplicates
    if 'numero_precatorio' in df.columns:
        duplicates = df['numero_precatorio'].duplicated().sum()
        if duplicates > 0:
            logger.warning(f"⚠️  Found {duplicates} duplicate numero_precatorio!")
        else:
            logger.info("✅ No duplicates in numero_precatorio")

    # Check ordem sequence
    if 'ordem' in df.columns:
        # Extract numeric part of ordem (e.g., "2º" -> 2)
        df['ordem_num'] = df['ordem'].str.extract(r'(\d+)').astype(float)
        ordens = df['ordem_num'].dropna().sort_values()

        if len(ordens) > 0:
            min_ordem = int(ordens.min())
            max_ordem = int(ordens.max())
            expected_count = max_ordem - min_ordem + 1
            actual_count = len(ordens)

            logger.info(f"📊 Ordem range: {min_ordem} to {max_ordem}")
            logger.info(f"   Expected records: {expected_count}")
            logger.info(f"   Actual records: {actual_count}")

            gap_pct = ((expected_count - actual_count) / expected_count * 100) if expected_count > 0 else 0

            if gap_pct > 5:
                logger.warning(f"⚠️  Possible gaps: {gap_pct:.1f}% missing")
            else:
                logger.info(f"✅ Coverage: {100 - gap_pct:.1f}%")

    # Summary statistics
    logger.info(f"\n📈 Summary:")
    logger.info(f"   Total records: {len(df)}")

    if 'entidade_devedora' in df.columns:
        logger.info(f"   Unique entities: {df['entidade_devedora'].nunique()}")

    if 'saldo_atualizado' in df.columns:
        # Convert to numeric (it's already float from Decimal)
        valores = pd.to_numeric(df['saldo_atualizado'], errors='coerce')
        total_valor = valores.sum()
        logger.info(f"   Total value: R$ {total_valor:,.2f}")

    logger.info(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='TJRJ Precatórios Web Scraper V3 (with page range parallelization)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract Estado RJ with 4 parallel processes (complete)
  python main_v3_parallel.py --entity-id 1 --num-processes 4

  # Extract Estado RJ with 4 processes + skip-expanded (FASTEST)
  python main_v3_parallel.py --entity-id 1 --num-processes 4 --skip-expanded

  # Manual parallelization (run in separate terminals)
  python main_v3_parallel.py --entity-id 1 --start-page 1 --end-page 746 --process-id 1
  python main_v3_parallel.py --entity-id 1 --start-page 747 --end-page 1492 --process-id 2
        """
    )

    # Required arguments
    parser.add_argument(
        '--entity-id',
        type=int,
        required=True,
        help='Entity ID to extract (e.g., 1 for Estado RJ)'
    )

    # Page range options
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument(
        '--num-processes',
        type=int,
        help='Number of parallel processes (auto-divides pages). Recommended: 2-4'
    )
    range_group.add_argument(
        '--start-page',
        type=int,
        help='Start page for manual range extraction (use with --end-page)'
    )

    parser.add_argument(
        '--end-page',
        type=int,
        help='End page for manual range extraction (use with --start-page)'
    )

    parser.add_argument(
        '--total-pages',
        type=int,
        help='Total pages for the entity (required with --num-processes). Use browser to find this.'
    )

    parser.add_argument(
        '--process-id',
        type=int,
        help='Process ID for manual range extraction (for logging)'
    )

    # Optional arguments
    parser.add_argument(
        '--entity-name',
        type=str,
        default='Unknown Entity',
        help='Entity name for logging (e.g., "Estado do Rio de Janeiro")'
    )

    parser.add_argument(
        '--regime',
        choices=['geral', 'especial'],
        default='especial',
        help='Regime (default: especial, since Estado RJ is in especial)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV filename (auto-generated if not specified)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )

    parser.add_argument(
        '--skip-expanded',
        action='store_true',
        help='Skip extraction of 7 expanded fields (68%% faster). COMBO with parallelization for 91%% total reduction!'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.num_processes:
        if not args.total_pages:
            parser.error("--total-pages is required when using --num-processes")
        if args.num_processes < 2 or args.num_processes > 8:
            parser.error("--num-processes must be between 2 and 8")

    if args.start_page and not args.end_page:
        parser.error("--end-page is required when using --start-page")

    if args.end_page and not args.start_page:
        parser.error("--start-page is required when using --end-page")

    # Setup logging
    setup_logging(args.log_level)

    # Print banner
    logger.info("=" * 80)
    logger.info("🚀 TJRJ Precatórios Scraper V3 - Page Range Parallelization")
    logger.info("=" * 80)
    logger.info(f"Entity: {args.entity_name} (ID: {args.entity_id})")
    logger.info(f"Regime: {args.regime}")
    logger.info(f"Headless: {not args.no_headless}")

    if args.skip_expanded:
        logger.info(f"Mode: ⚡ FAST (skip expanded fields - 11 columns, ~68% faster)")
    else:
        logger.info(f"Mode: 📋 COMPLETE (with expanded fields - 19 columns)")

    logger.info("=" * 80)

    start_time = time.time()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    try:
        # MODE 1: Automatic parallelization (--num-processes)
        if args.num_processes:
            logger.info(f"\n🔀 Parallel mode: {args.num_processes} processes")
            logger.info(f"📄 Total pages: {args.total_pages}")

            # Divide pages into ranges
            ranges = divide_pages_into_ranges(args.total_pages, args.num_processes)

            logger.info(f"\n📊 Page ranges:")
            for i, (start, end) in enumerate(ranges, 1):
                pages_in_range = end - start + 1
                logger.info(f"  Process {i}: pages {start:,}-{end:,} ({pages_in_range:,} pages)")

            logger.info(f"\n{'='*80}")
            logger.info("🚀 Starting parallel extraction...")
            logger.info(f"{'='*80}\n")

            # Prepare worker arguments
            worker_args = []
            for i, (start, end) in enumerate(ranges, 1):
                worker_args.append({
                    'entity_id': args.entity_id,
                    'entity_name': args.entity_name,
                    'regime': args.regime,
                    'start_page': start,
                    'end_page': end,
                    'process_id': i,
                    'skip_expanded': args.skip_expanded,
                    'headless': not args.no_headless,
                    'output_dir': str(output_dir)
                })

            # Run in parallel
            with mp.Pool(processes=args.num_processes) as pool:
                results = pool.map(extract_page_range_worker, worker_args)

            # Check results
            logger.info(f"\n{'='*80}")
            logger.info("📊 Process Results:")
            logger.info(f"{'='*80}")

            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]

            for result in results:
                status = "✅" if result['success'] else "❌"
                logger.info(f"{status} Process {result['process_id']}: "
                          f"pages {result['start_page']}-{result['end_page']} - "
                          f"{result['records_extracted']} records in {result['elapsed_seconds']/60:.1f}min")

                if not result['success']:
                    logger.error(f"   Error: {result['error']}")

            if failed:
                logger.error(f"\n❌ {len(failed)} process(es) failed!")
                return 1

            # Merge partial CSVs
            partial_paths = [r['partial_csv'] for r in successful]
            output_filename = args.output or f"precatorios_{args.entity_name.replace(' ', '_')}_{timestamp}.csv"
            output_path = output_dir / output_filename

            merged_df = merge_partial_csvs(partial_paths, str(output_path))

            # Validate
            validate_data(merged_df)

        # MODE 2: Manual range extraction (--start-page --end-page)
        elif args.start_page and args.end_page:
            logger.info(f"\n📄 Manual range mode: pages {args.start_page}-{args.end_page}")

            worker_args = {
                'entity_id': args.entity_id,
                'entity_name': args.entity_name,
                'regime': args.regime,
                'start_page': args.start_page,
                'end_page': args.end_page,
                'process_id': args.process_id or 1,
                'skip_expanded': args.skip_expanded,
                'headless': not args.no_headless,
                'output_dir': str(output_dir)
            }

            result = extract_page_range_worker(worker_args)

            if not result['success']:
                logger.error(f"❌ Extraction failed: {result['error']}")
                return 1

            logger.info(f"\n✅ Extraction complete: {result['records_extracted']} records")
            logger.info(f"💾 Saved to: {result['partial_csv']}")

        else:
            parser.error("Either --num-processes or --start-page/--end-page must be specified")

        # Final summary
        elapsed = time.time() - start_time
        logger.info(f"\n{'='*80}")
        logger.info("✅ SUCCESS!")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️  Total time: {elapsed/3600:.2f}h ({elapsed/60:.1f}min)")

        if args.num_processes:
            logger.info(f"📊 Total records: {len(merged_df)}")
            logger.info(f"💾 Output file: {output_path}")

        logger.info(f"{'='*80}\n")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
