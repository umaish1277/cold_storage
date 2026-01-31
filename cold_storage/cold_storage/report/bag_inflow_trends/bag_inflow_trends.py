import frappe
from frappe import _

def execute(filters=None):
    if not filters: filters = {}
    
    # Columns: Date, Jute Bags, Net Bags
    # We will dynamically find bag types if we want, but user asked specifically for Jute and Net.
    # To be generic, we can pivot whatever bag types exist.
    
    # 1. Fetch all distinct bag types utilized in the filtered period
    # We need this to define the columns and initialize the pivot
    
    # Base conditions
    conditions = ""
    if filters.get("from_date"):
        conditions += f" AND p.receipt_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" AND p.receipt_date <= '{filters.get('to_date')}'"

    # Get Distinct Types
    distinct_types = frappe.db.sql(f"""
        SELECT DISTINCT c.bag_type
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions}
    """, as_dict=True)
    
    bag_types = sorted([d.bag_type for d in distinct_types if d.bag_type])
    
    # Always include 'Unspecified' if there are nulls, or if we want to show it.
    # Let's check if there are nulls.
    check_nulls = frappe.db.sql(f"""
        SELECT 1 FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 AND (c.bag_type IS NULL OR c.bag_type = '') {conditions}
        LIMIT 1
    """)
    if check_nulls:
        bag_types.append("Unspecified")

    # Define Columns
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
    ]
    for bt in bag_types:
        columns.append({
            "label": _(bt), 
            "fieldname": frappe.scrub(bt), 
            "fieldtype": "Int", 
            "width": 100
        })

    # 2. Aggregate Data
    raw_data = frappe.db.sql(f"""
        SELECT p.receipt_date, c.bag_type, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions}
        GROUP BY p.receipt_date, c.bag_type
        ORDER BY p.receipt_date ASC
    """, as_dict=True)
    
    # Pivot
    from collections import defaultdict
    pivot = defaultdict(lambda: {bt: 0 for bt in bag_types})
    
    for row in raw_data:
        bt_key = row.bag_type 
        if not bt_key:
             bt_key = "Unspecified"
        
        if bt_key in bag_types:
            pivot[str(row.receipt_date)][bt_key] += float(row.qty or 0)
            
    data = []
    labels = sorted(pivot.keys())
    
    # Sort data by date
    for date_str in labels:
        row = {"date": date_str}
        for bt in bag_types:
            row[frappe.scrub(bt)] = pivot[date_str][bt]
        data.append(row)

    # Chart Structure
    datasets = []
    import random
    
    # Pre-defined nice colors
    colors = ["#449CF0", "#ECAD4B", "#28a745", "#dc3545", "#ffc107", "#17a2b8"]
    chart_colors = []
    
    for i, bt in enumerate(bag_types):
        datasets.append({
            "name": bt,
            "values": [pivot[d][bt] for d in labels]
        })
        # Assign color cyclically or mapped
        if bt == "Unspecified":
            chart_colors.append("#808080")
        else:
            chart_colors.append(colors[i % len(colors)])

    chart = {
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "type": "bar",
        "colors": chart_colors
    }
        
    return columns, data, None, chart




