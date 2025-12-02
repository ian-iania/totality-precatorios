#!/usr/bin/env python3
"""
V6 Orchestrator - Full Extraction Workflow

This script orchestrates the complete extraction process:
1. Run main extraction (V5)
2. Detect gaps (failed entities)
3. Recover gaps if any
4. Merge and finalize output

Usage:
    python main_v6_orchestrator.py --regime especial --num-processes 10
    python main_v6_orchestrator.py --regime geral --num-processes 5
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from loguru import logger

# Import gap recovery functions
from gap_recovery import (
    detect_failed_entities,
    recover_failed_entities,
    merge_and_finalize,
    get_extraction_summary
)


def setup_logging():
    """Configure logging for orchestrator."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/orchestrator_v6.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB"
    )


def run_main_extraction(regime: str, num_processes: int, timeout: int = 60, entity_id: int = None) -> Tuple[bool, str]:
    """
    Run the main V5 extraction as a subprocess.
    
    Args:
        regime: 'geral' or 'especial'
        num_processes: Number of parallel workers
        timeout: Timeout per entity in minutes
        entity_id: Optional single entity ID to extract
        
    Returns:
        Tuple of (success, output_csv_path)
    """
    logger.info("=" * 60)
    logger.info("PHASE 1: MAIN EXTRACTION")
    logger.info("=" * 60)
    logger.info(f"Regime: {regime}")
    logger.info(f"Workers: {num_processes}")
    logger.info(f"Timeout: {timeout} min/entity")
    if entity_id:
        logger.info(f"Entity ID: {entity_id} (single entity mode)")
    
    cmd = [
        sys.executable,
        "main_v5_all_entities.py",
        "--regime", regime,
        "--num-processes", str(num_processes),
        "--timeout", str(timeout)
    ]
    
    if entity_id:
        cmd.extend(["--entity-id", str(entity_id)])
    
    logger.info(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Let output flow to console
            text=True,
            cwd=Path(__file__).parent
        )
        
        elapsed = (time.time() - start_time) / 60
        
        if result.returncode == 0:
            logger.success(f"Main extraction completed in {elapsed:.1f} min")
            
            # Find the output CSV
            output_dir = Path("output")
            pattern = f"precatorios_{regime}_*.csv"
            csv_candidates = [p for p in output_dir.glob(pattern) if "_COMPLETE_" not in p.stem]
            csv_files = sorted(csv_candidates, key=lambda x: x.stat().st_mtime, reverse=True)
            
            if csv_files:
                output_csv = str(csv_files[0])
                logger.info(f"Output CSV: {output_csv}")
                return True, output_csv
            else:
                logger.warning("No output CSV found")
                return True, ""
        else:
            logger.error(f"Main extraction failed with code {result.returncode}")
            return False, ""
            
    except Exception as e:
        logger.error(f"Error running main extraction: {e}")
        return False, ""


def run_gap_detection(log_file: str = "logs/scraper_v3.log") -> Tuple[list, Dict]:
    """
    Detect failed entities from extraction logs.
    
    Args:
        log_file: Path to scraper log file
        
    Returns:
        Tuple of (failed_entities_list, summary_dict)
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 2: GAP DETECTION")
    logger.info("=" * 60)
    
    if not Path(log_file).exists():
        logger.error(f"Log file not found: {log_file}")
        return [], {}
    
    failed = detect_failed_entities(log_file)
    summary = get_extraction_summary(log_file)
    
    logger.info(f"Total entities: {summary.get('total_entities', 0)}")
    logger.info(f"Successful: {summary.get('successful', 0)}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total records: {summary.get('total_records', 0):,}")
    logger.info(f"Completeness: {summary.get('completeness', 0):.2f}%")
    
    if failed:
        logger.warning("Failed entities:")
        for f in failed:
            logger.warning(f"  - {f['name']} (ID: {f['id']}): {f['reason']}")
    else:
        logger.success("No failed entities detected!")
    
    return failed, summary


def run_gap_recovery(
    failed_entities: list,
    regime: str,
    num_processes: int = 5,
    timeout_minutes: int = 10
) -> Tuple[int, Optional[str]]:
    """
    Recover failed entities.
    
    Args:
        failed_entities: List of failed entity dicts
        regime: 'geral' or 'especial'
        num_processes: Workers for recovery
        timeout_minutes: Timeout per entity
        
    Returns:
        Tuple of (records_recovered, gaps_csv_path)
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 3: GAP RECOVERY")
    logger.info("=" * 60)
    
    if not failed_entities:
        logger.info("No gaps to recover - skipping")
        return 0, None
    
    logger.info(f"Recovering {len(failed_entities)} failed entities...")
    
    records, csv_path = recover_failed_entities(
        failed_entities=failed_entities,
        regime=regime,
        num_processes=num_processes,
        timeout_minutes=timeout_minutes
    )
    
    if records:
        logger.success(f"Recovered {len(records)} records")
        logger.info(f"Gaps CSV: {csv_path}")
        return len(records), csv_path
    else:
        logger.info("No records recovered (entities may be legitimately empty)")
        return 0, None


def run_merge_and_finalize(
    main_csv: str,
    gaps_csv: Optional[str] = None
) -> Dict:
    """
    Merge main extraction with recovered gaps and finalize.
    
    Args:
        main_csv: Path to main extraction CSV
        gaps_csv: Optional path to gaps CSV
        
    Returns:
        Result dict with final stats
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 4: MERGE & FINALIZE")
    logger.info("=" * 60)
    
    if not main_csv or not Path(main_csv).exists():
        logger.error(f"Main CSV not found: {main_csv}")
        return {"success": False, "error": "Main CSV not found"}
    
    logger.info(f"Main CSV: {main_csv}")
    if gaps_csv:
        logger.info(f"Gaps CSV: {gaps_csv}")
    else:
        logger.info("No gaps CSV to merge")
    
    result = merge_and_finalize(main_csv, gaps_csv)
    
    if result.get("success"):
        logger.success(f"Final output: {result.get('output_csv')}")
        logger.success(f"Total records: {result.get('total_records'):,}")
        logger.info(f"Duplicates removed: {result.get('duplicates_removed', 0)}")
    else:
        logger.error(f"Merge failed: {result.get('error')}")
    
    return result


def run_full_workflow(
    regime: str,
    num_processes: int = 10,
    timeout: int = 60,
    skip_extraction: bool = False,
    main_csv: str = None,
    entity_id: int = None
) -> Dict:
    """
    Run the complete V6 extraction workflow.
    
    Args:
        regime: 'geral' or 'especial'
        num_processes: Number of parallel workers
        timeout: Timeout per entity in minutes
        skip_extraction: If True, skip main extraction (use existing CSV)
        main_csv: Path to existing main CSV (if skip_extraction=True)
        entity_id: Optional single entity ID to extract
        
    Returns:
        Result dict with workflow stats
    """
    start_time = time.time()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("V6 ORCHESTRATOR - FULL WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Regime: {regime}")
    logger.info(f"Workers: {num_processes}")
    if entity_id:
        logger.info(f"Entity ID: {entity_id} (single entity mode)")
    
    result = {
        "regime": regime,
        "start_time": datetime.now().isoformat(),
        "entity_id": entity_id,
        "phases": {}
    }
    
    # Phase 1: Main Extraction
    if skip_extraction and main_csv:
        logger.info("Skipping main extraction (using provided CSV)")
        extraction_success = True
        output_csv = main_csv
    else:
        extraction_success, output_csv = run_main_extraction(regime, num_processes, timeout, entity_id)
    
    result["phases"]["extraction"] = {
        "success": extraction_success,
        "output_csv": output_csv
    }
    
    if not extraction_success:
        result["success"] = False
        result["error"] = "Main extraction failed"
        return result
    
    # Phase 2: Gap Detection
    failed_entities, summary = run_gap_detection()
    result["phases"]["detection"] = {
        "total_entities": summary.get("total_entities", 0),
        "failed_count": len(failed_entities),
        "completeness": summary.get("completeness", 0)
    }
    
    # Phase 3: Gap Recovery
    recovered_count, gaps_csv = run_gap_recovery(
        failed_entities, 
        regime, 
        num_processes=min(5, num_processes),
        timeout_minutes=10
    )
    result["phases"]["recovery"] = {
        "attempted": len(failed_entities),
        "recovered_records": recovered_count,
        "gaps_csv": gaps_csv
    }
    
    # Phase 4: Merge & Finalize
    merge_result = run_merge_and_finalize(output_csv, gaps_csv)
    result["phases"]["merge"] = merge_result
    
    # Final summary
    elapsed = (time.time() - start_time) / 60
    result["success"] = merge_result.get("success", False)
    result["total_time_min"] = round(elapsed, 1)
    result["final_output"] = merge_result.get("output_csv")
    result["total_records"] = merge_result.get("total_records", 0)
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total time: {elapsed:.1f} min")
    logger.info(f"Final records: {result['total_records']:,}")
    logger.info(f"Output: {result['final_output']}")
    
    if failed_entities and recovered_count == 0:
        logger.info(f"Note: {len(failed_entities)} entities had no data (legitimately empty)")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="V6 Orchestrator - Full Extraction Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Full extraction for especial regime
    python main_v6_orchestrator.py --regime especial --num-processes 10
    
    # Full extraction for geral regime (smaller)
    python main_v6_orchestrator.py --regime geral --num-processes 5
    
    # Single entity extraction (e.g., Estado do RJ = ID 1)
    python main_v6_orchestrator.py --regime especial --entity-id 1 --num-processes 15
    
    # Skip extraction, just process existing CSV
    python main_v6_orchestrator.py --regime geral --skip-extraction --main-csv output/precatorios_geral_ALL_20251201.csv
        """
    )
    
    parser.add_argument(
        "--regime",
        type=str,
        choices=["geral", "especial"],
        default="especial",
        help="Regime to extract (default: especial)"
    )
    parser.add_argument(
        "--num-processes",
        type=int,
        default=10,
        help="Number of parallel workers (default: 10)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout per entity in minutes (default: 60)"
    )
    parser.add_argument(
        "--entity-id",
        type=int,
        help="Single entity ID to extract (e.g., 1 for Estado do RJ)"
    )
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip main extraction (use existing CSV)"
    )
    parser.add_argument(
        "--main-csv",
        type=str,
        help="Path to existing main CSV (use with --skip-extraction)"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    result = run_full_workflow(
        regime=args.regime,
        num_processes=args.num_processes,
        timeout=args.timeout,
        skip_extraction=args.skip_extraction,
        main_csv=args.main_csv,
        entity_id=args.entity_id
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
