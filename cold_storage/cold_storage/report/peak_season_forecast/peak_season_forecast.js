frappe.query_reports["Peak Season Forecast"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname == "status") {
            if (value == "Peak") {
                value = `<span style="color:white; background-color:#e74c3c; padding:2px 6px; border-radius:4px; font-weight:bold;">${value}</span>`;
            } else if (value == "High") {
                value = `<span style="color:white; background-color:#f39c12; padding:2px 6px; border-radius:4px;">${value}</span>`;
            } else if (value == "Medium") {
                value = `<span style="color:white; background-color:#3498db; padding:2px 6px; border-radius:4px;">${value}</span>`;
            } else {
                value = `<span style="color:gray;">${value}</span>`;
            }
        }

        return value;
    }
};
