import frappe
import json
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "creation",
            "fieldtype": "Datetime",
            "width": 160
        },
        {
            "label": _("User"),
            "fieldname": "owner",
            "fieldtype": "Link",
            "options": "User",
            "width": 120
        },
        {
            "label": _("DocType"),
            "fieldname": "ref_doctype",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 150
        },
        {
            "label": _("Document"),
            "fieldname": "docname",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "label": _("Field"),
            "fieldname": "field",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Old Value"),
            "fieldname": "old_value",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("New Value"),
            "fieldname": "new_value",
            "fieldtype": "Data",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = []
    if filters.get("from_date"):
        conditions.append(["creation", ">=", filters.get("from_date")])
    if filters.get("to_date"):
        conditions.append(["creation", "<=", filters.get("to_date")])
    if filters.get("ref_doctype"):
        conditions.append(["ref_doctype", "=", filters.get("ref_doctype")])
    if filters.get("owner"):
        conditions.append(["owner", "=", filters.get("owner")])

    versions = frappe.get_all("Version",
        fields=["creation", "owner", "ref_doctype", "docname", "data"],
        filters=conditions,
        order_by="creation desc"
    )

    report_data = []
    for v in versions:
        if not v.data:
            continue
            
        try:
            audit_data = json.loads(v.data)
        except:
            continue

        # Changed Fields
        if audit_data.get("changed"):
            for row in audit_data.get("changed"):
                if len(row) >= 3:
                    field, old, new = row[0], row[1], row[2]
                    # Skip internal/empty changes if necessary
                    report_data.append({
                        "creation": v.creation,
                        "owner": v.owner,
                        "ref_doctype": v.ref_doctype,
                        "docname": v.docname,
                        "field": frappe.unscrub(field),
                        "old_value": old,
                        "new_value": new
                    })
        
        # New Documents (Creation)
        if not audit_data.get("changed") and not audit_data.get("row_changed"):
             report_data.append({
                "creation": v.creation,
                "owner": v.owner,
                "ref_doctype": v.ref_doctype,
                "docname": v.docname,
                "field": "Status",
                "old_value": "",
                "new_value": "Created"
            })

    return report_data
