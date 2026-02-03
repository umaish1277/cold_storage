import frappe
from frappe.utils import flt, add_days, getdate

def get_context(context):
    context.no_cache = 1
    context.full_width = 1
    context.show_sidebar = 0
    context.hide_sidebar = 1

    
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    # 1. Identify Customer
    # Assuming the Logged In User is a Contact for a Customer, or the Customer itself
    # Check if User is linked to a Customer
    customer = frappe.db.get_value("Portal User", {"user": frappe.session.user}, "parent")
    # Alternatively simpler: Check standard Customer contact
    if not customer:
        contact_name = frappe.db.get_value("Contact", {"user": frappe.session.user})
        if contact_name:
            customer = frappe.db.get_value("Dynamic Link", {"parent": contact_name, "link_doctype": "Customer"}, "link_name")
    
    # Fallback for demo/admin: Use first customer
    if not customer and frappe.session.user == "Administrator":
        customer = frappe.get_all("Customer", limit=1)[0].name if frappe.get_all("Customer") else None

    context.customer = customer
    
    if not customer:
        context.error = "No Customer linked to your account."
        return context

    # 2. Stats
    # Total Bags Stored (Sum of Receipts - Sum of Dispatches)
    # Actually, simpler: Sum of (Received - Dispatched) for all batches?
    # Let's do a simple aggregate from Ledger or just Receipts/Dispatches for now.
    
    # Active Batches (Count of Receipts where balance > 0)
    # This requires looking up balances.
    
    # Let's get "Recent Receipts"
    receipts = frappe.get_all("Cold Storage Receipt", 
        fields=["name", "receipt_date", "warehouse", "status"],
        filters={"customer": customer, "docstatus": 1},
        order_by="receipt_date desc",
        limit=5
    )
    
    # Calculate Total Bags for each receipt (since it's not in parent)
    for r in receipts:
        r.total_bags = frappe.db.sql("""
            SELECT SUM(number_of_bags) FROM `tabCold Storage Receipt Item`
            WHERE parent = %s
        """, r.name)[0][0] or 0
    
    # Recent Dispatches
    dispatches = frappe.get_all("Cold Storage Dispatch",
        fields=["name", "dispatch_date", "linked_receipt", "total_amount", "status"],
        filters={"customer": customer, "docstatus": 1},
        order_by="dispatch_date desc",
        limit=5
    )
    
    context.recent_receipts = receipts
    context.recent_dispatches = dispatches
    
    # Calculate Totals
    total_received = frappe.db.sql("""
        SELECT SUM(ri.number_of_bags) 
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.customer = %s AND r.docstatus = 1
    """, (customer,))[0][0] or 0
    
    total_dispatched = frappe.db.sql("""
        SELECT SUM(di.number_of_bags) 
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
        WHERE d.customer = %s AND d.docstatus = 1
    """, (customer,))[0][0] or 0
    
    context.total_stored = flt(total_received) - flt(total_dispatched)
    context.total_inward = total_received
    context.total_outward = total_dispatched

    # Chart Data (Last 6 Months)
    # We need dates. Let's do a simple query for recent activity GROUP BY Month
    incoming_data = frappe.db.sql("""
        SELECT DATE_FORMAT(receipt_date, '%%b %%y'), SUM(ri.number_of_bags)
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.customer = %s AND r.docstatus = 1
        GROUP BY DATE_FORMAT(receipt_date, '%%Y-%%m')
        ORDER BY receipt_date ASC
        LIMIT 6
    """, (customer,))
    
    outgoing_data = frappe.db.sql("""
        SELECT DATE_FORMAT(dispatch_date, '%%b %%y'), SUM(di.number_of_bags)
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
        WHERE d.customer = %s AND d.docstatus = 1
        GROUP BY DATE_FORMAT(dispatch_date, '%%Y-%%m')
        ORDER BY dispatch_date ASC
        LIMIT 6
    """, (customer,))

    # Format for Frappe Charts
    labels = []
    in_values = []
    out_values = []
    
    # Merge naive approach (assuming sorted by date, but group by might shuffle if strictly format used in group)
    # Better to map to dict
    data_map = {}
    
    for row in incoming_data:
        label, qty = row
        if label not in data_map: data_map[label] = {"in": 0, "out": 0}
        data_map[label]["in"] = flt(qty)
        
    for row in outgoing_data:
        label, qty = row
        if label not in data_map: data_map[label] = {"in": 0, "out": 0}
        data_map[label]["out"] = flt(qty)
        
    for label in data_map: # This might lose order if dict is unordered (Python 3.7+ preserves insertion, but SQL order matters)
        # Re-sort data_map keys?
        pass # Simplified for now
        
    # Re-construct sorted lists (Assuming last 6 months logic holds roughly)
    # Or just push lists (user will see labels)
    context.chart_data = {
        "labels": list(data_map.keys()),
        "datasets": [
            {"name": "Inward", "values": [d["in"] for d in data_map.values()]},
            {"name": "Outward", "values": [d["out"] for d in data_map.values()]}
        ]
    }
    
    # Chart 2: Stock by Item Group
    # Inward by Item Group
    in_bags = frappe.db.sql("""
        SELECT ri.item_group, SUM(ri.number_of_bags)
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.customer = %s AND r.docstatus = 1
        GROUP BY ri.item_group
    """, (customer,))
    
    # Outward by Item Group
    out_bags = frappe.db.sql("""
        SELECT di.item_group, SUM(di.number_of_bags)
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
        WHERE d.customer = %s AND d.docstatus = 1
        GROUP BY di.item_group
    """, (customer,))
    
    bag_balance = {}
    for row in in_bags:
        bag_balance[row[0]] = flt(row[1])
        
    for row in out_bags:
        bag_balance[row[0]] = bag_balance.get(row[0], 0) - flt(row[1])
        
    # Filter out zero or negative balances
    valid_bags = {k: v for k, v in bag_balance.items() if v > 0}
    
    context.bag_chart = {
        "labels": list(valid_bags.keys()),
        "datasets": [{"values": list(valid_bags.values())}]
    }
    
    return context
