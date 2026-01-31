frappe.query_reports["Customer Stock Ledger"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 0
        },
        {
            "fieldname": "batch_no",
            "label": __("Batch No"),
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "item_code",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item",
            "reqd": 0
        },
        {
            "fieldname": "show_zero_balance",
            "label": __("Show Zero Balance"),
            "fieldtype": "Check",
            "default": 0
        }
    ]
};
