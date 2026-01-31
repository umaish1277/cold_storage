import frappe

def debug_print_formats():
    formats = ["Modern Receipt", "Modern Dispatch"]
    for pf_name in formats:
        if frappe.db.exists("Print Format", pf_name):
            doc = frappe.get_doc("Print Format", pf_name)
            print(f"--- {pf_name} ---")
            print(f"Module: {doc.module}")
            print(f"DocType: {doc.doc_type}")
            print(f"Standard: {doc.standard}")
            print(f"Custom Format: {doc.custom_format}")
            print(f"Print Format Type: {doc.print_format_type}")
            print(f"Disabled: {doc.disabled}")
            # print(f"Raw CSS: {doc.css[:50]}...") 
        else:
            print(f"--- {pf_name} NOT FOUND ---")

debug_print_formats()
