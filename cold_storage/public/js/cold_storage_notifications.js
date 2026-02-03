
$(document).on('app_ready', function () {
    if (frappe.user.has_role("Cold Storage Manager")) {
        frappe.call({
            method: "cold_storage.cold_storage.notifications.get_pending_approvals",
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    frappe.msgprint({
                        title: __('Pending Approvals'),
                        message: __('You have pending approvals:<br>') + r.message.join('<br>'),
                        indicator: 'orange'
                    });
                }
            }
        });
    }
});
