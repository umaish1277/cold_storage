frappe.query_reports["Audit Trail"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "ref_doctype",
            "label": __("Ref DocType"),
            "fieldtype": "Link",
            "options": "DocType",
            "get_query": function () {
                return {
                    filters: {
                        "module": "Cold Storage",
                        "istable": 0
                    }
                };
            }
        },
        {
            "fieldname": "owner",
            "label": __("User"),
            "fieldtype": "Link",
            "options": "User"
        }
    ]
};
