import frappe

@frappe.whitelist()
def run_update():
    sidebar_name = "Cold Storage"
    doc = frappe.get_doc("Workspace Sidebar", sidebar_name)

    # Clear existing items
    doc.items = []

    # Add items
    # We will use the workspace name 'Cold Storage' or 'cold-storage'
    ws_name = "Cold Storage"
    if not frappe.db.exists("Workspace", ws_name):
        ws_name = "cold-storage"

    links = [
        ("Home", "Link", "Workspace", ws_name),
        ("📋 Transactions", "Section Break", None, None),
        ("Receipt", "Link", "DocType", "Cold Storage Receipt"),
        ("Dispatch", "Link", "DocType", "Cold Storage Dispatch"),
        ("⚙️ Setup & Settings", "Section Break", None, None),
        ("Cold Storage Settings", "Link", "DocType", "Cold Storage Settings"),
        ("Rate Card", "Link", "DocType", "Cold Storage Rate Card"),
        ("Season", "Link", "DocType", "Cold Storage Season"),
        ("Customer Tier", "Link", "DocType", "Cold Storage Customer Tier"),
        ("WhatsApp Settings", "Link", "DocType", "Cold Storage WhatsApp Settings"),
        ("📊 Reports", "Section Break", None, None),
        ("Customer Stock Ledger", "Link", "Report", "Customer Stock Ledger")
    ]

    for label, type, link_type, link_to in links:
        doc.append("items", {
            "label": label,
            "type": type,
            "link_type": link_type,
            "link_to": link_to
        })

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return "Sidebar Updated Successfully"

@frappe.whitelist()
def force_fix_everything():
    # 1. Standardize Workspace
    ws_name = "Cold Storage"
    if frappe.db.exists("Workspace", ws_name):
        ws = frappe.get_doc("Workspace", ws_name)
        ws.public = 1
        ws.is_hidden = 0
        ws.app = "cold_storage"
        ws.module = "Cold Storage"
        if "is_standard" in [f.fieldname for f in ws.meta.fields]:
            ws.is_standard = 1
        ws.db_update()
        print("Workspace standardized")

    # 2. Standardize Workspace Sidebar
    sidebar_name = "Cold Storage"
    if frappe.db.exists("Workspace Sidebar", sidebar_name):
        sidebar = frappe.get_doc("Workspace Sidebar", sidebar_name)
        sidebar.standard = 1
        sidebar.app = "cold_storage"
        sidebar.db_update()
        print("Sidebar standardized")

    frappe.db.commit()
    
    # 3. Re-run sidebar update
    run_update()
    
    return "Everything Fixed and Standardized"

@frappe.whitelist()
def rename_to_hyphenated():
    if frappe.db.exists("Workspace", "Cold Storage"):
        frappe.rename_doc("Workspace", "Cold Storage", "cold-storage", force=True)
        frappe.db.commit()
        return "Renamed to cold-storage"
    return "Already renamed or not found"
