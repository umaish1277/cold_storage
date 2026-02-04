$(document).on('app_ready', function () {
    if (frappe.user.has_role("Cold Storage Manager")) {
        // v5: User-specific key for maximum reliability
        const DISMISS_KEY = 'cs_dismiss_v5_' + frappe.session.user;

        console.warn("Notification System v5 Active for:", frappe.session.user);

        // SMART CHECK: If we are already on a list view filtered for Pending Approval, SILENTLY DISMISS
        if (window.location.href.indexOf('workflow_state=Pending%20Approval') !== -1) {
            console.log("On Pending list view. Persisting dismissal.");
            localStorage.setItem(DISMISS_KEY, 'true');
            return;
        }

        // Only check if not already acknowledged
        if (localStorage.getItem(DISMISS_KEY) !== 'true') {
            frappe.call({
                method: "cold_storage.cold_storage.notifications.get_pending_approvals",
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        // Re-check just in case something changed during the call
                        if (localStorage.getItem(DISMISS_KEY) === 'true') return;

                        let msg_dialog = frappe.msgprint({
                            title: __('Pending Approvals'),
                            message: __('You have pending approvals:<br>') + r.message.join('<br>'),
                            indicator: 'orange'
                        });

                        // Global identifier for this dialog session
                        msg_dialog.$wrapper.addClass('pending-approvals-dialog');
                    }
                }
            });
        }
    }
});

// Global high-reliability listener
$(document).on('click', '.btn-view-approval', function () {
    const DISMISS_KEY = 'cs_dismiss_v5_' + frappe.session.user;
    console.log("Global 'View' click captured. Setting localStorage:", DISMISS_KEY);
    localStorage.setItem(DISMISS_KEY, 'true');

    // Attempt to close any open dialogs of this type immediately
    $('.pending-approvals-dialog .btn-modal-close, .pending-approvals-dialog .close').click();
});
