#!/usr/bin/env python3
"""
Merge all partial CSVs and deduplicate by numero_precatorio.
Usage: python merge_csvs.py [--output NAME]
"""

import csv
import argparse
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

def merge_and_deduplicate(output_name: str = None):
    """Merge all CSVs from output/partial and deduplicate"""
    
    partial_dir = Path('output/partial')
    if not partial_dir.exists():
        print("❌ No partial directory found")
        return
    
    # Find all CSV files
    csv_files = list(partial_dir.glob('*.csv'))
    if not csv_files:
        print("❌ No CSV files found in output/partial/")
        return
    
    print(f"📄 Found {len(csv_files)} CSV files to merge")
    
    # Use OrderedDict to deduplicate by numero_precatorio while preserving order
    records_by_id = OrderedDict()
    total_read = 0
    duplicates = 0
    
    for csv_file in sorted(csv_files):
        print(f"   Reading: {csv_file.name}")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                total_read += 1
                key = row.get('numero_precatorio', '')
                
                if key and key in records_by_id:
                    duplicates += 1
                else:
                    records_by_id[key] = row
    
    print(f"\n📊 Statistics:")
    print(f"   Total records read: {total_read}")
    print(f"   Duplicates removed: {duplicates}")
    print(f"   Unique records: {len(records_by_id)}")
    
    # Generate output filename
    if output_name:
        output_file = Path(f'output/{output_name}.csv')
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = Path(f'output/precatorios_merged_{timestamp}.csv')
    
    # Write merged CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records_by_id.values())
    
    print(f"\n💾 Saved to: {output_file}")
    print(f"✅ Merge complete!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge and deduplicate CSVs')
    parser.add_argument('--output', help='Output filename (without .csv)')
    args = parser.parse_args()
    
    merge_and_deduplicate(args.output)
