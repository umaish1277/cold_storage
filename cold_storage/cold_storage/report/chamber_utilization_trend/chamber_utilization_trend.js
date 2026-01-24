frappe.query_reports["Chamber Utilization Trend"] = {
  filters: [
    { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "to_date", label: "To Date", fieldtype: "Date", reqd: 1 },
    { fieldname: "bucket", label: "Bucket", fieldtype: "Select", options: ["Weekly", "Monthly"], default: "Monthly" },
    { fieldname: "chamber", label: "Chamber", fieldtype: "Link", options: "Cold Storage Chamber" }
  ]
};
