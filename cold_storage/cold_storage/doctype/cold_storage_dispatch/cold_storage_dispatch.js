frappe.ui.form.on('Cold Storage Dispatch Item', {
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
        if (row.batch_no) {
            frappe.call({
                method: 'cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_batch_balance',
                args: {
                    linked_receipt: frm.doc.linked_receipt,
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
            // Just Calulate
            frappe.model.set_value(cdt, cdn, 'amount', row.rate * row.number_of_bags);
        }
    }
});

frappe.ui.form.on('Cold Storage Dispatch', {
    setup: function (frm) {
        if (frm.is_new()) {
            frappe.db.get_single_value("Cold Storage Settings", "default_company")
                .then(value => {
                    if (value) {
                        frm.set_value("company", value);
                    }
                });
        }
    },

    company: function (frm) {
        if (frm.doc.company) {
            frappe.db.get_value("Company", frm.doc.company, "abbr", (r) => {
                if (r && r.abbr) {
                    let abbr = r.abbr;
                    let options = "CSD-.MM.-.YY.-";

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
        if (frm.doc.company && frm.is_new()) {
            frm.trigger("company");
        }

        // Filter Batch No by Customer, Item, Item Group and Warehouse
        frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            return {
                query: "cold_storage.get_customer_items_query.get_customer_batches",
                filters: {
                    "customer": doc.customer,
                    "item_group": row.item_group,
                    "goods_item": row.goods_item,
                    "warehouse": doc.warehouse,
                    "linked_receipt": doc.linked_receipt
                }
            };
        });

        // Filter Goods Item by Customer and Warehouse
        frm.set_query("goods_item", "items", function (doc, cdt, cdn) {
            return {
                query: "cold_storage.get_customer_items_query.get_customer_items",
                filters: {
                    "customer": doc.customer,
                    "warehouse": doc.warehouse,
                    "linked_receipt": doc.linked_receipt
                }
            };
        });

        // Filter Item Group by Customer, Goods Item, and Warehouse
        frm.set_query("item_group", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            return {
                query: "cold_storage.get_customer_items_query.get_customer_item_groups",
                filters: {
                    "customer": doc.customer,
                    "goods_item": row.goods_item,
                    "warehouse": doc.warehouse,
                    "linked_receipt": doc.linked_receipt
                }
            };
        });

        // Filter Linked Receipt by Customer and Warehouse
        frm.set_query("linked_receipt", function (doc) {
            return {
                filters: {
                    "customer": doc.customer,
                    "warehouse": doc.warehouse
                }
            };
        });

        // Filter Warehouse by Customer (Active Warehouses)
        frm.set_query("warehouse", function (doc) {
            return {
                query: "cold_storage.get_customer_items_query.get_customer_warehouses",
                filters: {
                    "customer": doc.customer
                }
            };
        });
    },

    warehouse: function (frm) {
        // Clear child table items when warehouse changes to prevent invalid selections
        frm.clear_table("items");
        // Clear linked receipt as it depends on warehouse
        frm.set_value("linked_receipt", "");
        frm.refresh_field("items");
    },

    billing_type: function (frm) {
        // Update rates for all items when billing type changes
        $.each(frm.doc.items || [], function (i, row) {
            if (row.bag_type) {
                frappe.call({
                    method: 'cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_bag_rate',
                    args: {
                        bag_type: row.bag_type,
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
