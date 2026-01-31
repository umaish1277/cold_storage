import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def verify_total_row():
    print("Testing Total Row...")
    
    # Run with default filters (or empty) to get some data
    filters = {}
    columns, data = execute(filters)
    
    if not data:
        print("No data returned, cannot verify total row.")
        return

    last_row = data[-1]
    
    # Check if last row is indeed the total row
    # We used frappe.bold("Total") for customer, but raw string check might vary if bold adds HTML
    # It adds <b>Total</b>.
    print(f"Last Row Batch No Field: {last_row.get('batch_no')}")
    
    if "Total" in str(last_row.get('batch_no')):
        print("Confirmed: Last row is a Total row.")
        print(f"Total In Qty: {last_row.get('in_qty')}")
        print(f"Total Out Qty: {last_row.get('out_qty')}")
        print(f"Total Balance: {last_row.get('balance')}")
        print(f"Total Days In Store: '{last_row.get('days_in_store')}'")
        
        if last_row.get('days_in_store') == "":
            print("Success: Total Days In Store is empty.")
        else:
            print(f"Warning: Total Days In Store is NOT empty: {last_row.get('days_in_store')}")

        # Verify sum conceptually (first few rows)
        if len(data) > 1:
             # Sum of previous rows
            calc_in = sum(d['in_qty'] for d in data[:-1])
            print(f"Calculated Sum of In Qty (manual): {calc_in}")
            
            if last_row.get('in_qty') == calc_in:
                print("Success: Total In Qty matches calculated sum.")
            else:
                print(f"Warning: Total In Qty {last_row.get('in_qty')} != Calculated {calc_in}")
             # Note: Last row values are also bolded strings now, so equality check needs parsing or visual confirmation
    else:
        print("Error: Last row does not appear to be the Total row.")
