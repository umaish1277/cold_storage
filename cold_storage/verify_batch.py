import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def verify_batch_filter():
    print("Testing batch_no filter...")
    # Just try a dummy batch number, we mainly want to see if SQL errors out
    filters = {"batch_no": "TEST-123"} 
    
    try:
        columns, data = execute(filters)
        print(f"Success: Query executed without error. Rows: {len(data)}")
    except Exception as e:
        print(f"Error: {e}")

