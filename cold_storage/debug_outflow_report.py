import frappe
from cold_storage.cold_storage.report.bag_outflow_trends.bag_outflow_trends import execute

def debug():
    print("Debugging Bag Outflow Trends Report...")
    
    # Check if there are any submitted dispatches
    dispatches = frappe.get_all("Cold Storage Dispatch", filters={"docstatus": 1}, fields=["name", "dispatch_date"])
    print(f"Submitted Dispatches: {len(dispatches)}")
    for d in dispatches:
        print(f" - {d.name} ({d.dispatch_date})")
        
    if not dispatches:
        print("No submitted dispatches found. Chart will be empty.")
        return

    # Execute Report with empty filters (should show all if logic handles it)
    print("\nExecuting Report with empty filters (simulating dashboard initial load potentially)...")
    try:
        columns, data, message, chart = execute({})
        print(f"Data Rows: {len(data)}")
        if data:
            print("Sample Data:", data[0])
        
        print("\nChart Data:")
        if chart:
             print(f"Chart Type: {chart.get('type')}")
             print(f"Datasets: {len(chart.get('data', {}).get('datasets', []))}")
             labels = chart.get('data', {}).get('labels', [])
             print(f"Labels ({len(labels)}): {labels}")
             for ds in chart.get('data', {}).get('datasets', []):
                 print(f" - Dataset '{ds.get('name')}': {ds.get('values')}")
        else:
             print("Chart object is None or Empty!")
             
    except Exception as e:
        print(f"Execution Failed: {e}")
        import traceback
        traceback.print_exc()

