import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_warehouse_utilization(chart_name=None):
    """
    Returns data for the Warehouse Utilization dashboard chart.
    Format: { "labels": [...], "datasets": [{ "values": [...] }] }
    """
    # Get all warehouses with capacity
    warehouses = frappe.get_all("Warehouse", 
        fields=["name", "warehouse_name", "total_capacity_bags"],
        filters={"disabled": 0, "is_group": 0},
        order_by="warehouse_name"
    )
    
    labels = []
    values = []
    
    for w in warehouses:
        capacity = flt(w.total_capacity_bags)
        if capacity <= 0:
            continue
            
        # Calculate current stock (Bags)
        receipts = frappe.get_all("Cold Storage Receipt", 
            filters={"docstatus": 1, "warehouse": w.name}, 
            pluck="name", 
            ignore_permissions=True
        )
        
        in_bags = 0
        if receipts:
            in_items = frappe.get_all("Cold Storage Receipt Item",
                filters={"parent": ["in", receipts]},
                fields=["number_of_bags"],
                ignore_permissions=True
            )
            in_bags = sum(flt(item.number_of_bags) for item in in_items)
            
        out_items = frappe.get_all("Cold Storage Dispatch Item",
            filters={"docstatus": 1, "warehouse": w.name},
            fields=["number_of_bags"],
            ignore_permissions=True
        )
        out_bags = sum(flt(item.number_of_bags) for item in out_items)
        
        current_bags = in_bags - out_bags

        
        utilization = (flt(current_bags) / capacity) * 100
        
        labels.append(w.warehouse_name)
        values.append(flt(utilization, 2))
        
    return {
        "labels": labels,
        "datasets": [
            {
                "name": "Utilization (%)",
                "values": values
            }
        ]
    }
