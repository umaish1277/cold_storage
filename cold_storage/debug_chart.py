import frappe
import json

def debug_chart():
    chart_name = "Incoming Bags"
    if not frappe.db.exists("Dashboard Chart", chart_name):
        print(f"Chart {chart_name} not found")
        return
    
    chart = frappe.get_doc("Dashboard Chart", chart_name)
    print(f"Document Type: {chart.document_type}")
    print(f"Chart Type: {chart.chart_type}")
    print(f"Type: {chart.type}")
    print(f"Filters JSON: {chart.filters_json}")
    
    filters = frappe.parse_json(chart.filters_json)
    print(f"Parsed Filters (Type: {type(filters)}): {filters}")
    
    if filters is None:
        filters = []
    
    print(f"Filters after None check: {filters}")
    print(f"Filters hasattr append: {hasattr(filters, 'append')}")
    if hasattr(filters, 'append'):
        print(f"Filters append value: {filters.append}")
    
    try:
        filters.append([chart.document_type, "docstatus", "<", 2])
        print("Success: filters.append worked")
    except Exception as e:
        print(f"FAILED: filters.append failed with: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    debug_chart()
