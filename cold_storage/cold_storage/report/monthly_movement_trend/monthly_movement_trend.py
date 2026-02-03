
import frappe
from frappe import _

def execute(filters=None):
    if not filters: filters = {}

    columns = [
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 120},
        {"label": _("Incoming (Bags)"), "fieldname": "incoming", "fieldtype": "Int", "width": 120},
        {"label": _("Outgoing (Bags)"), "fieldname": "outgoing", "fieldtype": "Int", "width": 120},
        {"label": _("Net Movement"), "fieldname": "net", "fieldtype": "Int", "width": 120}
    ]
    
    # 1. Fetch Receipts (Inflow)
    conditions_in = ""
    if filters.get("from_date"): conditions_in += f" AND receipt_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions_in += f" AND receipt_date <= '{filters.get('to_date')}'"

    receipts = frappe.db.sql(f"""
        SELECT DATE_FORMAT(p.receipt_date, '%Y-%m') as month, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions_in}
        GROUP BY month
        ORDER BY month
    """, as_dict=True)

    # 2. Fetch Dispatches (Outflow)
    conditions_out = ""
    if filters.get("from_date"): conditions_out += f" AND dispatch_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions_out += f" AND dispatch_date <= '{filters.get('to_date')}'"
    
    dispatches = frappe.db.sql(f"""
        SELECT DATE_FORMAT(p.dispatch_date, '%Y-%m') as month, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Dispatch` p
        JOIN `tabCold Storage Dispatch Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions_out}
        GROUP BY month
        ORDER BY month
    """, as_dict=True)

    # 3. Merge Data
    data_map = {}
    
    for r in receipts:
        m = r.month
        if m not in data_map: data_map[m] = {"month": m, "incoming": 0, "outgoing": 0}
        data_map[m]["incoming"] += (r.qty or 0)
        
    for r in dispatches:
        m = r.month
        if m not in data_map: data_map[m] = {"month": m, "incoming": 0, "outgoing": 0}
        data_map[m]["outgoing"] += (r.qty or 0)
        
    # Flatten and Sort
    data = []
    months = sorted(data_map.keys())
    for m in months:
        row = data_map[m]
        row["net"] = row["incoming"] - row["outgoing"]
        data.append(row)

    # 4. Chart
    chart = {
        "data": {
            "labels": months,
            "datasets": [
                {"name": "Incoming", "values": [data_map[m]["incoming"] for m in months]},
                {"name": "Outgoing", "values": [data_map[m]["outgoing"] for m in months]}
            ]
        },
        "type": "bar",
        "colors": ["#2ecc71", "#e74c3c"] # Emerald Green, Alizarin Red
    }

    return columns, data, None, chart
