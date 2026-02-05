
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
    # Fetch Dispatch Items with parent data
    dispatch_filters = {"docstatus": 1}
    if filters.get("from_date"): dispatch_filters["dispatch_date"] = [">=", filters.get("from_date")]
    if filters.get("to_date"): dispatch_filters["dispatch_date"] = ["<=", filters.get("to_date")]
    
    dispatches = frappe.get_all("Cold Storage Dispatch", 
        filters=dispatch_filters, 
        fields=["name", "dispatch_date"],
        ignore_permissions=True
    )
    dispatch_map = {d.get("name"): d.get("dispatch_date") for d in dispatches}
    
    if not dispatches:
        return columns, [], None, None
        
    items = frappe.get_all("Cold Storage Dispatch Item",
        filters={
            "parent": ["in", list(dispatch_map.keys())],
            "linked_receipt": ["is", "set"]
        },
        fields=["goods_item", "number_of_bags", "linked_receipt", "parent"],
        ignore_permissions=True
    )
    
    # Get Receipt dates
    receipt_names = list(set(i.get("linked_receipt") for i in items))
    receipts = frappe.get_all("Cold Storage Receipt",
        filters={"name": ["in", receipt_names]},
        fields=["name", "receipt_date"],
        ignore_permissions=True
    )
    receipt_map = {r.get("name"): r.get("receipt_date") for r in receipts}
    
    # Prepare data for aggregation
    raw_data = []
    for i in items:
        disp_date = dispatch_map.get(i.get("parent"))
        rec_date = receipt_map.get(i.get("linked_receipt"))
        if disp_date and rec_date:
            duration = date_diff(disp_date, rec_date)
            raw_data.append({
                "item": i.get("goods_item"),
                "duration": duration,
                "bags": i.get("number_of_bags")
            })

    # Aggregate by Item
    item_stats = {}
    for row in raw_data:
        it = row.get("item")
        dur = row.get("duration") or 0
        bags = row.get("bags") or 0
        
        if it not in item_stats:
            item_stats[it] = {"item": it, "total_duration": 0, "total_bags": 0, "max_days": 0}
            
        item_stats[it]["total_duration"] += (dur * bags)
        item_stats[it]["total_bags"] += bags
        if dur > item_stats[it]["max_days"]:
            item_stats[it]["max_days"] = dur

    data = []
    chart_items = []
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
        chart_items.append(it)
        avg_durations.append(avg)

    # Chart
    chart = {
        "data": {
            "labels": chart_items,
            "datasets": [
                {"name": "Avg Storage Days", "values": avg_durations}
            ]
        },
        "type": "bar",
        "colors": ["#3498db"] # Blue
    }

    return columns, data, None, chart
