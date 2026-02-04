import frappe

def fix(wf_name):
    if not frappe.db.exists("Workflow", wf_name):
        return
        
    # 1. Ensure "Cancelled" Workflow State exists in master
    if not frappe.db.exists("Workflow State", "Cancelled"):
        frappe.get_doc({
            "doctype": "Workflow State",
            "workflow_state_name": "Cancelled",
            "style": "Danger" # Red for cancelled
        }).insert()
        print("Created 'Cancelled' Workflow State")

    # 2. Ensure "Cancel" Workflow Action exists in master
    if not frappe.db.exists("Workflow Action Master", "Cancel"):
        # Note: In recent Frappe versions it might be 'Workflow Action' or 'Workflow Action Master'
        # based on metadata. Let's check common names.
        try:
            frappe.get_doc({
                "doctype": "Workflow Action Master",
                "workflow_action_name": "Cancel"
            }).insert()
            print("Created 'Cancel' Workflow Action Master")
        except frappe.DoesNotExistError:
            pass # Try another if this fails
    
    wf = frappe.get_doc("Workflow", wf_name)
    states = [s.state for s in wf.states]
    if "Cancelled" not in states:
        wf.append("states", {"state": "Cancelled", "doc_status": "2", "allow_edit": "Cold Storage Manager"})
        wf.save()
        print(f"Added 'Cancelled' state to {wf_name}")
        wf = frappe.get_doc("Workflow", wf_name)
    
    transitions = [(t.state, t.action) for t in wf.transitions]
    if ("Approved", "Cancel") not in transitions:
        wf.append("transitions", {
            "state": "Approved",
            "action": "Cancel",
            "next_state": "Cancelled",
            "allowed": "Cold Storage Manager"
        })
        wf.save()
        print(f"Added 'Cancel' transition to {wf_name}")

def fix_all():
    fix("Cold Storage Receipt Approval")
    fix("Cold Storage Dispatch Approval")
    frappe.db.commit()
    print("Done")

if __name__ == "__main__":
    fix_all()
