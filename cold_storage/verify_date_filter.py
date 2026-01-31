import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def verify_date_filter():
    print("Testing Date Range Filter...")
    
    # 1. Fetch data without date filters to see range
    print("\n--- All Data ---")
    columns, all_data = execute({})
    if not all_data:
        print("No data found at all.")
        return
        
    dates = [d['receipt_date'] for d in all_data if d.get('receipt_date')]
    if not dates:
        print("No dates found in data")
        return
        
    min_date = min(dates)
    max_date = max(dates)
    print(f"Date Range in DB: {min_date} to {max_date}")
    
    # 2. Apply a filter that should exclude some data
    # Let's pick a range that covers the min_date but not the max_date (if they differ)
    # Or just picking the min_date itself
    
    test_from = min_date
    test_to = min_date 
    
    print(f"\n--- Filtering for {test_from} to {test_to} ---")
    
    filters = {
        "from_date": test_from,
        "to_date": test_to
    }
    
    col, filtered_data = execute(filters)
    
    fail = False
    count = 0
    for row in filtered_data:
        # Skip Total row which has empty receipt_date
        if not row.get('receipt_date'):
            continue
            
        count += 1
        if row['receipt_date'] < test_from or row['receipt_date'] > test_to:
            print(f"FAIL: Row has date {row['receipt_date']} which is outside {test_from}-{test_to}")
            fail = True
            
    if not fail:
        print(f"Success: All {count} rows are within range.")
    else:
        print("failed")

