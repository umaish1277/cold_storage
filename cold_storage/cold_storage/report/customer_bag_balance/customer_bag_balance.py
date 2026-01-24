from __future__ import annotations
import frappe

def execute(filters=None):
    filters = filters or {}
    customer = filters.get("customer")

    columns = [
        {"label":"Customer","fieldname":"customer","fieldtype":"Link","options":"Customer","width":220},
        {"label":"Bag Type","fieldname":"bag_type","fieldtype":"Data","width":120},
        {"label":"In","fieldname":"in_qty","fieldtype":"Int","width":90},
        {"label":"Out","fieldname":"out_qty","fieldtype":"Int","width":90},
        {"label":"Balance","fieldname":"balance","fieldtype":"Int","width":100},
        {"label":"JEB Balance","fieldname":"jeb_balance","fieldtype":"Float","width":110},
    ]

    params = {}
    cond = ""
    if customer:
        cond = " where customer=%(customer)s"
        params["customer"] = customer

    rows = frappe.db.sql(
        f"""
        select customer, bag_type,
               coalesce(sum(in_qty),0) as in_qty,
               coalesce(sum(out_qty),0) as out_qty
        from `tabCustomer Bag Ledger Entry`
        {cond}
        group by customer, bag_type
        order by customer, bag_type
        """,
        params,
        as_dict=True,
    )

    by_cust = {}
    data = []
    for r in rows:
        bal = int(r["in_qty"] or 0) - int(r["out_qty"] or 0)
        r["balance"] = bal
        data.append(r)
        by_cust.setdefault(r["customer"], {"Jute": 0, "Net": 0})
        by_cust[r["customer"]][r["bag_type"]] = bal

    for r in data:
        b = by_cust.get(r["customer"], {"Jute": 0, "Net": 0})
        r["jeb_balance"] = float(b.get("Jute", 0)) + float(b.get("Net", 0))/2.0

    return columns, data
