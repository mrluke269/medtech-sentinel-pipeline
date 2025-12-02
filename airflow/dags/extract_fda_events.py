import time
import requests
import json
from pathlib import Path

def extract_fda_events(product_code, start_date, end_date):
    """
    Extract FDA events for a given product code and date range.
    
    Args:
        product_code (str): The FDA product code.
        start_date (str): The start date in 'YYYYMMDD'
        end_date (str): The end date in 'YYYYMMDD'
    """
    # Implementation goes here
    base_url = 'https://api.fda.gov/device/event.json'
    skip = 0
    limit = 1000
    results_combined = []
    params = {
        'search': f'device.device_report_product_code:"{product_code}" AND date_received:[{start_date} TO {end_date}]',
        'limit': limit,
        'skip': skip
    }

    # Initial request
    print(f"Request URL: {base_url}")
    print(f"Params: {params}")

    response = requests.get(base_url, params=params)

    if response.status_code == 404:
        print("No data found for the given query parameters.")
        return results_combined

    if response.status_code != 200:
        try:
            error_info = response.json()
            print("Error JSON from openFDA:", json.dumps(error_info, indent=2))
        except Exception:
            print("Error response (not JSON):", response.text)

        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()

    # Get meta info
    meta = data.get('meta', {})
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)

    # Current batch of results
    batch = data.get('results', [])
    results_combined.extend(batch)
    print(f"Total records to extract: {total_records}")
    print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")

    # Update skip for pagination
    skip += len(batch)

    # ---- Pagination loop ----
    while skip < total_records: # Continue until all records are fetched
        params['skip'] = skip
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")

        data = response.json()
        batch = data.get('results', [])
        if not batch:
            print("No more results returned by API, stopping early.")
            break
        results_combined.extend(batch) # Append new batch to combined results
        print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")

        skip += len(batch)
        time.sleep(0.1)  # be polite to the API

    return results_combined

def save_events_to_json(events, product_code, start_date, end_date):
    """
    Save extracted FDA events to a JSON file.
    
    Args:
        events (list): List of FDA event records.
        product_code (str): FDA product code used in the query.
        start_date (str): Start date in 'YYYYMMDD'.
        end_date (str): End date in 'YYYYMMDD'.
    """
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    OUTPUT_DIR = PROJECT_ROOT / 'data' / 'fda_events'
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f'{product_code}_{start_date}_{end_date}.json'

    with open(output_path, 'w') as f:
        json.dump(events, f, indent=2)

    print(f"Saved {len(events)} events to {output_path}")

if __name__ == "__main__":
    product_code = "DYE"
    start_date = "20251001"
    end_date = "20251101"
    data = extract_fda_events(product_code, start_date, end_date)
    save_events_to_json(data, product_code, start_date, end_date)