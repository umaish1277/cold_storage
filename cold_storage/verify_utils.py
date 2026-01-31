import frappe
from cold_storage.cold_storage.utils import get_bag_type_filter

def verify_query():
    print("Testing import from utils...")
    results = get_bag_type_filter("Item", "", "name", 0, 10, {})
    print(f"Bag Types found via Utils: {results}")
    
    if not results:
        print("Error: No bag types returned by filter query.")
    else:
        print("Success: Method is accessible and returns data.")

