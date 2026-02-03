import frappe

@frappe.whitelist()
def get_pending_approvals():
    if "Cold Storage Manager" not in frappe.get_roles():
        return []

    # Check Receipts and Dispatches in "Pending Approval" state
    # We can query based on workflow_state field
    
    pending = []
    
    # Receipts
    receipts_count = frappe.db.count("Cold Storage Receipt", {"workflow_state": "Pending Approval"})
    if receipts_count > 0:
        url = "/app/cold-storage-receipt?workflow_state=Pending%20Approval"
        pending.append(f'{receipts_count} Receipts <a href="{url}" class="btn btn-xs btn-primary" style="margin-left: 5px;">View</a>')
        
    # Dispatches
    dispatches_count = frappe.db.count("Cold Storage Dispatch", {"workflow_state": "Pending Approval"})
    if dispatches_count > 0:
        url = "/app/cold-storage-dispatch?workflow_state=Pending%20Approval"
        pending.append(f'{dispatches_count} Dispatches <a href="{url}" class="btn btn-xs btn-primary" style="margin-left: 5px;">View</a>')
        
    return pending
