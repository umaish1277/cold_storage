from __future__ import annotations
import frappe

@frappe.whitelist()
def chamber_occupancy_jeb(filters=None):
    rows = frappe.db.sql(
        """
        select chamber,
               coalesce(sum(jute_in - jute_out),0) as jute,
               coalesce(sum(net_in - net_out),0) as net
        from `tabStorage Batch`
        where docstatus=1 and status='In Storage'
        group by chamber
        order by chamber
        """,
        as_dict=True,
    )
    labels, values = [], []
    for r in rows:
        labels.append(r.get("chamber") or "—")
        jeb = float(r.get("jute") or 0) + (float(r.get("net") or 0) / 2.0)
        values.append(jeb)
    return {"labels": labels, "datasets": [{"name": "JEB In Storage", "values": values}]}
