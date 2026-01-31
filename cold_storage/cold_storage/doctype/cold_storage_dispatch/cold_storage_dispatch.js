frappe.ui.form.on('Cold Storage Dispatch Item', {
    bag_type: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.bag_type) {
            frappe.call({
                method: 'cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_bag_rate',
                args: {
                    bag_type: row.bag_type
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'rate', r.message);
                    } else {
                        frappe.model.set_value(cdt, cdn, 'rate', 0);
                    }
                }
            });
        }
    },

    rate: function (frm, cdt, cdn) {
        // Auto-calculate Item Amount when rate changes
        var row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.rate * row.number_of_bags);
    },

    number_of_bags: function (frm, cdt, cdn) {
        // Auto-calculate Item Amount when qty changes
        var row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.rate * row.number_of_bags);
    }
});

frappe.ui.form.on('Cold Storage Dispatch', {
    refresh: function (frm) {

    }
});
