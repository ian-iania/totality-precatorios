#!/usr/bin/env python3
"""
V6 Gap Recovery Module

This module provides functions for:
- Phase 1: Detecting failed entities from extraction logs
- Phase 2: Recovering failed entities by re-extraction
- Phase 3: Merging main extraction with recovered gaps

Usage:
    # Phase 1: Detect gaps
    from gap_recovery import detect_failed_entities, get_extraction_summary
    failed = detect_failed_entities('logs/scraper_v3.log', '2025-12-01 19:38')
    summary = get_extraction_summary('logs/scraper_v3.log', '2025-12-01 19:38')
    
    # Phase 2: Recover gaps
    from gap_recovery import recover_failed_entities
    records, path = recover_failed_entities(failed, 'especial')
    
    # Phase 3: Merge
    from gap_recovery import merge_and_finalize
    result = merge_and_finalize('main.csv', 'gaps.csv', 'output.csv')
"""

import re
import sys
import math
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from loguru import logger

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# PHASE 1: GAP DETECTION
# =============================================================================

def detect_failed_entities(log_file: str, start_time: str = None) -> List[Dict]:
    """
    Parse extraction log to find entities that failed.
    
    Detects:
    - Entities with 0 records extracted
    - Entities with timeout errors
    - Entities with Page.goto timeout errors
    
    Args:
        log_file: Path to scraper_v3.log
        start_time: Optional timestamp to filter logs (format: 'YYYY-MM-DD HH:MM')
                   If None, analyzes entire log file
    
    Returns:
        List of dicts: [{"id": 62, "name": "Município X", "reason": "timeout", "expected_records": 100}]
    """
    log_path = Path(log_file)
    if not log_path.exists():
        logger.error(f"Log file not found: {log_file}")
        return []
    
    # First pass: collect all entity info and their "Entity complete" records
    entities_info = {}  # {id: {"name": str, "expected": int}}
    entity_records = {}  # {id: records_count}
    entity_errors = {}  # {id: error_reason}
    
    current_entity_id = None
    previous_entity_id = None  # Track previous entity for "Entity complete" association
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Filter by start time if provided
            if start_time:
                ts_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
                if ts_match and ts_match.group(1) < start_time:
                    continue
            
            # Detect entity with ID: 🏛️ ENTITY: MUNICÍPIO DE X (ID: 62)
            entity_id_match = re.search(r'ENTITY:\s*(.+?)\s*\(ID:\s*(\d+)\)', line)
            if entity_id_match:
                previous_entity_id = current_entity_id  # Save previous before updating
                current_entity_id = int(entity_id_match.group(2))
                entity_name = entity_id_match.group(1).strip()
                entities_info[current_entity_id] = {"name": entity_name, "expected": 0}
                continue
            
            # Detect expected records: Pages: 7 | Workers: 5
            pages_match = re.search(r'Pages:\s*(\d+)\s*\|', line)
            if pages_match and current_entity_id:
                pages = int(pages_match.group(1))
                entities_info[current_entity_id]["expected"] = pages * 10
                continue
            
            # Detect entity complete summary: 📊 Entity complete: 29840 records
            # This line appears BEFORE the next entity starts, so associate with current_entity_id
            entity_complete_match = re.search(r'Entity complete:\s*(\d+)\s*records', line)
            if entity_complete_match and current_entity_id:
                records = int(entity_complete_match.group(1))
                entity_records[current_entity_id] = records
                continue
            
            # Detect timeout errors
            if current_entity_id and 'Timeout' in line and 'exceeded' in line:
                entity_errors[current_entity_id] = "timeout"
                continue
            
            # Detect Page.goto timeout
            if current_entity_id and 'Page.goto' in line and 'Timeout' in line:
                entity_errors[current_entity_id] = "page_timeout"
                continue
            
            # Detect 0 records in entity summary (must be exactly "0 records", not "10 records")
            # Pattern: "Entity complete: 0 records" or "Complete: 0 records"
            zero_records_match = re.search(r'(?:complete|Entity complete):\s*0\s*records', line, re.IGNORECASE)
            if current_entity_id and zero_records_match:
                if current_entity_id not in entity_errors:
                    entity_errors[current_entity_id] = "zero_records"
                continue
    
    # Build failed entities list
    failed_entities = []
    for entity_id, info in entities_info.items():
        records = entity_records.get(entity_id, 0)
        error = entity_errors.get(entity_id)
        expected = info.get("expected", 0)
        
        # Entity is successful if it has records > 0
        # Entity failed if:
        # 1. Has 0 records AND expected > 0 (extraction failed or empty page)
        # 2. Has explicit error AND 0 records (timeout with no data saved)
        # Note: If records > 0, entity is successful regardless of errors
        if records > 0:
            continue  # Success - has data
            
        # records == 0 at this point
        if expected > 0 or error:
            failed_entities.append({
                "id": entity_id,
                "name": info["name"],
                "reason": error or "zero_records",
                "expected_records": expected,
                "actual_records": records
            })
    
    logger.info(f"Detected {len(failed_entities)} failed entities out of {len(entities_info)} total")
    return failed_entities


def get_extraction_summary(log_file: str, start_time: str = None) -> Dict:
    """
    Get comprehensive extraction summary from log file.
    
    Args:
        log_file: Path to scraper_v3.log
        start_time: Optional timestamp to filter logs (format: 'YYYY-MM-DD HH:MM')
    
    Returns:
        Dict with:
        - total_entities: int
        - successful_entities: int
        - failed_entities: int
        - total_records: int
        - expected_records: int
        - failed_list: List[Dict]
        - regime: str
    """
    log_path = Path(log_file)
    if not log_path.exists():
        logger.error(f"Log file not found: {log_file}")
        return {}
    
    total_entities = 0
    total_records = 0
    expected_records = 0
    regime = "unknown"
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Filter by start time if provided
            if start_time:
                ts_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
                if ts_match and ts_match.group(1) < start_time:
                    continue
            
            # Detect regime
            regime_match = re.search(r'Regime:\s*(geral|especial)', line, re.IGNORECASE)
            if regime_match:
                regime = regime_match.group(1).lower()
            
            # Detect total entities: Entities: 41
            entities_match = re.search(r'Entities:\s*(\d+)', line)
            if entities_match:
                total_entities = int(entities_match.group(1))
            
            # Detect total pendentes: Total pendentes: 40,252
            pendentes_match = re.search(r'Total pendentes:\s*([\d,]+)', line)
            if pendentes_match:
                expected_records = int(pendentes_match.group(1).replace(',', ''))
            
            # Detect final total: Total records: 40,120
            total_match = re.search(r'Total records:\s*([\d,]+)', line)
            if total_match:
                total_records = int(total_match.group(1).replace(',', ''))
            
            # Alternative: Progress line with total
            progress_match = re.search(r'Progress:.*\|\s*([\d,]+)\s*total records', line)
            if progress_match:
                total_records = max(total_records, int(progress_match.group(1).replace(',', '')))
    
    # Get failed entities
    failed_list = detect_failed_entities(log_file, start_time)
    
    successful = total_entities - len(failed_list)
    
    return {
        "regime": regime,
        "total_entities": total_entities,
        "successful_entities": successful,
        "failed_entities": len(failed_list),
        "total_records": total_records,
        "expected_records": expected_records,
        "completeness_percent": round(total_records / expected_records * 100, 2) if expected_records > 0 else 0,
        "failed_list": failed_list
    }


# =============================================================================
# PHASE 2: GAP RECOVERY
# =============================================================================

def recover_failed_entities(
    failed_entities: List[Dict],
    regime: str,
    num_processes: int = 5,
    timeout_minutes: int = 10
) -> Tuple[List[Dict], str]:
    """
    Re-extract records for failed entities.
    
    Args:
        failed_entities: List from detect_failed_entities()
        regime: 'geral' or 'especial'
        num_processes: Workers per entity (default 5 for recovery)
        timeout_minutes: Timeout per entity (default 10 min for recovery)
    
    Returns:
        Tuple of (records_list, partial_csv_path)
    """
    if not failed_entities:
        logger.info("No failed entities to recover")
        return [], None
    
    # Import extract_single_entity from main_v5
    from main_v5_all_entities import extract_single_entity, load_entities_from_website
    
    logger.info(f"🔧 Recovering {len(failed_entities)} failed entities for regime: {regime}")
    
    # Load full entity list to get precatorios_pendentes for page calculation
    all_entities = load_entities_from_website(regime, headless=True)
    entity_lookup = {e['id']: e for e in all_entities}
    
    all_records = []
    recovery_stats = []
    
    for i, failed in enumerate(failed_entities, 1):
        entity_id = failed['id']
        entity_name = failed['name']
        
        # Get full entity info for page count
        entity_info = entity_lookup.get(entity_id)
        if not entity_info:
            logger.warning(f"⚠️ Entity {entity_id} not found in current entity list, skipping")
            continue
        
        # Calculate pages
        total_pages = math.ceil(entity_info['precatorios_pendentes'] / 10)
        if total_pages == 0:
            logger.info(f"⏭️ Skipping {entity_name} - 0 pages")
            continue
        
        logger.info(f"\n🔄 Recovery {i}/{len(failed_entities)}: {entity_name} (ID: {entity_id})")
        logger.info(f"   Pages: {total_pages}, Workers: {min(num_processes, total_pages)}")
        
        try:
            records, stats = extract_single_entity(
                entity_id=entity_id,
                entity_name=entity_name,
                regime=regime,
                total_pages=total_pages,
                num_processes=num_processes,
                headless=True,
                timeout_minutes=timeout_minutes
            )
            
            all_records.extend(records)
            recovery_stats.append({
                'id': entity_id,
                'name': entity_name,
                'records': len(records),
                'success': stats.get('success', False)
            })
            
            logger.info(f"   ✅ Recovered {len(records)} records")
            
        except Exception as e:
            logger.error(f"   ❌ Recovery failed: {e}")
            recovery_stats.append({
                'id': entity_id,
                'name': entity_name,
                'records': 0,
                'success': False,
                'error': str(e)
            })
    
    # Save recovered records to partial CSV
    partial_csv_path = None
    if all_records:
        import pandas as pd
        from datetime import datetime
        
        df = pd.DataFrame(all_records)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        partial_csv_path = f"output/partial/gaps_recovered_{timestamp}.csv"
        
        Path(partial_csv_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(partial_csv_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"\n💾 Saved {len(all_records)} recovered records to: {partial_csv_path}")
    
    # Summary
    successful = sum(1 for s in recovery_stats if s.get('success', False))
    logger.info(f"\n📊 Recovery Summary: {successful}/{len(failed_entities)} entities recovered")
    
    return all_records, partial_csv_path


# =============================================================================
# PHASE 3: MERGE & FINALIZE
# =============================================================================

def merge_and_finalize(
    main_csv: str,
    gaps_csv: str = None,
    output_path: str = None
) -> Dict:
    """
    Merge main extraction with recovered gaps and apply formatting.
    
    Args:
        main_csv: Path to main extraction CSV
        gaps_csv: Path to gaps CSV (can be None if no gaps)
        output_path: Path for final output (auto-generated if None)
    
    Returns:
        Dict with: total_records, duplicates_removed, output_file, excel_file
    """
    import pandas as pd
    from main_v5_all_entities import clean_ordem_column, format_monetary_columns, save_dataframe
    
    logger.info(f"📦 Merging and finalizing extraction...")
    
    # Load main CSV
    main_path = Path(main_csv)
    if not main_path.exists():
        raise FileNotFoundError(f"Main CSV not found: {main_csv}")
    
    df_main = pd.read_csv(main_csv, sep=';', encoding='utf-8-sig')
    logger.info(f"   Main CSV: {len(df_main)} records")
    
    initial_count = len(df_main)
    
    # Load and merge gaps CSV if provided
    if gaps_csv and Path(gaps_csv).exists():
        df_gaps = pd.read_csv(gaps_csv, encoding='utf-8-sig')
        logger.info(f"   Gaps CSV: {len(df_gaps)} records")
        
        # Concatenate
        df_combined = pd.concat([df_main, df_gaps], ignore_index=True)
        logger.info(f"   Combined: {len(df_combined)} records")
    else:
        df_combined = df_main
        logger.info(f"   No gaps CSV to merge")
    
    # Remove duplicates based on unique identifier
    # Try numero_precatorio first, then fall back to combination of fields
    before_dedup = len(df_combined)
    
    if 'numero_precatorio' in df_combined.columns:
        df_combined = df_combined.drop_duplicates(subset=['numero_precatorio'], keep='first')
    elif 'ordem' in df_combined.columns and 'entidade_devedora' in df_combined.columns:
        df_combined = df_combined.drop_duplicates(subset=['entidade_devedora', 'ordem'], keep='first')
    
    duplicates_removed = before_dedup - len(df_combined)
    if duplicates_removed > 0:
        logger.info(f"   Removed {duplicates_removed} duplicates")
    
    # Apply formatting
    df_combined = clean_ordem_column(df_combined)
    df_combined = format_monetary_columns(df_combined)
    
    # Sort
    sort_cols = []
    if 'entidade_devedora' in df_combined.columns:
        sort_cols.append('entidade_devedora')
    if 'ordem' in df_combined.columns:
        sort_cols.append('ordem')
    
    if sort_cols:
        df_combined = df_combined.sort_values(sort_cols)
        logger.info(f"   Sorted by: {', '.join(sort_cols)}")
    
    # Generate output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Extract regime from main CSV name
        regime = 'geral' if 'geral' in main_csv.lower() else 'especial'
        output_path = f"output/precatorios_{regime}_COMPLETE_{timestamp}.csv"
    
    # Save
    excel_path = save_dataframe(df_combined, output_path)
    
    result = {
        "total_records": len(df_combined),
        "initial_records": initial_count,
        "gaps_added": len(df_combined) - initial_count + duplicates_removed,
        "duplicates_removed": duplicates_removed,
        "output_file": output_path,
        "excel_file": str(excel_path)
    }
    
    logger.info(f"\n✅ Merge complete!")
    logger.info(f"   Total records: {result['total_records']}")
    logger.info(f"   Output: {output_path}")
    
    return result


# =============================================================================
# CLI FOR TESTING
# =============================================================================

def main():
    """CLI for testing gap detection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='V6 Gap Recovery - Detection Test')
    parser.add_argument('--log-file', default='logs/scraper_v3.log', help='Path to log file')
    parser.add_argument('--start-time', help='Filter logs from this time (YYYY-MM-DD HH:MM)')
    parser.add_argument('--summary', action='store_true', help='Show full summary')
    
    args = parser.parse_args()
    
    if args.summary:
        summary = get_extraction_summary(args.log_file, args.start_time)
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Regime: {summary.get('regime', 'unknown')}")
        print(f"Total Entities: {summary.get('total_entities', 0)}")
        print(f"Successful: {summary.get('successful_entities', 0)}")
        print(f"Failed: {summary.get('failed_entities', 0)}")
        print(f"Total Records: {summary.get('total_records', 0):,}")
        print(f"Expected Records: {summary.get('expected_records', 0):,}")
        print(f"Completeness: {summary.get('completeness_percent', 0)}%")
        
        if summary.get('failed_list'):
            print("\nFailed Entities:")
            for e in summary['failed_list']:
                print(f"  - ID {e['id']}: {e['name']} ({e['reason']})")
    else:
        failed = detect_failed_entities(args.log_file, args.start_time)
        print(f"\nDetected {len(failed)} failed entities:")
        for e in failed:
            print(f"  - ID {e['id']}: {e['name']} ({e['reason']})")


if __name__ == "__main__":
    main()
