
import frappe
from frappe import _
from frappe.utils import date_diff

def execute(filters=None):
    if not filters: filters = {}

    columns = [
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Avg Storage Days"), "fieldname": "avg_days", "fieldtype": "Float", "width": 150},
        {"label": _("Max Storage Days"), "fieldname": "max_days", "fieldtype": "Int", "width": 150},
        {"label": _("Total Dispatched Bags"), "fieldname": "total_bags", "fieldtype": "Int", "width": 150}
    ]

    # Conditions
    conditions = "WHERE d.docstatus = 1 AND d.linked_receipt IS NOT NULL"
    if filters.get("from_date"): conditions += f" AND d.dispatch_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"): conditions += f" AND d.dispatch_date <= '{filters.get('to_date')}'"

    # Query to get durations
    # We join dispatch items with receipt items to be precise, or just use parent dates
    # Let's use parent dates for simplicity as long as dispatch is linked to receipt
    raw_data = frappe.db.sql(f"""
        SELECT 
            di.goods_item as item,
            DATEDIFF(d.dispatch_date, r.receipt_date) as duration,
            di.number_of_bags as bags
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
        JOIN `tabCold Storage Receipt` r ON r.name = d.linked_receipt
        {conditions}
    """, as_dict=True)

    # Aggregate by Item
    item_stats = {}
    for row in raw_data:
        it = row.item
        dur = row.duration or 0
        bags = row.bags or 0
        
        if it not in item_stats:
            item_stats[it] = {"item": it, "total_duration": 0, "total_bags": 0, "max_days": 0}
            
        item_stats[it]["total_duration"] += (dur * bags)
        item_stats[it]["total_bags"] += bags
        if dur > item_stats[it]["max_days"]:
            item_stats[it]["max_days"] = dur

    data = []
    items = []
    avg_durations = []

    for it in item_stats:
        stats = item_stats[it]
        avg = round(stats["total_duration"] / stats["total_bags"], 1) if stats["total_bags"] > 0 else 0
        data.append({
            "item": it,
            "avg_days": avg,
            "max_days": stats["max_days"],
            "total_bags": stats["total_bags"]
        })
        items.append(it)
        avg_durations.append(avg)

    # Chart
    chart = {
        "data": {
            "labels": items,
            "datasets": [
                {"name": "Avg Storage Days", "values": avg_durations}
            ]
        },
        "type": "bar",
        "colors": ["#3498db"] # Blue
    }

    return columns, data, None, chart
