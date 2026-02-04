import frappe
import json
import os

def sync_workspace():
    workspace_name = 'Cold Storage'
    # Use direct path to be sure
    path = '/home/frappe/frappe-bench/apps/cold_storage/cold_storage/cold_storage/workspace/cold_storage/cold_storage.json'
    
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    # Use SQL to be absolutely sure we set the exact string from the JSON file
    # The JSON 'content' is already a stringified JSON array
    content_str = data.get('content')
    
    # Verify JSON validity before saving
    try:
        json.loads(content_str)
        print("Content JSON is valid.")
    except Exception as e:
        print(f"Content JSON is INVALID: {e}")
        return

    # Update using database API which handles escaping
    frappe.db.set_value('Workspace', workspace_name, 'content', content_str)
    
    # Also sync charts child table
    frappe.db.delete('Workspace Chart', {'parent': workspace_name})
    for chart in data.get('charts', []):
        chart_doc = frappe.get_doc({
            'doctype': 'Workspace Chart',
            'parent': workspace_name,
            'parenttype': 'Workspace',
            'parentfield': 'charts',
            'chart_name': chart.get('chart_name'),
            'label': chart.get('label')
        })
        chart_doc.insert()
        
    frappe.db.commit()
    print(f"Successfully synced Workspace: {workspace_name}")

sync_workspace()
