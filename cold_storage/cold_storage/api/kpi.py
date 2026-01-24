from __future__ import annotations
import frappe

@frappe.whitelist()
def pending_approvals_count() -> int:
    recv = frappe.db.count("Cold Storage Receive Goods", filters={"docstatus": 0, "workflow_state": "CS Pending Approval"}) or 0
    disp = frappe.db.count("Cold Storage Dispatch Goods", filters={"docstatus": 0, "workflow_state": "CS Pending Approval"}) or 0
    return int(recv) + int(disp)
