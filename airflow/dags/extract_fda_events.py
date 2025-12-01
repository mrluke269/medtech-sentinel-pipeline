import requests
import json

def extract_fda_events(product_code, start_date, end_date):
    """
    Extract FDA events for a given product code and date range.
    
    Args:
        product_code (str): The FDA product code.
        start_date (str): The start date in 'YYYY-MM-DD'
        end_date (str): The end date in 'YYYY-MM-DD'
    """
    # Implementation goes here
    response = requests.get(f'https://api.fda.gov/device/event.json?search=product_code:{product_code}+AND+date_received:[{start_date}+TO+{end_date}]&limit=100')
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
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