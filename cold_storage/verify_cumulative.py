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
    if last_row.get('cumulative_balance') == last_row.get('balance'): # In total row, cumulative should equal total balance
         print(f"Total Row Cumulative matches Total Balance: {last_row.get('cumulative_balance')}")
    else:
        # Note: They are bolded strings, so strict equality might fail if not checked carefully, but here we expect them to be generated same way
        # frappe.bold(cumulative_balance) vs frappe.bold(total_balance). cumulative_balance == total_balance at end.
        print(f"Warning: Total Row Cumulative {last_row.get('cumulative_balance')} != Total Balance {last_row.get('balance')}")

