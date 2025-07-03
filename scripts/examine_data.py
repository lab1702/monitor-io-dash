#!/usr/bin/env python3
"""
Script to examine the structure of CSV files from the monitor-io device.

This utility script helps analyze the data structure and format of CSV files
from monitor-io devices, useful for debugging data processing issues.

Usage:
    python scripts/examine_data.py
"""

import sys
import os
import pandas as pd

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher import MonitorIODataFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def examine_csv_structure():
    """Examine all CSV files to understand data structure"""
    fetcher = MonitorIODataFetcher()
    
    # Get all CSV links
    csv_links = fetcher.get_csv_links()
    
    if not csv_links:
        print("No CSV files found!")
        return
    
    print(f"Found {len(csv_links)} CSV files to examine:")
    for i, link in enumerate(csv_links, 1):
        print(f"{i}. {link}")
    
    print("\n" + "="*80)
    print("EXAMINING CSV STRUCTURE")
    print("="*80)
    
    all_columns = set()
    file_analysis = []
    
    for i, csv_url in enumerate(csv_links, 1):
        print(f"\n--- File {i}/{len(csv_links)}: {csv_url.split('/')[-1]} ---")
        
        try:
            df = fetcher.download_csv(csv_url)
            if df is not None:
                analysis = {
                    'filename': csv_url.split('/')[-1],
                    'rows': len(df),
                    'columns': list(df.columns),
                    'column_count': len(df.columns)
                }
                
                print(f"Rows: {len(df)}")
                print(f"Columns ({len(df.columns)}): {list(df.columns)}")
                
                # Look for timestamp columns
                timestamp_cols = [col for col in df.columns if any(keyword in col.lower() 
                                for keyword in ['time', 'date', 'timestamp'])]
                if timestamp_cols:
                    print(f"Timestamp columns: {timestamp_cols}")
                    # Show sample timestamp values
                    for col in timestamp_cols[:1]:  # Just first timestamp column
                        print(f"Sample {col} values: {df[col].head(3).tolist()}")
                
                # Look for Target columns
                target_cols = [col for col in df.columns if 'target' in col.lower()]
                if target_cols:
                    print(f"Target columns: {target_cols}")
                
                # Look for ping/latency columns
                ping_cols = [col for col in df.columns if any(keyword in col.lower() 
                           for keyword in ['ping', 'latency', 'rtt', 'response'])]
                if ping_cols:
                    print(f"Ping/Latency columns: {ping_cols}")
                
                # Look for packet loss columns
                loss_cols = [col for col in df.columns if any(keyword in col.lower() 
                           for keyword in ['loss', 'packet', 'dropped'])]
                if loss_cols:
                    print(f"Packet Loss columns: {loss_cols}")
                
                # Show first few rows
                print(f"First 2 rows:")
                print(df.head(2).to_string())
                
                file_analysis.append(analysis)
                all_columns.update(df.columns)
                
        except Exception as e:
            print(f"Error examining {csv_url}: {e}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"Total unique columns across all files: {len(all_columns)}")
    print("All columns found:", sorted(all_columns))
    
    # Group by column count
    by_column_count = {}
    for analysis in file_analysis:
        count = analysis['column_count']
        if count not in by_column_count:
            by_column_count[count] = []
        by_column_count[count].append(analysis['filename'])
    
    print(f"\nFiles grouped by column count:")
    for count, files in sorted(by_column_count.items()):
        print(f"  {count} columns: {files}")
    
    # Find common patterns
    target_patterns = set()
    for analysis in file_analysis:
        targets = [col for col in analysis['columns'] if 'target' in col.lower()]
        if targets:
            target_patterns.add(tuple(sorted(targets)))
    
    if target_patterns:
        print(f"\nTarget column patterns found:")
        for i, pattern in enumerate(sorted(target_patterns), 1):
            print(f"  Pattern {i}: {list(pattern)}")

if __name__ == "__main__":
    examine_csv_structure()