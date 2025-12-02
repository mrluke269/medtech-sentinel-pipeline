import time
import requests
import json

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
        'search': f'device.device_report_product_code:"{product_code}"+AND+date_received:[{start_date}+TO+{end_date}]',
        'limit': limit,
        'skip': skip
    }

    # Initial request
    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()

    # Get meta info
    meta = data.get('meta', {})
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)

    # Current batch of results
    batch = data.get('results', [])
    results_combined.extend(batch)
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