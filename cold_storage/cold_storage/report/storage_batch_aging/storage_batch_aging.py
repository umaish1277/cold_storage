from __future__ import annotations
import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}
    as_on = getdate(filters.get("as_on_date"))
    customer = filters.get("customer")
    chamber = filters.get("chamber")

    columns = [
        {"label":"Storage Batch","fieldname":"name","fieldtype":"Link","options":"Storage Batch","width":160},
        {"label":"Customer","fieldname":"customer","fieldtype":"Link","options":"Customer","width":220},
        {"label":"Contract","fieldname":"contract","fieldtype":"Link","options":"Storage Contract","width":160},
        {"label":"Chamber","fieldname":"chamber","fieldtype":"Link","options":"Cold Storage Chamber","width":140},
        {"label":"In Date","fieldname":"in_date","fieldtype":"Datetime","width":150},
        {"label":"Days","fieldname":"days","fieldtype":"Int","width":80},
        {"label":"Jute Bal","fieldname":"jute","fieldtype":"Int","width":90},
        {"label":"Net Bal","fieldname":"net","fieldtype":"Int","width":90},
        {"label":"JEB","fieldname":"jeb","fieldtype":"Float","width":90},
    ]

    params = {"as_on": as_on}
    cond = " where docstatus=1 and in_date <= %(as_on)s and (out_date is null or out_date >= %(as_on)s)"
    if customer:
        cond += " and customer=%(customer)s"; params["customer"] = customer
    if chamber:
        cond += " and chamber=%(chamber)s"; params["chamber"] = chamber

    rows = frappe.db.sql(
        f"""
        select name, customer, contract, chamber, in_date,
               coalesce(jute_in,0)-coalesce(jute_out,0) as jute,
               coalesce(net_in,0)-coalesce(net_out,0) as net
        from `tabStorage Batch`
        {cond}
        order by in_date asc
        """,
        params,
        as_dict=True,
    )

    for r in rows:
        r["days"] = max((as_on - getdate(r["in_date"])).days, 0)
        r["jeb"] = float(r["jute"] or 0) + float(r["net"] or 0)/2.0

    return columns, rows
