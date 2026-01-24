from __future__ import annotations
import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    txn_type = filters.get("txn_type")
    customer = filters.get("customer")

    columns = [
        {"label": "Type", "fieldname": "txn_type", "fieldtype": "Data", "width": 90},
        {"label": "Document", "fieldname": "docname", "fieldtype": "Dynamic Link", "options": "doctype_name", "width": 180},
        {"label": "Date/Time", "fieldname": "dt", "fieldtype": "Datetime", "width": 170},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 220},
        {"label": "Contract", "fieldname": "contract", "fieldtype": "Link", "options": "Storage Contract", "width": 160},
        {"label": "Reference", "fieldname": "reference", "fieldtype": "Data", "width": 180},
        {"label": "Workflow State", "fieldname": "workflow_state", "fieldtype": "Data", "width": 150},
        {"label": "doctype_name", "fieldname": "doctype_name", "fieldtype": "Data", "hidden": 1},
    ]

    params = {}
    date_cond_recv = ""
    date_cond_disp = ""
    cust_cond = ""

    if customer:
        cust_cond = " and customer=%(customer)s"
        params["customer"] = customer

    if from_date:
        params["from_date"] = f"{getdate(from_date)} 00:00:00"
        date_cond_recv += " and receiving_datetime >= %(from_date)s"
        date_cond_disp += " and dispatch_datetime >= %(from_date)s"

    if to_date:
        params["to_date"] = f"{getdate(to_date)} 23:59:59"
        date_cond_recv += " and receiving_datetime <= %(to_date)s"
        date_cond_disp += " and dispatch_datetime <= %(to_date)s"

    data = []

    if not txn_type or txn_type == "Receive":
        data += frappe.db.sql(
            f"""
            select 'Receive' as txn_type,
                   name as docname,
                   receiving_datetime as dt,
                   customer, contract, reference, workflow_state,
                   'Cold Storage Receive Goods' as doctype_name
            from `tabCold Storage Receive Goods`
            where docstatus=0 and workflow_state='CS Pending Approval'
            {cust_cond} {date_cond_recv}
            """,
            params,
            as_dict=True,
        )

    if not txn_type or txn_type == "Dispatch":
        data += frappe.db.sql(
            f"""
            select 'Dispatch' as txn_type,
                   name as docname,
                   dispatch_datetime as dt,
                   customer, contract, reference, workflow_state,
                   'Cold Storage Dispatch Goods' as doctype_name
            from `tabCold Storage Dispatch Goods`
            where docstatus=0 and workflow_state='CS Pending Approval'
            {cust_cond} {date_cond_disp}
            """,
            params,
            as_dict=True,
        )

    data.sort(key=lambda r: (r.get("dt") or "", r.get("txn_type") or "", r.get("docname") or ""))
    return columns, data
