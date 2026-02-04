
frappe.query_reports["Storage Duration Analysis"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("Dispatch From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
        },
        {
            "fieldname": "to_date",
            "label": __("Dispatch To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        }
    ]
};
