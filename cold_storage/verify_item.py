import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def verify_item_filter():
    print("Testing item_code filter...")
    
    # Get a receipt item to test with
    item = frappe.db.sql("SELECT goods_item FROM `tabCold Storage Receipt Item` WHERE docstatus=1 LIMIT 1", as_dict=True)
    
    if not item:
        print("No receipt items found to test.")
        return

    test_item = item[0].goods_item
    print(f"Testing with Item: {test_item}")
    
    filters = {"item_code": test_item}
    columns, data = execute(filters)
    
    print(f"Rows returned: {len(data)}")
    
    mismatch = False
    for row in data:
        if row.get('item') != test_item:
            print(f"MISMATCH: Row has item '{row.get('item')}' but filter was '{test_item}'")
            mismatch = True
            
    if not mismatch and data:
        print("Success: All rows match the Item filter.")
    elif not data:
        print("Warning: No data returned (might be expected for this item if no open receipts, but query didn't error).")

