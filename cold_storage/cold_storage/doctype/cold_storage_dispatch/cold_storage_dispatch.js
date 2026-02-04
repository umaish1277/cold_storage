frappe.ui.form.on('Cold Storage Dispatch Item', {
    linked_receipt: function (frm, cdt, cdn) {
        // Clear dependent fields when linked_receipt changes
        frappe.model.set_value(cdt, cdn, "warehouse", "");
        frappe.model.set_value(cdt, cdn, "goods_item", "");
        frappe.model.set_value(cdt, cdn, "item_group", "");
        frappe.model.set_value(cdt, cdn, "batch_no", "");

        // Fetch warehouse from receipt
        var row = locals[cdt][cdn];
        if (row.linked_receipt) {
            frappe.db.get_value("Cold Storage Receipt", row.linked_receipt, "warehouse", (r) => {
                if (r && r.warehouse) {
                    frappe.model.set_value(cdt, cdn, "warehouse", r.warehouse);
                }
            });
        }
    },

    warehouse: function (frm, cdt, cdn) {
        // Clear dependent fields when warehouse changes
        frappe.model.set_value(cdt, cdn, "goods_item", "");
        frappe.model.set_value(cdt, cdn, "item_group", "");
        frappe.model.set_value(cdt, cdn, "batch_no", "");
    },

    goods_item: function (frm, cdt, cdn) {
        // Clear dependent fields
        frappe.model.set_value(cdt, cdn, "item_group", "");
        frappe.model.set_value(cdt, cdn, "batch_no", "");
    },

    item_group: function (frm, cdt, cdn) {
        // Clear dependent batch
        frappe.model.set_value(cdt, cdn, "batch_no", "");

        var row = locals[cdt][cdn];
        if (row.item_group) {
            frappe.call({
                method: 'cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_bag_rate',
                args: {
                    item_group: row.item_group,
                    billing_type: frm.doc.billing_type,
                    goods_item: row.goods_item
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'rate', r.message);
                    } else {
                        frappe.model.set_value(cdt, cdn, 'rate', 0);
                    }
                }
            });
        }
    },

    rate: function (frm, cdt, cdn) {
        // Auto-calculate Item Amount when rate changes
        var row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.rate * row.number_of_bags);
    },

    number_of_bags: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.number_of_bags <= 0) {
            frappe.msgprint(__("Number of Bags must be greater than 0"));
            frappe.model.set_value(cdt, cdn, "number_of_bags", "");
            return;
        }

        // Validate against available balance
        if (row.batch_no && row.linked_receipt) {
            frappe.call({
                method: 'cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_batch_balance',
                args: {
                    linked_receipt: row.linked_receipt,
                    batch_no: row.batch_no,
                    current_dispatch: frm.doc.name
                },
                callback: function (r) {
                    let available = r.message || 0;
                    if (row.number_of_bags > available) {
                        frappe.msgprint(__("Row {0}: Insufficient balance. Available: {1}", [row.idx, available]));
                        frappe.model.set_value(cdt, cdn, "number_of_bags", ""); // Clear invalid
                    } else {
                        // Valid, Calculate Amount
                        frappe.model.set_value(cdt, cdn, 'amount', row.rate * row.number_of_bags);
                    }
                }
            });
        } else {
            // Just Calculate
            frappe.model.set_value(cdt, cdn, 'amount', row.rate * row.number_of_bags);
        }
    }
});

frappe.ui.form.on('Cold Storage Dispatch', {
    onload: function (frm) {
        // Enforce read-only company
        frm.set_df_property("company", "read_only", 1);

        if (frm.is_new()) {
            let default_company = (frm.doc.__onload && frm.doc.__onload.default_company) ? frm.doc.__onload.default_company : null;

            let set_comp = function (val) {
                if (val) {
                    frm.set_df_property("company", "read_only", 0);
                    frm.set_value("company", val);
                    frm.set_df_property("company", "read_only", 1);
                }
            };

            if (default_company) {
                set_comp(default_company);
            } else {
                frappe.db.get_single_value("Cold Storage Settings", "default_company", (value) => {
                    set_comp(value);
                });
            }
        }
    },

    company: function (frm) {
        if (frm.doc.company) {
            frappe.db.get_value("Company", frm.doc.company, "abbr", (r) => {
                if (r && r.abbr) {
                    let abbr = r.abbr;
                    let options = "CSD-.YYYY.-";

                    let new_series = `${abbr}-${options}`;

                    frm.set_df_property("naming_series", "options", new_series);
                    frm.set_value("naming_series", new_series);
                }
            });
        }
    },

    validate: function (frm) {
        // Ensure Number of Bags is positive
        $.each(frm.doc.items || [], function (i, row) {
            if (row.number_of_bags <= 0) {
                frappe.msgprint(__("Row {0}: Number of Bags must be greater than 0", [row.idx]));
                frappe.validated = false;
                return false;
            }
        });
    },

    refresh: function (frm) {
        if (frm.is_new()) {
            let default_company = (frm.doc.__onload && frm.doc.__onload.default_company) ? frm.doc.__onload.default_company : null;

            let set_comp = function (val) {
                if (val && frm.doc.company !== val) {
                    frm.set_df_property("company", "read_only", 0);
                    frm.set_value("company", val);
                    frm.set_df_property("company", "read_only", 1);
                } else if (frm.doc.company === val) {
                    frm.trigger("company");
                }
            };

            if (default_company) {
                set_comp(default_company);
            } else {
                frappe.db.get_single_value("Cold Storage Settings", "default_company", (value) => {
                    set_comp(value);
                });
            }
        }

        // Filter Linked Receipt by Customer
        frm.set_query("linked_receipt", "items", function (doc, cdt, cdn) {
            return {
                filters: {
                    "customer": doc.customer,
                    "docstatus": 1
                }
            };
        });

        // Filter Warehouse by Customer (Active Warehouses)
        frm.set_query("warehouse", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            if (row.linked_receipt) {
                // If receipt is selected, filter to that receipt's warehouse
                return {
                    query: "cold_storage.get_customer_items_query.get_receipt_warehouses",
                    filters: {
                        "linked_receipt": row.linked_receipt
                    }
                };
            }
            return {
                query: "cold_storage.get_customer_items_query.get_customer_warehouses",
                filters: {
                    "customer": doc.customer
                }
            };
        });

        // Filter Batch No by Customer, Item, Item Group and row-level Warehouse/Receipt
        frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            return {
                query: "cold_storage.get_customer_items_query.get_customer_batches",
                filters: {
                    "customer": doc.customer,
                    "item_group": row.item_group,
                    "goods_item": row.goods_item,
                    "warehouse": row.warehouse,
                    "linked_receipt": row.linked_receipt
                }
            };
        });

        // Filter Goods Item by Customer and row-level Warehouse/Receipt
        frm.set_query("goods_item", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            return {
                query: "cold_storage.get_customer_items_query.get_customer_items",
                filters: {
                    "customer": doc.customer,
                    "warehouse": row.warehouse,
                    "linked_receipt": row.linked_receipt
                }
            };
        });

        // Filter Item Group by Customer, Goods Item, and row-level Warehouse/Receipt
        frm.set_query("item_group", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            return {
                query: "cold_storage.get_customer_items_query.get_customer_item_groups",
                filters: {
                    "customer": doc.customer,
                    "goods_item": row.goods_item,
                    "warehouse": row.warehouse,
                    "linked_receipt": row.linked_receipt
                }
            };
        });
    },

    billing_type: function (frm) {
        // Update rates for all items when billing type changes
        $.each(frm.doc.items || [], function (i, row) {
            if (row.item_group) {
                frappe.call({
                    method: 'cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_bag_rate',
                    args: {
                        item_group: row.item_group,
                        billing_type: frm.doc.billing_type,
                        goods_item: row.goods_item
                    },
                    callback: function (r) {
                        frappe.model.set_value(row.doctype, row.name, 'rate', r.message || 0);
                    }
                });
            }
        });
    }
});
