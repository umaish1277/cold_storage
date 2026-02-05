import frappe
from frappe import _

def execute(filters=None):
    if not filters: filters = {}
    
    # Base conditions
    conditions = ""
    if filters.get("from_date"):
        conditions += f" AND p.dispatch_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" AND p.dispatch_date <= '{filters.get('to_date')}'"

    # Get Distinct Types from Dispatches
    distinct_types = frappe.db.sql(f"""
        SELECT DISTINCT c.item_group
        FROM `tabCold Storage Dispatch` p
        JOIN `tabCold Storage Dispatch Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 AND (p.remarks IS NULL OR p.remarks NOT LIKE 'Auto-generated Transfer%') {conditions}
    """, as_dict=True)
    
    item_groups = sorted([d.get("item_group") for d in distinct_types if d.get("item_group")])
    
    check_nulls = frappe.db.sql(f"""
        SELECT 1 FROM `tabCold Storage Dispatch` p
        JOIN `tabCold Storage Dispatch Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 AND (c.item_group IS NULL OR c.item_group = '') {conditions}
        LIMIT 1
    """)
    if check_nulls:
        item_groups.append("Unspecified")

    # Define Columns
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
    ]
    for bt in item_groups:
        columns.append({
            "label": _(bt), 
            "fieldname": frappe.scrub(bt), 
            "fieldtype": "Int", 
            "width": 100
        })

    # 2. Aggregate Data
    raw_data = frappe.db.sql(f"""
        SELECT p.dispatch_date, c.item_group, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Dispatch` p
        JOIN `tabCold Storage Dispatch Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 AND (p.remarks IS NULL OR p.remarks NOT LIKE 'Auto-generated Transfer%') {conditions}
        GROUP BY p.dispatch_date, c.item_group
        ORDER BY p.dispatch_date ASC
    """, as_dict=True)
    
    # Pivot
    from collections import defaultdict
    pivot = defaultdict(lambda: {bt: 0 for bt in item_groups})
    
    for row in raw_data:
        bt_key = row.get("item_group")
        if not bt_key:
             bt_key = "Unspecified"
        
        if bt_key in item_groups:
            pivot[str(row.get("dispatch_date"))][bt_key] += float(row.get("qty") or 0)
            
    data = []
    labels = sorted(pivot.keys())
    
    # Sort data by date
    for date_str in labels:
        row = {"date": date_str}
        for bt in item_groups:
            row[frappe.scrub(bt)] = pivot[date_str][bt]
        data.append(row)

    # Chart Structure
    datasets = []
    import random
    
    # Pre-defined nice colors
    colors = ["#449CF0", "#ECAD4B", "#28a745", "#dc3545", "#ffc107", "#17a2b8"]
    chart_colors = []
    
    for i, bt in enumerate(item_groups):
        datasets.append({
            "name": bt,
            "values": [pivot[d][bt] for d in labels]
        })
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
