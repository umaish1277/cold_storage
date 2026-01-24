from __future__ import annotations
import frappe
from frappe.utils import getdate, add_days

def _bucket_starts(from_date, to_date, bucket: str):
    cur = getdate(from_date)
    end = getdate(to_date)
    out = []
    if bucket == "Weekly":
        while cur <= end:
            out.append(cur)
            cur = add_days(cur, 7)
    else:
        y, m = cur.year, cur.month
        cur = getdate(f"{y}-{m:02d}-01")
        while cur <= end:
            out.append(cur)
            if m == 12:
                y += 1; m = 1
            else:
                m += 1
            cur = getdate(f"{y}-{m:02d}-01")
    return out

def execute(filters=None):
    filters = filters or {}
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    bucket = filters.get("bucket") or "Monthly"
    chamber = filters.get("chamber")

    columns = [
        {"label": "Period Start", "fieldname": "period_start", "fieldtype": "Date", "width": 110},
        {"label": "Chamber", "fieldname": "chamber", "fieldtype": "Link", "options": "Cold Storage Chamber", "width": 220},
        {"label": "Jute (Nos)", "fieldname": "jute", "fieldtype": "Int", "width": 120},
        {"label": "Net (Nos)", "fieldname": "net", "fieldtype": "Int", "width": 120},
        {"label": "JEB", "fieldname": "jeb", "fieldtype": "Float", "width": 120},
    ]

    periods = _bucket_starts(from_date, to_date, bucket)
    data = []
    for p in periods:
        if bucket == "Weekly":
            snap = min(add_days(p, 6), to_date)
        else:
            tmp = add_days(getdate(f"{p.year}-{p.month:02d}-28"), 4)
            snap = add_days(getdate(f"{tmp.year}-{tmp.month:02d}-01"), -1)
            if snap > to_date:
                snap = to_date

        params = {"snap": snap}
        ch_cond = ""
        if chamber:
            ch_cond = " and chamber=%(chamber)s"
            params["chamber"] = chamber

        rows = frappe.db.sql(
            f"""
            select chamber,
                   coalesce(sum(jute_in - jute_out),0) as jute,
                   coalesce(sum(net_in - net_out),0) as net
            from `tabStorage Batch`
            where docstatus=1
              and in_date <= %(snap)s
              and (out_date is null or out_date >= %(snap)s)
              {ch_cond}
            group by chamber
            order by chamber
            """,
            params,
            as_dict=True,
        )
        for r in rows:
            jeb = float(r["jute"] or 0) + (float(r["net"] or 0) / 2.0)
            data.append({"period_start": p, "chamber": r["chamber"], "jute": int(r["jute"] or 0), "net": int(r["net"] or 0), "jeb": jeb})

    return columns, data
