#!/usr/bin/env python3
"""
Script to collect WAI history data from the API and save it as JSON and CSV.
Used by GitHub Actions to periodically collect data.
"""
import json
import csv
import os
import sys
from datetime import datetime
import httpx


def fetch_wai_history(api_url: str) -> list:
    """Fetch the complete WAI history from the API."""
    try:
        response = httpx.get(f"{api_url}/api/wai/history", timeout=60.0)
        response.raise_for_status()
        result = response.json()
        print(response.json())
        
        # Handle different response structures
        if isinstance(result, dict) and 'data' in result:
            return result['data']
        elif isinstance(result, list):
            return result
        else:
            print(f"Unexpected response format: {type(result)}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)


def save_json(data: list, filepath: str):
    """Save data as JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON to {filepath} ({len(data)} records)")


def save_csv(data: list, filepath: str):
    """Save data as CSV file."""
    if not data:
        print("No data to save")
        return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Get all possible fields from the data
    fieldnames = set()
    for record in data:
        if not isinstance(record, dict):
            print(f"Warning: Skipping non-dict record: {type(record)}", file=sys.stderr)
            continue
        fieldnames.update(record.keys())
        # Flatten metadata if present
        if 'metadata' in record and isinstance(record['metadata'], dict):
            for key in record['metadata'].keys():
                fieldnames.add(f'metadata_{key}')
    
    if not fieldnames:
        print("No valid records to save", file=sys.stderr)
        return
    
    fieldnames = sorted(fieldnames)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            if not isinstance(record, dict):
                continue
            flat_record = dict(record)
            # Flatten metadata
            if 'metadata' in flat_record and isinstance(flat_record['metadata'], dict):
                for key, value in flat_record['metadata'].items():
                    flat_record[f'metadata_{key}'] = value
                del flat_record['metadata']
            
            writer.writerow(flat_record)
    
    print(f"✓ Saved CSV to {filepath} ({len(data)} records)")


def main():
    # Get API URL from environment or use default
    api_url = os.getenv('WAI_API_URL', 'http://80.158.78.0:8000')
    
    print(f"Fetching WAI history from {api_url}...")
    data = fetch_wai_history(api_url)
    
    # Add collection metadata
    collection_info = {
        'collected_at': datetime.utcnow().isoformat() + 'Z',
        'record_count': len(data)
    }
    
    # Save as JSON with metadata
    json_data = {
        'metadata': collection_info,
        'data': data
    }
    json_path = 'data/wai_history.json'
    save_json(json_data, json_path)
    
    # Save as CSV (just the data records)
    csv_path = 'data/wai_history.csv'
    save_csv(data, csv_path)
    
    print(f"\n✓ Data collection completed successfully! ({len(data)} records)")


if __name__ == '__main__':
    main()
