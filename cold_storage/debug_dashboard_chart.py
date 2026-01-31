import frappe
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get

def debug():
    print("Debugging Dashboard Chart API...")
    
    # 1. Test Incoming Bags (Working)
    print("\n--- Testing INCOMING BAGS (Reference) ---")
    try:
        chart_inc = frappe.get_doc("Dashboard Chart", "Incoming Bags")
        data_inc = get(chart_name="Incoming Bags", filters={})
        print(f"Incoming Data Keys: {data_inc.keys()}")
        if 'labels' in data_inc:
             print(f"Labels: {len(data_inc['labels'])}")
    except Exception as e:
        print(f"Incoming Failed: {e}")

    # 2. Test Outgoing Bags (Broken)
    print("\n--- Testing OUTGOING BAGS (Target) ---")
    try:
        # Check if doc exists
        if not frappe.db.exists("Dashboard Chart", "Outgoing Bags"):
             print("CRITICAL: Dashboard Chart 'Outgoing Bags' not found in DB!")
             return

        chart_out = frappe.get_doc("Dashboard Chart", "Outgoing Bags")
        print(f"Chart Found: {chart_out.name}, Report: {chart_out.report_name}")
        
        # Simulate Dashboard Call
        # defaults usually: filters={}, time_interval='Daily', timespan='Last Year'
        data_out = get(chart_name="Outgoing Bags", filters={}, time_interval="Daily", timespan="Last Year")
        
        print(f"Outgoing Data Keys: {data_out.keys()}")
        if 'labels' in data_out:
             print(f"Labels: {len(data_out['labels'])}")
             print(f"Values: {data_out}")
        else:
             print("No labels returned!")
             
    except Exception as e:
        print(f"Outgoing Failed: {e}")
        import traceback
        traceback.print_exc()
