#!/usr/bin/env python3
"""
Check for missing pages in extraction log and optionally fill gaps.
Usage: python check_gaps.py [--fill] [--log-file PATH]
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Set, Tuple

def parse_log_for_pages(log_path: str) -> Tuple[Set[int], int, str]:
    """
    Parse log file to find all successfully processed pages.
    Returns: (set of processed pages, total pages expected, entity name)
    """
    processed_pages = set()
    total_pages = 0
    entity_name = ""
    
    with open(log_path, 'r') as f:
        for line in f:
            # Match: [P1] Page 248/249 (248/249) followed by ✅ records
            # We need to track which pages had successful extraction
            page_match = re.search(r'\[P\d+\] Page (\d+)/(\d+)', line)
            if page_match:
                current_page = int(page_match.group(1))
                end_page = int(page_match.group(2))
                if end_page > total_pages:
                    total_pages = end_page
            
            # Match successful extraction: [P1]   ✅ 10 records
            if '✅' in line and 'records' in line:
                # The page was logged just before this line
                # We need to track the last page seen per worker
                pass
            
            # Match: Pages: 2984 | Workers: 12
            pages_match = re.search(r'Pages: (\d+) \| Workers:', line)
            if pages_match:
                total_pages = int(pages_match.group(1))
            
            # Match entity: ENTITY 1/41: Estado do Rio de Janeiro
            entity_match = re.search(r'ENTITY \d+/\d+: (.+)', line)
            if entity_match:
                entity_name = entity_match.group(1).strip()
    
    # Better approach: find all pages that had "✅ ... records" logged after them
    # Re-parse looking for page -> success pattern
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Find all successful extractions by looking at the pattern
    # [P1] Page 248/249 (248/249)
    # [P1]   ✅ 10 records (total: 2480) [2.3s]
    
    # Extract all pages that appear before a success message
    lines = content.split('\n')
    last_page_per_worker = {}
    
    for line in lines:
        # Track current page per worker
        page_match = re.search(r'\[P(\d+)\] Page (\d+)/\d+', line)
        if page_match:
            worker_id = page_match.group(1)
            page_num = int(page_match.group(2))
            last_page_per_worker[worker_id] = page_num
        
        # If we see success, mark that page as processed
        success_match = re.search(r'\[P(\d+)\]\s+✅.*records', line)
        if success_match:
            worker_id = success_match.group(1)
            if worker_id in last_page_per_worker:
                processed_pages.add(last_page_per_worker[worker_id])
    
    return processed_pages, total_pages, entity_name


def find_gaps(processed: Set[int], total: int) -> list:
    """Find missing pages"""
    expected = set(range(1, total + 1))
    missing = sorted(expected - processed)
    return missing


def main():
    parser = argparse.ArgumentParser(description='Check for missing pages in extraction')
    parser.add_argument('--log-file', default='logs/scraper_v3.log', help='Path to log file')
    parser.add_argument('--fill', action='store_true', help='Fill gaps by extracting missing pages')
    args = parser.parse_args()
    
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        sys.exit(1)
    
    print(f"📄 Analyzing log: {log_path}")
    processed, total, entity = parse_log_for_pages(str(log_path))
    
    print(f"📊 Entity: {entity}")
    print(f"📊 Total pages expected: {total}")
    print(f"📊 Pages processed: {len(processed)}")
    
    gaps = find_gaps(processed, total)
    
    if not gaps:
        print("✅ No gaps found! All pages were processed.")
        return
    
    print(f"⚠️  Missing pages ({len(gaps)}): {gaps[:20]}{'...' if len(gaps) > 20 else ''}")
    
    # Save gaps to file for fill_gaps.py
    gaps_file = Path('logs/missing_pages.txt')
    with open(gaps_file, 'w') as f:
        f.write(f"entity={entity}\n")
        f.write(f"total={total}\n")
        f.write(f"pages={','.join(map(str, gaps))}\n")
    print(f"💾 Gaps saved to: {gaps_file}")
    
    if args.fill:
        print("\n🔄 Starting gap filling...")
        import subprocess
        subprocess.run([sys.executable, 'fill_gaps.py'])


if __name__ == '__main__':
    main()
