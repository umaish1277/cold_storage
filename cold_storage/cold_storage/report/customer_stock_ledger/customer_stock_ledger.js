frappe.query_reports["Customer Stock Ledger"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 0
        },
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
            "fieldtype": "Link",
            "options": "Batch",
            "get_query": function () {
                var customer = frappe.query_report.get_filter_value("customer");
                return {
                    query: "cold_storage.get_customer_items_query.get_customer_batches",
                    filters: { customer: customer }
                };
            },
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
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "get_query": function () {
                return {
                    query: "cold_storage.cold_storage.utils.get_item_group_filter"
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
