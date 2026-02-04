# Copyright (c) 2026, Cold Storage and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart

def get_columns():
    return [
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 200},
        {"label": _("Capacity (Bags)"), "fieldname": "capacity", "fieldtype": "Int", "width": 120},
        {"label": _("Current Stock"), "fieldname": "current_stock", "fieldtype": "Int", "width": 120},
        {"label": _("Utilization (%)"), "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
        {"label": _("Available Space"), "fieldname": "available", "fieldtype": "Int", "width": 120},
    ]

def get_data(filters):
    # Get all warehouses with capacity
    warehouses = frappe.get_all("Warehouse", 
        fields=["name", "warehouse_name", "total_capacity_bags"],
        filters={"disabled": 0, "is_group": 0},
        order_by="warehouse_name"
    )
    
    data = []
    
    for w in warehouses:
        capacity = flt(w.total_capacity_bags)
        if capacity <= 0:
            continue
            
        # Calculate current stock (Bags)
        current_bags = frappe.db.sql("""
            SELECT 
                (SELECT IFNULL(SUM(ri.number_of_bags), 0) 
                 FROM `tabCold Storage Receipt` r 
                 JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name 
                 WHERE r.docstatus = 1 AND r.warehouse = %s) - 
                (SELECT IFNULL(SUM(di.number_of_bags), 0) 
                 FROM `tabCold Storage Dispatch` d 
                 JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name 
                 WHERE d.docstatus = 1 AND d.warehouse = %s)
        """, (w.name, w.name))[0][0] or 0

        utilization = (flt(current_bags) / capacity) * 100
        available = capacity - current_bags
        
        data.append({
            "warehouse": w.warehouse_name,
            "capacity": int(capacity),
            "current_stock": int(current_bags),
            "utilization": flt(utilization, 2),
            "available": int(available) if available > 0 else 0
        })
    
    return data

def get_chart(data):
    """Generate a bar chart showing warehouse utilization percentages"""
    if not data:
        return None
    
    labels = [d["warehouse"] for d in data]
    values = [d["utilization"] for d in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Utilization (%)"),
                    "values": values
                }
            ]
        },
        "type": "bar",
        "colors": ["#4299E1"]
    }
