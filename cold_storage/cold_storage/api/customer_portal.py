# Copyright (c) 2026, Cold Storage and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today
import io

@frappe.whitelist()
def get_customer_statement(customer=None, from_date=None, to_date=None, format="json"):
    """
    Get customer stock statement for portal download.
    Format can be 'json', 'pdf', or 'xlsx'
    """
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
        from_date = frappe.utils.add_days(today(), -365)
    if not to_date:
        to_date = today()
    
    # Get statement data
    data = get_statement_data(customer, from_date, to_date)
    
    if format == "json":
        return data
    elif format == "xlsx":
        return generate_excel(data, customer, from_date, to_date)
    elif format == "pdf":
        return generate_pdf(data, customer, from_date, to_date)
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
    from frappe.utils.xlsxutils import make_xlsx
    
    # Prepare data for Excel
    rows = []
    
    # Header row
    rows.append(["Customer Stock Statement"])
    rows.append([f"Customer: {customer}"])
    rows.append([f"Period: {from_date} to {to_date}"])
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
    
    # Detail rows
    for item in data["items"]:
        rows.append([
            item.get("receipt"),
            str(item.get("receipt_date")),
            item.get("warehouse"),
            item.get("item"),
            item.get("item_group"),
            item.get("batch_no"),
            item.get("received_qty"),
            item.get("dispatched_qty"),
            item.get("balance_qty"),
            item.get("days_in_store")
        ])
    
    xlsx_file = make_xlsx(rows, "Stock Statement")
    
    # Return as downloadable file
    frappe.response["filename"] = f"Stock_Statement_{customer}_{today()}.xlsx"
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"] = "download"


def generate_pdf(data, customer, from_date, to_date):
    """Generate PDF statement using Frappe's PDF generator"""
    
    html = frappe.render_template(
        "cold_storage/templates/customer_statement.html",
        {
            "data": data,
            "customer": customer,
            "from_date": from_date,
            "to_date": to_date,
            "generated_on": today()
        }
    )
    
    from frappe.utils.pdf import get_pdf
    pdf = get_pdf(html)
    
    frappe.response["filename"] = f"Stock_Statement_{customer}_{today()}.pdf"
    frappe.response["filecontent"] = pdf
    frappe.response["type"] = "download"


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
