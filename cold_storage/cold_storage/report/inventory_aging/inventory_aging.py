# Copyright (c) 2026, Cold Storage and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, date_diff, getdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data, filters)
    return columns, data, None, chart

def get_columns():
    return [
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Receipt"), "fieldname": "receipt", "fieldtype": "Link", "options": "Cold Storage Receipt", "width": 140},
        {"label": _("Receipt Date"), "fieldname": "receipt_date", "fieldtype": "Date", "width": 100},
        {"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Data", "width": 100},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 130},
        {"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Int", "width": 100},
        {"label": _("Age (Days)"), "fieldname": "age_days", "fieldtype": "Int", "width": 90},
        {"label": _("Age Bucket"), "fieldname": "age_bucket", "fieldtype": "Data", "width": 110},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

def get_data(filters):
    conditions = ""
    if filters.get("customer"):
        conditions += f" AND r.customer = '{filters.get('customer')}'"
    if filters.get("warehouse"):
        conditions += f" AND r.warehouse = '{filters.get('warehouse')}'"
    if filters.get("item"):
        conditions += f" AND ri.goods_item = '{filters.get('item')}'"
    
    # Fetch all submitted receipts with items
    receipts = frappe.db.sql(f"""
        SELECT 
            r.name as receipt, 
            r.customer, 
            r.warehouse, 
            r.receipt_date,
            ri.goods_item as item, 
            ri.batch_no, 
            ri.number_of_bags as in_qty
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.docstatus = 1 {conditions}
        ORDER BY r.receipt_date ASC
    """, as_dict=True)
    
    data = []
    threshold = filters.get("threshold_days") or 30
    today_date = getdate(today())
    
    for r in receipts:
        # Calculate dispatched quantity for this receipt + batch
        out_qty = frappe.db.sql("""
            SELECT COALESCE(SUM(di.number_of_bags), 0)
            FROM `tabCold Storage Dispatch` d
            JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
            WHERE d.docstatus = 1 AND di.linked_receipt = %s AND di.batch_no = %s
        """, (r.receipt, r.batch_no))[0][0] or 0
        
        balance = r.in_qty - out_qty
        
        # Skip zero balance items unless explicitly requested
        if balance <= 0 and not filters.get("show_zero_balance"):
            continue
        
        age_days = date_diff(today_date, r.receipt_date)
        age_bucket = get_age_bucket(age_days)
        
        # Determine status based on threshold
        if age_days > threshold:
            status = "⚠️ Overdue"
        elif age_days > (threshold * 0.8):  # 80% of threshold = warning
            status = "⏳ Warning"
        else:
            status = "✅ Fresh"
        
        # Apply age filter if specified
        min_age = filters.get("min_age_days") or 0
        max_age = filters.get("max_age_days")
        
        if age_days < min_age:
            continue
        if max_age and age_days > max_age:
            continue
        
        data.append({
            "customer": r.customer,
            "receipt": r.receipt,
            "receipt_date": r.receipt_date,
            "item": r.item,
            "batch_no": r.batch_no,
            "warehouse": r.warehouse,
            "balance_qty": balance,
            "age_days": age_days,
            "age_bucket": age_bucket,
            "status": status
        })
    
    # Sort by age descending (oldest first) to highlight aging stock
    data.sort(key=lambda x: x["age_days"], reverse=True)
    
    return data

def get_age_bucket(age_days):
    """Categorize age into buckets for easy analysis"""
    if age_days <= 7:
        return "0-7 days"
    elif age_days <= 30:
        return "8-30 days"
    elif age_days <= 60:
        return "31-60 days"
    elif age_days <= 90:
        return "61-90 days"
    else:
        return "90+ days"

def get_chart(data, filters):
    """Generate a bar chart showing stock distribution by age bucket"""
    if not data:
        return None
    
    # Aggregate quantities by age bucket
    bucket_totals = {}
    bucket_order = ["0-7 days", "8-30 days", "31-60 days", "61-90 days", "90+ days"]
    
    for bucket in bucket_order:
        bucket_totals[bucket] = 0
    
    for row in data:
        bucket = row.get("age_bucket")
        if bucket in bucket_totals:
            bucket_totals[bucket] += row.get("balance_qty", 0)
    
    return {
        "data": {
            "labels": bucket_order,
            "datasets": [
                {
                    "name": "Balance Qty (Bags)",
                    "values": [bucket_totals[b] for b in bucket_order]
                }
            ]
        },
        "type": "bar",
        "colors": ["#27ae60", "#3498db", "#f39c12", "#e67e22", "#e74c3c"]
    }
