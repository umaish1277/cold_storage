frappe.query_reports["My Pending Cold Storage Approvals"] = {
  filters: [
    { fieldname: "from_date", label: "From Date", fieldtype: "Date" },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date" },
    { fieldname: "txn_type", label: "Type", fieldtype: "Select", options: ["", "Receive", "Dispatch"] },
    { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" }
  ]
};
