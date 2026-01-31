import frappe
from cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger import execute

def verify_cumulative_balance():
    print("Testing Cumulative Balance Column...")
    
    filters = {}
    columns, data = execute(filters)
    
    if not data:
        print("No data to verify.")
        return
        
    running_total = 0
    mismatch = False
    
    # Iterate all rows except the last "Total" row
    for i, row in enumerate(data[:-1]):
        balance = row.get('balance')
        cumulative = row.get('cumulative_balance')
        
        running_total += balance
        
        if cumulative != running_total:
            print(f"Mismatch at Row {i}: Balance={balance}, Expected Cumulative={running_total}, Got={cumulative}")
            mismatch = True
            break
            
    if not mismatch:
        print("Success: Cumulative balance calculates correctly for all rows.")
        
    last_row = data[-1]
    # Verify Total row also has it
    if last_row.get('cumulative_balance') == "": 
         print(f"Success: Total Row Cumulative is empty as requested.")
    else:
        print(f"Warning: Total Row Cumulative is NOT empty: {last_row.get('cumulative_balance')}")

