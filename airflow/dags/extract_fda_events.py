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
    results_combined = []
    response = requests.get(f'https://api.fda.gov/device/event.json?search=device.device_report_product_code:"{product_code}"+AND+date_received:[{start_date}+TO+{end_date}]&limit=1000')

    if response.status_code == 200:
        data = response.json()

        meta = data.get('meta', {}) # Get meta from data
        meta_info = meta.get('results', {}) # Get results info from meta
        limit = meta_info.get('limit') # get limit infro from meta
        
        results = data.get('results', []) # Get results from data
        results_received = len(results) 

        while  results_received <= limit:
            results_combined.extend(results)
            response = requests.get(f'https://api.fda.gov/device/event.json?search=device.device_report_product_code:"{product_code}"+AND+date_received:[{start_date}+TO+{end_date}]&limit=1000&skip=1{results_received}')
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                results_received += len(results)

    return results_combined


    pass



"""
Function 1: extract_fda_events(product_code, start_date, end_date)

Builds API URL
While loop: keep requesting until results_received < limit
Append each page's events to a combined list
Return the combined list

Function 2: save_to_json(data, filepath)

Takes the list from function 1
Saves it to a JSON file"""