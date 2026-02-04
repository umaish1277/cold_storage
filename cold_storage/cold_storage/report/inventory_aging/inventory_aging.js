// Copyright (c) 2026, Cold Storage and contributors
// For license information, please see license.txt

frappe.query_reports["Inventory Aging"] = {
    "filters": [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "item",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "threshold_days",
            "label": __("Alert Threshold (Days)"),
            "fieldtype": "Int",
            "default": 30,
            "description": "Stock older than this will be marked as Overdue"
        },
        {
            "fieldname": "min_age_days",
            "label": __("Min Age (Days)"),
            "fieldtype": "Int",
            "default": 0
        },
        {
            "fieldname": "max_age_days",
            "label": __("Max Age (Days)"),
            "fieldtype": "Int"
        },
        {
            "fieldname": "show_zero_balance",
            "label": __("Show Zero Balance"),
            "fieldtype": "Check",
            "default": 0
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "status") {
            if (data && data.status) {
                if (data.status.includes("Overdue")) {
                    value = `<span style="color: #e74c3c; font-weight: bold;">${value}</span>`;
                } else if (data.status.includes("Warning")) {
                    value = `<span style="color: #f39c12; font-weight: bold;">${value}</span>`;
                } else {
                    value = `<span style="color: #27ae60;">${value}</span>`;
                }
            }
        }

        if (column.fieldname === "age_days" && data) {
            let threshold = frappe.query_report.get_filter_value("threshold_days") || 30;
            if (data.age_days > threshold) {
                value = `<span style="color: #e74c3c; font-weight: bold;">${value}</span>`;
            } else if (data.age_days > threshold * 0.8) {
                value = `<span style="color: #f39c12; font-weight: bold;">${value}</span>`;
            }
        }

        if (column.fieldname === "age_bucket" && data) {
            if (data.age_bucket === "90+ days") {
                value = `<span style="background: #ffebee; padding: 2px 6px; border-radius: 3px; color: #c0392b;">${value}</span>`;
            } else if (data.age_bucket === "61-90 days") {
                value = `<span style="background: #fff3e0; padding: 2px 6px; border-radius: 3px; color: #e67e22;">${value}</span>`;
            }
        }

        return value;
    }
};
