frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Warehouse Utilization"] = {
    method: "cold_storage.cold_storage.dashboard_chart_source.warehouse_utilization.warehouse_utilization.get",
    filters: [],
};
