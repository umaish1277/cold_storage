import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import get_bag_type_filter

def verify_query():
    # Test the query method
    results = get_bag_type_filter("Item", "", "name", 0, 10, {})
    print(f"Bag Types found via API: {results}")
    
    expected = ['Jute Bag', 'Net Bag', 'Plastic Bag'] # Based on previous debug
    
    # Check if results match expectations (at least contain them)
    found_bags = [r[0] for r in results]
    for bag in expected:
        if bag in found_bags:
            print(f"Confirmed: {bag} is present in filter options.")
        else:
            print(f"Warning: {bag} missing from filter options (might not be in DB anymore?)")
            
    if not results:
        print("Error: No bag types returned by filter query.")
