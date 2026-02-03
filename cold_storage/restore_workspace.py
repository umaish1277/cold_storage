import frappe
import json
import os

def restore_workspace():
    with open('/home/frappe/frappe-bench/restore_log.txt', 'a') as log:
        log.write("Restore script started\n")
    workspace_name = 'Cold Storage'
    print(f"Starting restoration for {workspace_name}...")
    
    # Delete existing records to clear any corruption/duplicates
    frappe.db.delete('Workspace', {'name': workspace_name})
    frappe.db.delete('Has Role', {'parent': workspace_name, 'parenttype': 'Workspace'})
    frappe.db.delete('Workspace Chart', {'parent': workspace_name})
    frappe.db.delete('Workspace Shortcut', {'parent': workspace_name})
    frappe.db.delete('Workspace Link', {'parent': workspace_name})
    frappe.db.delete('Workspace Quick List', {'parent': workspace_name})
    frappe.db.delete('Workspace Custom Block', {'parent': workspace_name})
    
    # Path to the JSON file
    path = '/home/frappe/frappe-bench/apps/cold_storage/cold_storage/cold_storage/workspace/cold_storage/cold_storage.json'
    
    if not os.path.exists(path):
        print(f"Error: JSON file not found at {path}")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    # Remove fields that shouldn't be in a new doc or causing issues
    for field in ['modified', 'modified_by', 'creation', 'owner']:
        if field in data:
            del data[field]
            
    # Ensure mandatory fields
    data['doctype'] = 'Workspace'
    data['name'] = workspace_name
    
    # Insert
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    
    frappe.db.commit()
    print(f"Successfully restored Workspace: {workspace_name}")
    
    # Double check visibility
    res = frappe.db.get_value('Workspace', workspace_name, ['public', 'is_hidden', 'label'], as_dict=True)
    print(f"Workspace Checks: {res}")

if __name__ == "__main__":
    restore_workspace()
