from __future__ import annotations
import frappe
from frappe.utils import now_datetime, getdate

def on_submit_create_docs(doc, method=None):
    sb = frappe.get_doc("Storage Batch", doc.storage_batch)

    # Bag Issue
    if frappe.db.exists("DocType", "Bag Issue"):
        bi = frappe.new_doc("Bag Issue")
        bi.customer = doc.customer
        bi.contract = doc.contract
        bi.posting_datetime = doc.dispatch_datetime or now_datetime()
        bi.reference = doc.reference
        bi.storage_batch = doc.storage_batch
        for r in (doc.get("bags") or []):
            bi.append("bags", {"bag_type": r.bag_type, "qty": r.qty})
        bi.insert(ignore_permissions=True)
        bi.submit()

    # Stock Entry (Material Issue)
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Issue"
    se.company = frappe.defaults.get_user_default("Company") or frappe.db.get_default("company")
    se.posting_date = getdate(doc.dispatch_datetime) if doc.dispatch_datetime else getdate(now_datetime())
    se.posting_time = (doc.dispatch_datetime or now_datetime()).strftime("%H:%M:%S")
    se.append("items", {
        "item_code": doc.item,
        "qty": doc.qty_dispatch,
        "uom": doc.uom or "Nos",
        "s_warehouse": doc.warehouse,
        "batch_no": doc.batch or sb.batch,
    })
    se.insert(ignore_permissions=True)
    se.submit()

    # Update Storage Batch bag balances + close when emptied
    jute_out = 0
    net_out = 0
    for r in (doc.get("bags") or []):
        if r.bag_type == "Jute":
            jute_out += int(r.qty or 0)
        elif r.bag_type == "Net":
            net_out += int(r.qty or 0)

    sb.db_set("jute_out", (sb.jute_out or 0) + jute_out)
    sb.db_set("net_out", (sb.net_out or 0) + net_out)

    jute_bal = (sb.jute_in or 0) - (sb.jute_out or 0)
    net_bal = (sb.net_in or 0) - (sb.net_out or 0)
    if jute_bal <= 0 and net_bal <= 0:
        sb.db_set("out_date", doc.dispatch_datetime or now_datetime())
        sb.db_set("status", "Dispatched")
