frappe.pages["cold-storage-approvals"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("Cold Storage Approvals"), single_column: true });

  const $root = $(wrapper).find(".layout-main-section");
  $root.html(`
    <div class="cs-approvals">
      <div class="btn-group" style="margin-bottom:12px;">
        <button class="btn btn-default btn-recv active">${__("Receive")}</button>
        <button class="btn btn-default btn-disp">${__("Dispatch")}</button>
      </div>
      <div class="cs-list"></div>
    </div>
  `);

  let mode = "Receive";

  function render_cards(rows, doctype) {
    const $list = $root.find(".cs-list");
    if (!rows.length) return $list.html(`<div class="text-muted">${__("No pending approvals.")}</div>`);

    $list.html(rows.map((r) => `
      <div class="card" style="margin-bottom:10px;">
        <div class="card-body">
          <div style="display:flex; justify-content:space-between; gap:10px;">
            <div>
              <div style="font-weight:700;">
                <a href="/app/${frappe.router.slug(doctype)}/${r.name}">${r.name}</a>
              </div>
              <div class="text-muted" style="font-size:12px;">
                ${__("Customer")}: ${r.customer || ""}<br>
                ${__("Date/Time")}: ${r.dt || ""}<br>
                ${__("Reference")}: ${r.reference || ""}
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:8px; min-width:120px;">
              <button class="btn btn-primary btn-approve" data-name="${r.name}" data-doctype="${doctype}">${__("Approve")}</button>
              <button class="btn btn-default btn-reject" data-name="${r.name}" data-doctype="${doctype}">${__("Reject")}</button>
            </div>
          </div>
        </div>
      </div>`).join(""));
  }

  function fetch_pending() {
    const doctype = mode === "Receive" ? "Cold Storage Receive Goods" : "Cold Storage Dispatch Goods";
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype,
        fields: ["name", "customer", "reference", mode === "Receive" ? "receiving_datetime as dt" : "dispatch_datetime as dt"],
        filters: { docstatus: 0, workflow_state: "CS Pending Approval" },
        limit_page_length: 50,
        order_by: "modified desc",
      },
      callback: (r) => render_cards(r.message || [], doctype),
    });
  }

  $root.on("click", ".btn-recv", function () {
    mode = "Receive";
    $root.find(".btn-recv").addClass("active");
    $root.find(".btn-disp").removeClass("active");
    fetch_pending();
  });

  $root.on("click", ".btn-disp", function () {
    mode = "Dispatch";
    $root.find(".btn-disp").addClass("active");
    $root.find(".btn-recv").removeClass("active");
    fetch_pending();
  });

  $root.on("click", ".btn-approve", function () {
    const name = $(this).data("name");
    const doctype = $(this).data("doctype");
    frappe.call({
      method: "cold_storage.cold_storage.api.bulk_approve.bulk_approve",
      args: { doctype, names: [name] },
      freeze: true,
      callback: () => fetch_pending(),
    });
  });

  $root.on("click", ".btn-reject", function () {
    const name = $(this).data("name");
    const doctype = $(this).data("doctype");
    frappe.prompt([{ fieldname: "reason", label: __("Rejection Reason"), fieldtype: "Small Text", reqd: 1 }], (values) => {
      frappe.call({
        method: "cold_storage.cold_storage.api.bulk_approve.bulk_reject",
        args: { doctype, names: [name], reason: values.reason },
        freeze: true,
        callback: () => fetch_pending(),
      });
    }, __("Reject Document"), __("Reject"));
  });

  fetch_pending();
};
