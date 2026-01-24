from __future__ import annotations
import frappe

def execute():
    fields = [
        dict(dt="Sales Invoice", fieldname="cold_storage_contract", label="Cold Storage Contract", fieldtype="Link",
             options="Storage Contract", insert_after="customer"),
        dict(dt="Sales Invoice", fieldname="cold_storage_period_start", label="Cold Storage Period Start",
             fieldtype="Date", insert_after="posting_date"),
        dict(dt="Sales Invoice", fieldname="cold_storage_period_end", label="Cold Storage Period End",
             fieldtype="Date", insert_after="cold_storage_period_start"),
    ]
    for f in fields:
        if frappe.db.exists("Custom Field", {"dt": f["dt"], "fieldname": f["fieldname"]}):
            continue
        frappe.get_doc({"doctype": "Custom Field", **f}).insert(ignore_permissions=True)
