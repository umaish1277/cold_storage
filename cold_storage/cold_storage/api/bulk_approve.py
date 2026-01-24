from __future__ import annotations
import frappe

ALLOWED_ROLES = ("Cold Storage Supervisor", "Cold Storage Manager", "System Manager")

def _has_permission() -> bool:
    return any(frappe.has_role(r) for r in ALLOWED_ROLES)

@frappe.whitelist()
def bulk_approve(doctype: str, names: list[str]) -> dict:
    if not _has_permission():
        frappe.throw("You are not allowed to bulk approve these documents.")
    if doctype not in ("Cold Storage Receive Goods", "Cold Storage Dispatch Goods"):
        frappe.throw("Invalid DocType for bulk approval.")

    approved, skipped = [], []
    for name in names:
        try:
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus != 0 or doc.workflow_state != "CS Pending Approval":
                skipped.append({"name": name, "reason": "Not pending approval"})
                continue
            doc.apply_workflow("Approve")
            approved.append(name)
        except Exception as e:
            skipped.append({"name": name, "reason": str(e)})

    return {"approved": approved, "skipped": skipped, "approved_count": len(approved), "skipped_count": len(skipped)}

@frappe.whitelist()
def bulk_reject(doctype: str, names: list[str], reason: str | None = None) -> dict:
    if not _has_permission():
        frappe.throw("You are not allowed to bulk reject these documents.")
    if doctype not in ("Cold Storage Receive Goods", "Cold Storage Dispatch Goods"):
        frappe.throw("Invalid DocType for bulk rejection.")

    reason = (reason or "").strip()
    rejected, skipped = [], []
    for name in names:
        try:
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus != 0 or doc.workflow_state != "CS Pending Approval":
                skipped.append({"name": name, "reason": "Not pending approval"})
                continue
            if reason:
                doc.add_comment("Comment", f"Rejected in bulk. Reason: {reason}")
                if hasattr(doc, "rejection_reason"):
                    doc.rejection_reason = reason
            doc.apply_workflow("Reject")
            rejected.append(name)
        except Exception as e:
            skipped.append({"name": name, "reason": str(e)})

    return {"rejected": rejected, "skipped": skipped, "rejected_count": len(rejected), "skipped_count": len(skipped)}
