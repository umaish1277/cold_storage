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
        # Using a direct SQL query for efficiency
        current_bags = frappe.db.sql("""
            SELECT 
                (SELECT IFNULL(SUM(ri.number_of_bags), 0) 
                 FROM `tabCold Storage Receipt` r 
                 JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name 
                 WHERE r.docstatus = 1 AND r.warehouse = %s) - 
                (SELECT IFNULL(SUM(di.number_of_bags), 0) 
                 FROM `tabCold Storage Dispatch` d 
                 JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name 
                 WHERE d.docstatus = 1 AND di.warehouse = %s)
        """, (w.name, w.name))[0][0] or 0

        
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
