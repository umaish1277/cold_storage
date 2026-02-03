import frappe

def auto_request_approval(doc, method):
    # Ensure default state if missing (Draft)
    # workflow_state might be None immediately after insert if not set by controller yet
    if not doc.workflow_state:
        doc.workflow_state = "Draft"
        
    if doc.workflow_state == "Draft":
        try:
             from frappe.model.workflow import apply_workflow
             
             # Attempt to apply "Request Approval" action
             apply_workflow(doc, "Request Approval")
             
             # apply_workflow updates the doc state in memory.
             # We must persist this change to the database.
             # Using db_set avoids triggering recursive save/validate loops.
             doc.db_set("workflow_state", doc.workflow_state)
             
             # Also update status if mapped
             if hasattr(doc, "status"):
                 doc.db_set("status", doc.status)
                 
        except frappe.model.workflow.WorkflowStateError:
             # This happens if transition is not valid for the user/state
             # We log it but DON'T block the creation, or else user can't create at all.
             frappe.log_error("Auto Approval Workflow Mismatch", f"Doc: {doc.name}, State: {doc.workflow_state}, User: {frappe.session.user}")
        except Exception as e:
            frappe.log_error("Auto Approval Error", f"Failed for {doc.name}: {str(e)}")
