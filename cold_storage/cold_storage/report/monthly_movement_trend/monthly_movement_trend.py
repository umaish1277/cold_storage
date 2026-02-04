
import frappe
from frappe import _

def execute(filters=None):
    if not filters: filters = {}

    columns = [
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 120},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": _("Incoming (Bags)"), "fieldname": "incoming", "fieldtype": "Int", "width": 120},
        {"label": _("Outgoing (Bags)"), "fieldname": "outgoing", "fieldtype": "Int", "width": 120},
        {"label": _("Net Movement"), "fieldname": "net", "fieldtype": "Int", "width": 120}
    ]
    
    # 1. Fetch Receipts (Inflow)
    conditions_in = ""
    if filters.get("from_date"): conditions_in += f" AND p.receipt_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions_in += f" AND p.receipt_date <= '{filters.get('to_date')}'"

    receipts = frappe.db.sql(f"""
        SELECT DATE_FORMAT(p.receipt_date, '%Y-%m') as month, c.item_group, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions_in}
        GROUP BY month, c.item_group
    """, as_dict=True)

    # 2. Fetch Dispatches (Outflow)
    conditions_out = ""
    if filters.get("from_date"): conditions_out += f" AND p.dispatch_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions_out += f" AND p.dispatch_date <= '{filters.get('to_date')}'"
    
    dispatches = frappe.db.sql(f"""
        SELECT DATE_FORMAT(p.dispatch_date, '%Y-%m') as month, c.item_group, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Dispatch` p
        JOIN `tabCold Storage Dispatch Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions_out}
        GROUP BY month, c.item_group
    """, as_dict=True)

    # 3. Merge Data
    data_map = {}
    all_item_groups = set()
    all_months = set()
    
    for r in receipts:
        k = (r.month, r.item_group)
        if k not in data_map: data_map[k] = {"month": r.month, "item_group": r.item_group, "incoming": 0, "outgoing": 0}
        data_map[k]["incoming"] += (r.qty or 0)
        all_item_groups.add(r.item_group)
        all_months.add(r.month)
        
    for r in dispatches:
        k = (r.month, r.item_group)
        if k not in data_map: data_map[k] = {"month": r.month, "item_group": r.item_group, "incoming": 0, "outgoing": 0}
        data_map[k]["outgoing"] += (r.qty or 0)
        all_item_groups.add(r.item_group)
        all_months.add(r.month)
        
    # Flatten and Sort
    data = []
    sorted_keys = sorted(data_map.keys())
    for k in sorted_keys:
        row = data_map[k]
        row["net"] = row["incoming"] - row["outgoing"]
        data.append(row)

    # 4. Chart Generation
    labels = sorted(list(all_months))
    datasets = []
    
    # Sort item groups for consistent order
    sorted_item_groups = sorted(list(all_item_groups))
    
    for ig in sorted_item_groups:
        incoming_vals = []
        outgoing_vals = []
        for m in labels:
            val = data_map.get((m, ig), {})
            incoming_vals.append(val.get("incoming", 0))
            outgoing_vals.append(val.get("outgoing", 0))
            
        datasets.append({"name": f"Incoming ({ig})", "values": incoming_vals})
        datasets.append({"name": f"Outgoing ({ig})", "values": outgoing_vals})

    chart = {
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "type": "bar",
        "colors": ["#2ecc71", "#27ae60", "#e74c3c", "#c0392b"] # Greens and Reds
    }

    return columns, data, None, chart
