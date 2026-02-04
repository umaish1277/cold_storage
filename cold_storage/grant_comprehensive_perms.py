import frappe

def execute():
    role = "Cold Storage Manager"
    
    # 1. Update DocType Permissions
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
        
        perm.save(ignore_permissions=True)
        print(f"Set permissions for {dt}")

    # 2. Update Report Permissions
    reports = ["Customer Stock Ledger"]
    for report_name in reports:
        if frappe.db.exists("Report", report_name):
            report = frappe.get_doc("Report", report_name)
            # Check if role already exists in Has Role child table
            found = False
            for r in report.roles:
                if r.role == role:
                    found = True
                    break
            
            if not found:
                report.append("roles", {"role": role})
                report.save(ignore_permissions=True)
                print(f"Set permissions for Report: {report_name}")

    frappe.db.commit()
    print("Done!")
