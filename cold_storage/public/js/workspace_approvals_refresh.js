(function () {
  const REFRESH_MS = 30000;

  function on_workspace() {
    const route = frappe.get_route();
    return route && route[0] === "Workspaces" && (route[1] || "").startsWith("Cold Storage");
  }

  function refresh_workspace() {
    try {
      if (!on_workspace()) return;
      if (frappe.workspace && frappe.workspace.current_workspace) {
        frappe.workspace.current_workspace.reload();
      }
    } catch (e) {}
  }

  frappe.router.on("change", () => refresh_workspace());
  setInterval(() => refresh_workspace(), REFRESH_MS);
})();
