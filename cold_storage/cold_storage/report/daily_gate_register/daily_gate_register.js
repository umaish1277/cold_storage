frappe.query_reports["Daily Gate Register"] = {
  filters: [
    { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" }
  ]
};
