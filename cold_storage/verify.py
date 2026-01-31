import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def verify_filters():
    #Get a warehouse and bag type
    warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
    bag_type = frappe.db.get_value("Item", {"item_group": "Bag Type"}, "name")
    
    # Debug: Check values
    print(f"DEBUG: Found Warehouse: {warehouse}")
    print(f"DEBUG: Found Bag Type: {bag_type}")

    if not warehouse:
        print("No Warehouse found to test")
        # return - don't return, try testing without warehouse if null to see base case

    print(f"Testing with Warehouse: {warehouse}")
    filters = {"warehouse": warehouse}
    try:
        columns, data = execute(filters)
        print(f"Rows returned with Warehouse filter: {len(data)}")
    except Exception as e:
        print(f"Error executing with Warehouse filter: {e}")
    
    if bag_type:
        print(f"Testing with Bag Type: {bag_type}")
        filters = {"bag_type": bag_type}
        try:
            columns, data = execute(filters)
            print(f"Rows returned with Bag Type filter: {len(data)}")
        except Exception as e:
             print(f"Error executing with Bag Type filter: {e}")
    else:
        print("No Bag Type item found to test")
