frappe.query_reports["Storage Batch Aging"] = {
  filters: [
    { fieldname: "as_on_date", label: "As On Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" },
    { fieldname: "chamber", label: "Chamber", fieldtype: "Link", options: "Cold Storage Chamber" }
  ]
};
