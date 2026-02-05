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
        {"label": _("Capacity (Jute Eq.)"), "fieldname": "capacity", "fieldtype": "Float", "precision": 1, "width": 140},
        {"label": _("Jute Bags"), "fieldname": "jute_bags", "fieldtype": "Int", "width": 100},
        {"label": _("Net Bags"), "fieldname": "net_bags", "fieldtype": "Int", "width": 100},
        {"label": _("Equivalent Stock"), "fieldname": "equivalent_stock", "fieldtype": "Float", "precision": 1, "width": 130},
        {"label": _("Utilization (%)"), "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
        {"label": _("Available Space"), "fieldname": "available", "fieldtype": "Float", "precision": 1, "width": 120},
    ]

def get_data(filters):
    """
    Calculate warehouse utilization with bag type conversion:
    - Capacity is measured in Jute Bag equivalents
    - 2 Net Bags = 1 Jute Bag equivalent
    - Equivalent Stock = Jute Bags + (Net Bags / 2)
    """
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
        
        # Calculate Jute Bags In
        # We need to filter by Receipt's warehouse because Receipt Item doesn't have it
        receipts = frappe.get_all("Cold Storage Receipt", 
            filters={"docstatus": 1, "warehouse": w.name}, 
            pluck="name", 
            ignore_permissions=True
        )
        
        jute_in = 0
        if receipts:
            jute_in_items = frappe.get_all("Cold Storage Receipt Item",
                filters={
                    "parent": ["in", receipts],
                    "item_group": ["in", ["Jute Bag", None, ""]]
                },
                fields=["number_of_bags"],
                ignore_permissions=True
            )
            jute_in = sum(flt(item.number_of_bags) for item in jute_in_items)
        
        # Calculate Jute Bags Out
        # Dispatch Item has warehouse directly
        jute_out_items = frappe.get_all("Cold Storage Dispatch Item",
            filters={
                "warehouse": w.name,
                "docstatus": 1,
                "item_group": ["in", ["Jute Bag", None, ""]]
            },
            fields=["number_of_bags"],
            ignore_permissions=True
        )
        jute_out = sum(flt(item.number_of_bags) for item in jute_out_items)
        
        jute_bags = jute_in - jute_out
        
        # Calculate Net Bags In
        net_in = 0
        if receipts:
            net_in_items = frappe.get_all("Cold Storage Receipt Item",
                filters={
                    "parent": ["in", receipts],
                    "item_group": "Net Bag"
                },
                fields=["number_of_bags"],
                ignore_permissions=True
            )
            net_in = sum(flt(item.number_of_bags) for item in net_in_items)
        
        # Calculate Net Bags Out
        net_out_items = frappe.get_all("Cold Storage Dispatch Item",
            filters={
                "warehouse": w.name,
                "docstatus": 1,
                "item_group": "Net Bag"
            },
            fields=["number_of_bags"],
            ignore_permissions=True
        )
        net_out = sum(flt(item.number_of_bags) for item in net_out_items)
        
        net_bags = net_in - net_out
        
        # Calculate equivalent stock: 2 Net Bags = 1 Jute Bag
        equivalent_stock = flt(jute_bags) + (flt(net_bags) / 2)
        
        utilization = (equivalent_stock / capacity) * 100
        available = capacity - equivalent_stock
        
        data.append({
            "warehouse": w.warehouse_name,
            "capacity": flt(capacity, 1),
            "jute_bags": int(jute_bags) if jute_bags > 0 else 0,
            "net_bags": int(net_bags) if net_bags > 0 else 0,
            "equivalent_stock": flt(equivalent_stock, 1),
            "utilization": flt(utilization, 2),
            "available": flt(available, 1) if available > 0 else 0
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

