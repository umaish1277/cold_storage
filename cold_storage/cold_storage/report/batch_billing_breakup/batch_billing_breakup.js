frappe.query_reports["Batch Billing Breakup"] = {
  filters: [
    { fieldname: "contract", label: "Contract", fieldtype: "Link", options: "Storage Contract", reqd: 1 },
    { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "chamber", label: "Chamber", fieldtype: "Link", options: "Cold Storage Chamber" }
  ]
};
