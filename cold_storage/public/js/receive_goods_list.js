frappe.listview_settings["Cold Storage Receive Goods"] = {
  onload(listview) {
    listview.page.add_action_item(__("Bulk Approve"), () => {
      const names = listview.get_checked_items(true);
      if (!names.length) return frappe.msgprint(__("Please select at least one document."));
      frappe.confirm(__("Approve {0} selected Receive Goods documents?", [names.length]), () => {
        frappe.call({
          method: "cold_storage.cold_storage.api.bulk_approve.bulk_approve",
          args: { doctype: "Cold Storage Receive Goods", names },
          freeze: true,
          callback: () => listview.refresh(),
        });
      });
    });

    listview.page.add_action_item(__("Bulk Reject"), () => {
      const names = listview.get_checked_items(true);
      if (!names.length) return frappe.msgprint(__("Please select at least one document."));
      frappe.prompt([{ fieldname: "reason", label: __("Rejection Reason"), fieldtype: "Small Text", reqd: 1 }], (values) => {
        frappe.confirm(__("Reject {0} selected Receive Goods documents?", [names.length]), () => {
          frappe.call({
            method: "cold_storage.cold_storage.api.bulk_approve.bulk_reject",
            args: { doctype: "Cold Storage Receive Goods", names, reason: values.reason },
            freeze: true,
            callback: () => listview.refresh(),
          });
        });
      }, __("Bulk Reject"), __("Reject"));
    });
  },
};
