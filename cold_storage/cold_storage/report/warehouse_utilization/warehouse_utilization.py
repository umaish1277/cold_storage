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
        
        jute_in = frappe.db.sql("""
            SELECT IFNULL(SUM(ri.number_of_bags), 0)
            FROM `tabCold Storage Receipt` r 
            JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name 
            WHERE r.docstatus = 1 AND r.warehouse = %s 
            AND (ri.item_group = 'Jute Bag' OR ri.item_group IS NULL OR ri.item_group = '')
        """, (w.name,))[0][0] or 0
        
        # DEBUG: Verifying code execution path
        frappe.logger().debug(f"Executing Warehouse Utilization for {w.name}")
        sql_query = """
            SELECT IFNULL(SUM(di.number_of_bags), 0)
            FROM `tabCold Storage Dispatch` dispatch_parent 
            JOIN `tabCold Storage Dispatch Item` di ON di.parent = dispatch_parent.name 
            WHERE dispatch_parent.docstatus = 1 AND di.warehouse = %s
            AND (di.item_group = 'Jute Bag' OR di.item_group IS NULL OR di.item_group = '')
        """
        # frappe.throw(sql_query % f"'{w.name}'") # Un-comment to see the query in UI
        jute_out = frappe.db.sql(sql_query, (w.name,))[0][0] or 0
        
        jute_bags = jute_in - jute_out
        
        net_in = frappe.db.sql("""
            SELECT IFNULL(SUM(ri.number_of_bags), 0)
            FROM `tabCold Storage Receipt` r 
            JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name 
            WHERE r.docstatus = 1 AND r.warehouse = %s 
            AND ri.item_group = 'Net Bag'
        """, (w.name,))[0][0] or 0
        
        net_out = frappe.db.sql("""
            SELECT IFNULL(SUM(di.number_of_bags), 0)
            FROM `tabCold Storage Dispatch` dispatch_parent 
            JOIN `tabCold Storage Dispatch Item` di ON di.parent = dispatch_parent.name 
            WHERE dispatch_parent.docstatus = 1 AND di.warehouse = %s
            AND di.item_group = 'Net Bag'
        """, (w.name,))[0][0] or 0
        
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

