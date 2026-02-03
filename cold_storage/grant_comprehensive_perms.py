import frappe

def execute():
    role = "Cold Storage Manager"
    doctypes = [
        "Stock Ledger Entry",
        "GL Entry",
        "Serial and Batch Bundle",
        "Stock Entry Detail",
        "Sales Invoice Item",
        "Batch",
        "Stock Entry",
        "Sales Invoice",
        "Stock Settings"
    ]
    
    for dt in doctypes:
        existing = frappe.db.get_value("Custom DocPerm", {"parent": dt, "role": role}, "name")
        if existing:
            perm = frappe.get_doc("Custom DocPerm", existing)
        else:
            perm = frappe.new_doc("Custom DocPerm")
            perm.parent = dt
            perm.parenttype = "DocType"
            perm.parentfield = "permissions"
            perm.role = role
        
        perm.read = 1
        perm.write = 1
        perm.create = 1
        perm.select = 1
        
        if dt in ["Stock Entry", "Sales Invoice", "Serial and Batch Bundle"]:
            perm.submit = 1
            perm.cancel = 1
            perm.amend = 1
            perm.delete = 1
        
        # Ensure only read for Stock Settings if needed, but the loop sets all basic ones.
        # Most managers need read/write for settings if they are "Managers".
        
        perm.save(ignore_permissions=True)
        print(f"Set permissions for {dt}")

    frappe.db.commit()
    print("Done!")
