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
    if lang:
        frappe.local.lang = lang
    
    # Force clear cache for this request to ensure fresh code/data
    frappe.clear_cache()
    
    frappe.logger().debug(f"Generating statement for {customer} (format: {format}, lang: {lang})")

    # Validate customer access
    if not customer:
        customer = get_customer_for_user()
    
    if not customer:
        frappe.throw(_("No customer linked to your account"))
    
    # Verify user has access to this customer
    if not can_access_customer(customer):
        frappe.throw(_("You do not have access to this customer's data"))
    
    from frappe.utils import today, add_days
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
    """Get detailed stock statement for a customer using optimized JOINs"""
    from frappe.utils import flt, getdate, today
    
    # Get all receipt items with dispatched quantities in one go
    # Using more robust SELECT to avoid SQL mode issues
    data = frappe.db.sql("""
        SELECT 
            r.name as receipt,
            r.receipt_date,
            r.warehouse,
            ri.goods_item as item,
            ri.item_group,
            ri.batch_no,
            ri.number_of_bags as received_qty,
            (SELECT COALESCE(SUM(di.number_of_bags), 0) 
             FROM `tabCold Storage Dispatch Item` di 
             JOIN `tabCold Storage Dispatch` d ON d.name = di.parent
             WHERE di.linked_receipt = r.name 
             AND di.batch_no = ri.batch_no
             AND d.docstatus = 1) as dispatched_qty
        FROM `tabCold Storage Receipt` r
        JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
        WHERE r.customer = %s 
        AND r.docstatus = 1
        AND r.receipt_date BETWEEN %s AND %s
        ORDER BY r.receipt_date DESC, r.name
    """, (customer, from_date, to_date), as_dict=True)
    
    # Calculate balances and days in store
    total_received = 0
    total_dispatched = 0
    today_date = getdate(today())
    
    results = []
    for row in data:
        row["balance_qty"] = flt(row["received_qty"]) - flt(row["dispatched_qty"])
        row["days_in_store"] = (today_date - getdate(row["receipt_date"])).days
        total_received += flt(row["received_qty"])
        total_dispatched += flt(row["dispatched_qty"])
        results.append(row)
    
    return {
        "customer": customer,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "generated_on": today(),
        "summary": {
            "total_received": total_received,
            "total_dispatched": total_dispatched,
            "total_balance": total_received - total_dispatched
        },
        "line_items": results
    }


def generate_excel(data, customer, from_date, to_date):
    """Generate Excel file for statement. Uses 'line_items' key."""
    from frappe.utils.xlsxutils import build_xlsx_response
    from frappe.utils import today
    from frappe import _
    
    if not data:
        data = {}

    # Prepare data for Excel
    rows = []
    
    # Header row
    rows.append([_("Customer Stock Statement")])
    rows.append([f"{_('Customer')}: {customer}"])
    
    p_from = from_date
    if hasattr(from_date, "strftime"):
        p_from = from_date.strftime('%d:%m:%Y')
    
    p_to = to_date
    if hasattr(to_date, "strftime"):
        p_to = to_date.strftime('%d:%m:%Y')

    rows.append([f"{_('Period')}: {p_from} {_('to')} {p_to}"])
    rows.append([f"{_('Generated')}: {today()}"])
    rows.append([])  # Empty row
    
    # Summary
    summary = data.get("summary", {})
    rows.append([_("Summary")])
    rows.append([_("Total Received"), summary.get("total_received", 0)])
    rows.append([_("Total Dispatched"), summary.get("total_dispatched", 0)])
    rows.append([_("Current Balance"), summary.get("total_balance", 0)])
    rows.append([])  # Empty row
    
    # Detail header
    rows.append([_("Receipt"), _("Date"), _("Warehouse"), _("Item"), _("Item Group"), _("Batch"), 
                 _("Received"), _("Dispatched"), _("Balance"), _("Days in Store")])
    
    items = data.get("line_items") or data.get("items") or []
    for item in items:
        receipt_date = item.get("receipt_date")
        formatted_date = str(receipt_date)
        if receipt_date and hasattr(receipt_date, "strftime"):
             formatted_date = receipt_date.strftime("%d:%m:%Y")
        
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
    rows.append([_("TOTAL"), "", "", "", "", "", 
                 summary.get("total_received", 0), 
                 summary.get("total_dispatched", 0), 
                 summary.get("total_balance", 0), ""])
    
    filename = f"Stock_Statement_{customer}_{today()}"
    build_xlsx_response(rows, filename)


def generate_pdf(data, customer, from_date, to_date, lang="en"):
    """Generate PDF statement using Frappe's PDF generator"""
    from frappe.utils import today
    
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
            "footer2": "Generated by Cold Storage Management System Powered By Umaish Solutions",
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
            "footer2": "کولڈ اسٹوریج مینجمنٹ سسٹم اور عمیش سلوشنز کی طرف سے تیار",
            "direction": "rtl"
        }
    }
    
    t = translations.get(lang, translations["en"])
    
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
    """Get last 6 months trend data for charts in a single query"""
    from frappe.utils import flt
    
    combined_data = frappe.db.sql("""
        SELECT 
            label, 
            SUM(qty_in) as inward, 
            SUM(qty_out) as outward
        FROM (
            SELECT DATE_FORMAT(receipt_date, '%%b %%y') as label, SUM(ri.number_of_bags) as qty_in, 0 as qty_out, receipt_date as sort_date
            FROM `tabCold Storage Receipt` r
            JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
            WHERE r.customer = %s AND r.docstatus = 1
            GROUP BY label
            
            UNION ALL
            
            SELECT DATE_FORMAT(dispatch_date, '%%b %%y') as label, 0 as qty_in, SUM(di.number_of_bags) as qty_out, dispatch_date as sort_date
            FROM `tabCold Storage Dispatch` d
            JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
            WHERE d.customer = %s AND d.docstatus = 1
            GROUP BY label
        ) AS t
        GROUP BY label
        ORDER BY MAX(sort_date) ASC
        LIMIT 6
    """, (customer, customer), as_dict=True)
    
    if not combined_data:
        return []

    max_val = max([flt(d.inward) for d in combined_data] + [flt(d.outward) for d in combined_data] + [1])
    
    chart_items = []
    for d in combined_data:
        chart_items.append({
            "label": d.label,
            "in_value": int(d.inward),
            "out_value": int(d.outward),
            "in_pct": int((flt(d.inward) / max_val) * 100),
            "out_pct": int((flt(d.outward) / max_val) * 100)
        })
    
    return chart_items


def get_bag_chart_data(customer):
    """Get stock by batch number for donut chart in a single query"""
    from frappe.utils import flt
    
    batch_data = frappe.db.sql("""
        SELECT 
            batch_no, 
            SUM(qty_in) - SUM(qty_out) as balance
        FROM (
            SELECT ri.batch_no, SUM(ri.number_of_bags) as qty_in, 0 as qty_out
            FROM `tabCold Storage Receipt` r
            JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
            WHERE r.customer = %s AND r.docstatus = 1
            GROUP BY ri.batch_no
            
            UNION ALL
            
            SELECT di.batch_no, 0 as qty_in, SUM(di.number_of_bags) as qty_out
            FROM `tabCold Storage Dispatch` d
            JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
            WHERE d.customer = %s AND d.docstatus = 1
            GROUP BY di.batch_no
        ) AS t
        GROUP BY batch_no
        HAVING balance > 0
    """, (customer, customer), as_dict=True)
    
    if not batch_data:
        return []
    
    total = sum([flt(d.balance) for d in batch_data]) or 1
    colors = ['#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#e74c3c']
    
    chart_items = []
    for i, d in enumerate(batch_data):
        chart_items.append({
            "label": d.batch_no,
            "value": int(d.balance),
            "pct": int((flt(d.balance) / total) * 100),
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
