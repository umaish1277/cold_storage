from __future__ import annotations
import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    customer = filters.get("customer")
    bag_type = filters.get("bag_type")

    columns = [
        {"label":"Posting","fieldname":"posting_datetime","fieldtype":"Datetime","width":160},
        {"label":"Customer","fieldname":"customer","fieldtype":"Link","options":"Customer","width":220},
        {"label":"Bag Type","fieldname":"bag_type","fieldtype":"Data","width":90},
        {"label":"In","fieldname":"in_qty","fieldtype":"Int","width":70},
        {"label":"Out","fieldname":"out_qty","fieldtype":"Int","width":70},
        {"label":"Voucher Type","fieldname":"voucher_type","fieldtype":"Data","width":140},
        {"label":"Voucher No","fieldname":"voucher_no","fieldtype":"Data","width":140},
        {"label":"Remarks","fieldname":"remarks","fieldtype":"Data","width":220},
    ]

    cond = " where 1=1"
    params = {}
    if from_date:
        cond += " and posting_datetime >= %(from)s"; params["from"] = f"{getdate(from_date)} 00:00:00"
    if to_date:
        cond += " and posting_datetime <= %(to)s"; params["to"] = f"{getdate(to_date)} 23:59:59"
    if customer:
        cond += " and customer=%(customer)s"; params["customer"] = customer
    if bag_type:
        cond += " and bag_type=%(bag_type)s"; params["bag_type"] = bag_type

    rows = frappe.db.sql(
        f"""select posting_datetime, customer, bag_type, in_qty, out_qty, voucher_type, voucher_no, remarks
              from `tabCustomer Bag Ledger Entry` {cond}
              order by posting_datetime desc""",
        params,
        as_dict=True,
    )
    return columns, rows
