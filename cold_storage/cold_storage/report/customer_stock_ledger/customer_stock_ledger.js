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
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "reqd": 0
        },
        {
            "fieldname": "bag_type",
            "label": __("Bag Type"),
            "fieldtype": "Link",
            "options": "Item",
            "get_query": function () {
                return {
                    query: "cold_storage.cold_storage.report.customer_stock_ledger.customer_stock_ledger.get_bag_type_filter"
                };
            },
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
