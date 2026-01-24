frappe.query_reports["Bag Movement Register"] = {
  filters: [
    { fieldname: "from_date", label: "From Date", fieldtype: "Date" },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date" },
    { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" },
    { fieldname: "bag_type", label: "Bag Type", fieldtype: "Select", options: ["", "Jute", "Net"] }
  ]
};
