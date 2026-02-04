# Copyright (c) 2026, Cold Storage and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()
def get_customer_statement(customer=None, from_date=None, to_date=None, format="json", lang="en"):
    """
    Get customer stock statement for portal download.
    Format can be 'json', 'pdf', or 'xlsx'
    Lang can be 'en' (English) or 'ur' (Urdu)
    """
    # Force reload of utils within the call to bypass caching
    from frappe.utils import today, add_days

    # Validate customer access
    if not customer:
        customer = get_customer_for_user()
    
    if not customer:
        frappe.throw(_("No customer linked to your account"))
    
    # Verify user has access to this customer
    if not can_access_customer(customer):
        frappe.throw(_("You do not have access to this customer's data"))
    
    # Default date range: last 1 year
    if not from_date:
        from_date = add_days(today(), -365)
    if not to_date:
        to_date = today()
    
    # Get statement data
    data = get_statement_data(customer, from_date, to_date)
    
    if format == "json":
        return data
    elif format == "xlsx":
        generate_excel(data, customer, from_date, to_date)
        return
    elif format == "pdf":
        generate_pdf(data, customer, from_date, to_date, lang)
        return
    else:
        frappe.throw(_("Invalid format. Use 'json', 'xlsx', or 'pdf'"))


def get_customer_for_user():
    """Get customer linked to current user"""
    user = frappe.session.user
    
    if user == "Guest":
        return None
    
    # Check Portal User
    customer = frappe.db.get_value("Portal User", {"user": user}, "parent")
    
    # Check Contact
    if not customer:
        contact_name = frappe.db.get_value("Contact", {"user": user})
        if contact_name:
            customer = frappe.db.get_value("Dynamic Link", {
                "parent": contact_name, 
                "link_doctype": "Customer"
            }, "link_name")
    
    # Admin fallback
    if not customer and user == "Administrator":
        customers = frappe.get_all("Customer", limit=1)
        if customers:
            customer = customers[0].name
    
    return customer


def can_access_customer(customer):
    """Check if current user can access this customer's data"""
    user = frappe.session.user
    
    if user == "Administrator":
        return True
    
    # Check if user is linked to this customer
    user_customer = get_customer_for_user()
    return user_customer == customer


def get_statement_data(customer, from_date, to_date):
    """Get detailed stock statement for a customer"""
    from frappe.utils import flt, getdate, today
    
    # Get all receipt items with dispatched quantities
    data = frappe.db.sql("""
        SELECT 
            r.name as receipt,
            r.receipt_date,
            r.warehouse,
            ri.goods_item as item,
            ri.item_group,
            ri.batch_no,
            ri.number_of_bags as received_qty,
            COALESCE((
                SELECT SUM(di.number_of_bags)
                FROM `tabCold Storage Dispatch` d
                JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
                WHERE d.docstatus = 1 
                AND di.linked_receipt = r.name 
                AND di.batch_no = ri.batch_no
            ), 0) as dispatched_qty
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.customer = %s 
        AND r.docstatus = 1
        AND r.receipt_date BETWEEN %s AND %s
        ORDER BY r.receipt_date DESC, r.name
    """, (customer, from_date, to_date), as_dict=True)
    
    # Calculate balances and days in store
    for row in data:
        row["balance_qty"] = flt(row["received_qty"]) - flt(row["dispatched_qty"])
        row["days_in_store"] = (getdate(today()) - getdate(row["receipt_date"])).days
    
    # Summary stats
    total_received = sum(flt(r.get("received_qty", 0)) for r in data)
    total_dispatched = sum(flt(r.get("dispatched_qty", 0)) for r in data)
    total_balance = sum(flt(r.get("balance_qty", 0)) for r in data)
    
    return {
        "customer": customer,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "generated_on": today(),
        "summary": {
            "total_received": total_received,
            "total_dispatched": total_dispatched,
            "total_balance": total_balance
        },
        "line_items": data
    }


def generate_excel(data, customer, from_date, to_date):
    """Generate Excel file for statement"""
    from frappe.utils.xlsxutils import build_xlsx_response
    from frappe.utils import today
    
    # Prepare data for Excel
    rows = []
    
    # Header row
    rows.append(["Customer Stock Statement"])
    rows.append([f"Customer: {customer}"])
    rows.append([f"Period: {from_date.strftime('%d:%m:%Y') if hasattr(from_date, 'strftime') else from_date} to {to_date.strftime('%d:%m:%Y') if hasattr(to_date, 'strftime') else to_date}"])
    rows.append([f"Generated: {today()}"])
    rows.append([])  # Empty row
    
    # Summary
    rows.append(["Summary"])
    rows.append(["Total Received", data["summary"]["total_received"]])
    rows.append(["Total Dispatched", data["summary"]["total_dispatched"]])
    rows.append(["Current Balance", data["summary"]["total_balance"]])
    rows.append([])  # Empty row
    
    # Detail header
    rows.append(["Receipt", "Receipt Date", "Warehouse", "Item", "Item Group", "Batch No", 
                 "Received", "Dispatched", "Balance", "Days in Store"])
    
    for item in data.get("line_items", []):
        receipt_date = item.get("receipt_date")
        formatted_date = receipt_date.strftime("%d:%m:%Y") if receipt_date and hasattr(receipt_date, "strftime") else str(receipt_date)
        
        rows.append([
            item.get("receipt"),
            formatted_date,
            item.get("warehouse"),
            item.get("item"),
            item.get("item_group"),
            item.get("batch_no"),
            item.get("received_qty"),
            item.get("dispatched_qty"),
            item.get("balance_qty"),
            item.get("days_in_store")
        ])
    
    # Add Total row at the bottom
    rows.append([])
    rows.append(["TOTAL", "", "", "", "", "", 
                 data["summary"]["total_received"], 
                 data["summary"]["total_dispatched"], 
                 data["summary"]["total_balance"], ""])
    
    # Use standard build_xlsx_response which handles both creation and response setup
    filename = f"Stock_Statement_{customer}_{today()}"
    build_xlsx_response(rows, filename)


def generate_pdf(data, customer, from_date, to_date, lang="en"):
    """Generate PDF statement using Frappe's PDF generator"""
    from frappe.utils import today
    
    # Translations
    translations = {
        "en": {
            "title": "Stock Statement",
            "subtitle": "Cold Storage Inventory Report",
            "customer": "Customer",
            "period": "Period",
            "generated": "Generated",
            "total_received": "Total Received",
            "total_dispatched": "Total Dispatched",
            "current_balance": "Current Balance",
            "stock_trends": "Stock Trends (Last 6 Months)",
            "stock_by_batch_no": "Stock by Batch No",
            "inward": "Inward",
            "outward": "Outward",
            "detailed_register": "Detailed Stock Register",
            "receipt": "Receipt",
            "date": "Date",
            "item": "Item",
            "batch": "Batch",
            "warehouse": "Warehouse",
            "received": "Received",
            "dispatched": "Dispatched",
            "balance": "Balance",
            "days": "Days",
            "bags": "Bags",
            "no_data": "No data available",
            "no_trend_data": "No trend data available",
            "footer1": "This is a computer-generated statement. No signature required.",
            "footer2": "Generated by Cold Storage Management System",
            "direction": "ltr"
        },
        "ur": {
            "title": "اسٹاک اسٹیٹمنٹ",
            "subtitle": "کولڈ اسٹوریج انوینٹری رپورٹ",
            "customer": "گاہک",
            "period": "مدت",
            "generated": "تاریخ اجراء",
            "total_received": "کل موصول",
            "total_dispatched": "کل روانہ",
            "current_balance": "موجودہ بیلنس",
            "stock_trends": "اسٹاک رجحانات (آخری 6 ماہ)",
            "stock_by_batch_no": "بیچ نمبر کے لحاظ سے اسٹاک",
            "inward": "اندر آنے والا",
            "outward": "باہر جانے والا",
            "detailed_register": "تفصیلی اسٹاک رجسٹر",
            "receipt": "رسید",
            "date": "تاریخ",
            "item": "آئٹم",
            "batch": "بیچ",
            "warehouse": "گودام",
            "received": "موصول",
            "dispatched": "روانہ",
            "balance": "بیلنس",
            "days": "دن",
            "bags": "بیگ",
            "no_data": "کوئی ڈیٹا دستیاب نہیں",
            "no_trend_data": "کوئی رجحان ڈیٹا دستیاب نہیں",
            "footer1": "یہ کمپیوٹر سے تیار کردہ اسٹیٹمنٹ ہے۔ دستخط کی ضرورت نہیں۔",
            "footer2": "کولڈ اسٹوریج مینجمنٹ سسٹم کی طرف سے تیار",
            "direction": "rtl"
        }
    }
    
    t = translations.get(lang, translations["en"])
    
    # Generate chart data for PDF
    trend_chart = get_trend_chart_data(customer)
    bag_chart = get_bag_chart_data(customer)
    
    html = frappe.render_template(
        "cold_storage/templates/customer_statement.html",
        {
            "data": data,
            "customer": customer,
            "from_date": from_date,
            "to_date": to_date,
            "generated_on": today(),
            "trend_chart": trend_chart,
            "bag_chart": bag_chart,
            "t": t,
            "lang": lang
        }
    )
    
    from frappe.utils.pdf import get_pdf
    pdf = get_pdf(html)
    
    frappe.response["filename"] = f"Stock_Statement_{customer}_{today()}.pdf"
    frappe.response["filecontent"] = pdf
    frappe.response["type"] = "download"


def get_trend_chart_data(customer):
    """Get last 6 months trend data for charts"""
    from frappe.utils import flt
    
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
    
    data_map = {}
    for row in incoming_data:
        label, qty = row
        if label not in data_map:
            data_map[label] = {"in": 0, "out": 0}
        data_map[label]["in"] = flt(qty)
        
    for row in outgoing_data:
        label, qty = row
        if label not in data_map:
            data_map[label] = {"in": 0, "out": 0}
        data_map[label]["out"] = flt(qty)
    
    # Calculate max for scaling
    max_val = 1
    for d in data_map.values():
        max_val = max(max_val, d["in"], d["out"])
    
    # Build chart data with percentages for bar heights
    chart_items = []
    for label, vals in data_map.items():
        chart_items.append({
            "label": label,
            "in_value": int(vals["in"]),
            "out_value": int(vals["out"]),
            "in_pct": int((vals["in"] / max_val) * 100) if max_val else 0,
            "out_pct": int((vals["out"] / max_val) * 100) if max_val else 0
        })
    
    return chart_items


def get_bag_chart_data(customer):
    """Get stock by item group for donut chart"""
    from frappe.utils import flt
    
    in_bags = frappe.db.sql("""
        SELECT ri.batch_no, SUM(ri.number_of_bags)
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.customer = %s AND r.docstatus = 1
        GROUP BY ri.batch_no
    """, (customer,))
    
    out_bags = frappe.db.sql("""
        SELECT di.batch_no, SUM(di.number_of_bags)
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
        WHERE d.customer = %s AND d.docstatus = 1
        GROUP BY di.batch_no
    """, (customer,))
    
    bag_balance = {}
    for row in in_bags:
        bag_balance[row[0]] = flt(row[1])
        
    for row in out_bags:
        bag_balance[row[0]] = bag_balance.get(row[0], 0) - flt(row[1])
    
    # Filter out zero or negative and calculate totals
    valid_bags = {k: v for k, v in bag_balance.items() if v > 0}
    total = sum(valid_bags.values()) or 1
    
    colors = ['#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#e74c3c']
    chart_items = []
    for i, (label, value) in enumerate(valid_bags.items()):
        chart_items.append({
            "label": label,
            "value": int(value),
            "pct": int((value / total) * 100),
            "color": colors[i % len(colors)]
        })
    
    return chart_items


@frappe.whitelist()
def get_customer_info():
    """Get basic customer info for current user"""
    customer = get_customer_for_user()
    
    if not customer:
        return {"error": "No customer linked"}
    
    return {
        "customer": customer,
        "customer_name": frappe.db.get_value("Customer", customer, "customer_name")
    }
