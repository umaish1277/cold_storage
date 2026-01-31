import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def debug_bag_filter():
    # Find distinct bag types actually used in Receipts
    bag_types = frappe.db.sql("""
        SELECT DISTINCT bag_type FROM `tabCold Storage Receipt Item` WHERE docstatus=1
    """, as_dict=True)
    
    print(f"DEBUG: Found used Bag Types: {[b.bag_type for b in bag_types]}")
    
    if not bag_types:
        print("No Bag Types found in existing Receipts.")
        return

    test_bag = "Jute Bag"
    
    # Get a warehouse used in receipts
    wh_data = frappe.db.sql("SELECT DISTINCT warehouse FROM `tabCold Storage Receipt` WHERE docstatus=1", as_dict=True)
    test_wh = wh_data[0].warehouse if wh_data else None

    print(f"Testing with Bag Type: '{test_bag}' (No Warehouse filter)")
    filters = {"bag_type": test_bag}
    
    if not test_bag:
         print("No non-empty bag type found")
         return

    # Execute report
    columns, data = execute(filters)
    print(f"Rows returned: {len(data)}")
    
    # Verify if rows actually match
    mismatch = False
    for row in data:
        if row.get('bag_type') != test_bag:
            print(f"MISMATCH found! Row has bag_type: '{row.get('bag_type')}' vs Filter: '{test_bag}'")
            mismatch = True
    
    if not mismatch and len(data) > 0:
        print("All rows match the filter.")
    elif len(data) == 0:
        print("No data returned for filter.")
    
    if not test_bag:
         print("No non-empty bag type found")
         return

    print(f"Testing with Bag Type: '{test_bag}'")
    filters = {"bag_type": test_bag}
    
    # Execute report
    columns, data = execute(filters)
    print(f"Rows returned: {len(data)}")
    
    # Verify if rows actually match
    mismatch = False
    for row in data:
        if row.get('bag_type') != test_bag:
            print(f"MISMATCH found! Row has bag_type: {row.get('bag_type')}")
            mismatch = True
            break
    
    if not mismatch and len(data) > 0:
        print("All rows match the filter.")
