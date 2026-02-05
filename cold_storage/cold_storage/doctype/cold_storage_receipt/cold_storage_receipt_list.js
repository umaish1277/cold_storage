frappe.listview_settings['Cold Storage Receipt'] = {
    onload: function (listview) {
        listview.page.add_inner_button(__("Bulk Print"), function () {
            const selected = listview.get_checked_items();
            if (selected.length === 0) {
                frappe.msgprint(__("Please select at least one receipt to print."));
                return;
            }

            new frappe.ui.BulkOperations({
                doctype: listview.doctype
            }).print(selected);
        });
    }
};
