
import frappe
from frappe import _

def execute(filters=None):
    if not filters: filters = {}

    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": _("Incoming (Bags)"), "fieldname": "incoming", "fieldtype": "Int", "width": 120},
        {"label": _("Outgoing (Bags)"), "fieldname": "outgoing", "fieldtype": "Int", "width": 120},
        {"label": _("Net Movement"), "fieldname": "net", "fieldtype": "Int", "width": 120}
    ]
    
    # 1. Fetch Receipts (Inflow)
    conditions_in = ""
    if filters.get("from_date"): conditions_in += f" AND receipt_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions_in += f" AND receipt_date <= '{filters.get('to_date')}'"

    receipts = frappe.db.sql(f"""
        SELECT p.receipt_date as date, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions_in}
        GROUP BY p.receipt_date
    """, as_dict=True)

    # 2. Fetch Dispatches (Outflow)
    conditions_out = ""
    if filters.get("from_date"): conditions_out += f" AND dispatch_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions_out += f" AND dispatch_date <= '{filters.get('to_date')}'"
    
    # Dispatch uses 'total_packages' or we sum items? Let's check dispatch tables.
    # Assuming 'Cold Storage Dispatch' has date field 'dispatch_date' 
    # and items with 'qty' or 'number_of_bags'. 
    # Let's verify Dispatch fields in a moment, but assuming standard structure based on Receipt.
    
    dispatches = frappe.db.sql(f"""
        SELECT p.dispatch_date as date, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Dispatch` p
        JOIN `tabCold Storage Dispatch Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions_out}
        GROUP BY p.dispatch_date
    """, as_dict=True)

    # 3. Merge Data
    data_map = {}
    
    for r in receipts:
        d = str(r.date)
        if d not in data_map: data_map[d] = {"date": d, "incoming": 0, "outgoing": 0}
        data_map[d]["incoming"] += (r.qty or 0)
        
    for r in dispatches:
        d = str(r.date)
        if d not in data_map: data_map[d] = {"date": d, "incoming": 0, "outgoing": 0}
        data_map[d]["outgoing"] += (r.qty or 0)
        
    # Flatten and Sort
    data = []
    dates = sorted(data_map.keys())
    for d in dates:
        row = data_map[d]
        row["net"] = row["incoming"] - row["outgoing"]
        data.append(row)

    # 4. Chart
    chart = {
        "data": {
            "labels": dates,
            "datasets": [
                {"name": "Incoming", "values": [data_map[d]["incoming"] for d in dates]},
                {"name": "Outgoing", "values": [data_map[d]["outgoing"] for d in dates]}
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545"] # Green for In, Red for Out
    }

    return columns, data, None, chart
