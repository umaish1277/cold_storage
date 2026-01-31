
frappe.ui.form.on('Cold Storage Receipt', {
    refresh: function (frm) {
        // Inject Custom CSS to resize QR Code image in form view
        // Targeting the specific field wrapper
        const css = `
            div[data-fieldname="qr_code"] .attached-file img {
                width: 150px !important;
                height: 150px !important;
                max-width: none !important;
                max-height: none !important;
                margin-bottom: 10px;
            }
            div[data-fieldname="qr_code"] .attached-file {
                height: auto !important;
            }
        `;

        $("<style>").prop("type", "text/css").html(css).appendTo("head");
    }
});
