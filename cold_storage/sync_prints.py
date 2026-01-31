import frappe
import json
import os

def sync_print_formats():
    apps_path = frappe.get_app_path("cold_storage")
    # Path to the specific json files
    # apps_path already includes the inner 'cold_storage'
    receipt_json = os.path.join(apps_path, "print_format", "modern_receipt", "modern_receipt.json")
    dispatch_json = os.path.join(apps_path, "print_format", "modern_dispatch", "modern_dispatch.json")
    
    files = [receipt_json, dispatch_json]
    
    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = json.load(f)
                
                doc_name = content.get("name")
                if not frappe.db.exists("Print Format", doc_name):
                    print(f"Inserting {doc_name}...")
                    doc = frappe.get_doc(content)
                    doc.insert()
                    print(f"Inserted {doc_name}")
                else:
                    print(f"Updating {doc_name}...")
                    doc = frappe.get_doc("Print Format", doc_name)
                    doc.update(content)
                    doc.save()
                    print(f"Updated {doc_name}")
        else:
            print(f"File not found: {file_path}")

    frappe.db.commit()

sync_print_formats()
