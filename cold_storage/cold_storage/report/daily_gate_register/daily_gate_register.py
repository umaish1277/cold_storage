from __future__ import annotations
import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    customer = filters.get("customer")

    columns = [
        {"label": "Date/Time", "fieldname": "dt", "fieldtype": "Datetime", "width": 160},
        {"label": "Type", "fieldname": "txn_type", "fieldtype": "Data", "width": 90},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 220},
        {"label": "Contract", "fieldname": "contract", "fieldtype": "Link", "options": "Storage Contract", "width": 160},
        {"label": "Storage Batch", "fieldname": "storage_batch", "fieldtype": "Link", "options": "Storage Batch", "width": 160},
        {"label": "ERP Batch", "fieldname": "batch", "fieldtype": "Link", "options": "Batch", "width": 130},
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 80},
        {"label": "Chamber", "fieldname": "chamber", "fieldtype": "Link", "options": "Cold Storage Chamber", "width": 140},
        {"label": "Jute", "fieldname": "jute", "fieldtype": "Int", "width": 70},
        {"label": "Net", "fieldname": "net", "fieldtype": "Int", "width": 70},
        {"label": "JEB", "fieldname": "jeb", "fieldtype": "Float", "width": 80},
        {"label": "Reference/Vehicle", "fieldname": "reference", "fieldtype": "Data", "width": 160},
        {"label": "Document", "fieldname": "docname", "fieldtype": "Dynamic Link", "options": "doctype_name", "width": 170},
        {"label": "doctype_name", "fieldname": "doctype_name", "fieldtype": "Data", "hidden": 1},
    ]

    params = {"from": f"{from_date} 00:00:00", "to": f"{to_date} 23:59:59"}
    cust_cond = ""
    if customer:
        cust_cond = " and customer=%(customer)s"
        params["customer"] = customer

    recv = frappe.db.sql(
        f"""
        select
            receiving_datetime as dt,
            'Receive' as txn_type,
            customer,
            contract,
            generated_storage_batch as storage_batch,
            batch,
            item,
            qty_stored as qty,
            chamber,
            coalesce(total_jute_bags,0) as jute,
            coalesce(total_net_bags,0) as net,
            reference,
            name as docname,
            'Cold Storage Receive Goods' as doctype_name
        from `tabCold Storage Receive Goods`
        where docstatus=1
          and receiving_datetime between %(from)s and %(to)s
          {cust_cond}
        """,
        params,
        as_dict=True,
    )

    disp = frappe.db.sql(
        f"""
        select
            dg.dispatch_datetime as dt,
            'Dispatch' as txn_type,
            dg.customer,
            dg.contract,
            dg.storage_batch,
            dg.batch,
            dg.item,
            dg.qty_dispatch as qty,
            dg.chamber,
            coalesce(sum(case when bml.bag_type='Jute' then bml.qty else 0 end),0) as jute,
            coalesce(sum(case when bml.bag_type='Net' then bml.qty else 0 end),0) as net,
            dg.reference,
            dg.name as docname,
            'Cold Storage Dispatch Goods' as doctype_name
        from `tabCold Storage Dispatch Goods` dg
        left join `tabBag Movement Line` bml
            on bml.parent = dg.name
            and bml.parenttype = 'Cold Storage Dispatch Goods'
            and bml.parentfield = 'bags'
        where dg.docstatus=1
          and dg.dispatch_datetime between %(from)s and %(to)s
          {cust_cond}
        group by
            dg.name, dg.dispatch_datetime, dg.customer, dg.contract, dg.storage_batch,
            dg.batch, dg.item, dg.qty_dispatch, dg.chamber, dg.reference
        """,
        params,
        as_dict=True,
    )

    rows = recv + disp
    for r in rows:
        j = int(r.get("jute") or 0)
        n = int(r.get("net") or 0)
        r["jeb"] = float(j) + (float(n) / 2.0)

    rows.sort(key=lambda x: x.get("dt"))
    return columns, rows
