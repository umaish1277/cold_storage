
frappe.ui.form.on('Cold Storage Receipt Item', {
    number_of_bags: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.number_of_bags <= 0) {
            frappe.msgprint(__("Number of Bags must be greater than 0"));
            frappe.model.set_value(cdt, cdn, "number_of_bags", "");
            return;
        }

        // Check availability if Customer Transfer
        if (frm.doc.receipt_type == "Customer Transfer" && frm.doc.source_receipt && row.batch_no) {
            frappe.call({
                method: "cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_batch_balance",
                args: {
                    linked_receipt: frm.doc.source_receipt,
                    batch_no: row.batch_no
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var available = r.message;
                        if (row.number_of_bags > available) {
                            frappe.msgprint(__("Row {0}: Insufficient balance for Batch {1}. Available: {2}, Requested: {3}",
                                [row.idx, row.batch_no, available, row.number_of_bags]));
                            frappe.model.set_value(cdt, cdn, "number_of_bags", "");
                        }
                    }
                }
            });
        } else if (frm.doc.receipt_type == "Warehouse Transfer" && frm.doc.from_warehouse && frm.doc.customer && row.batch_no) {
            frappe.call({
                method: "cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_total_batch_balance",
                args: {
                    customer: frm.doc.customer,
                    warehouse: frm.doc.from_warehouse,
                    batch_no: row.batch_no
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var available = r.message;
                        if (row.number_of_bags > available) {
                            frappe.msgprint(__("Row {0}: Insufficient balance for Batch {1}. Available: {2}, Requested: {3}",
                                [row.idx, row.batch_no, available, row.number_of_bags]));
                            frappe.model.set_value(cdt, cdn, "number_of_bags", "");
                        }
                    }
                }
            });
        }
    },



    // Filter Source Receipt by From Customer
    // Triggered when row is added or fields change
    description: function (frm, cdt, cdn) {
        // Dummy trigger if needed
    },

    batch_no: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (frm.doc.receipt_type == "Customer Transfer" && frm.doc.source_receipt && row.batch_no) {
            frappe.call({
                method: "cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_batch_balance",
                args: {
                    linked_receipt: frm.doc.source_receipt,
                    batch_no: row.batch_no
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var available = r.message;
                        // Just check if current val exceeds new batch balance
                        if (row.number_of_bags > available) {
                            frappe.msgprint(__("Row {0}: Insufficient balance for Batch {1}. Available: {2}, Requested: {3}",
                                [row.idx, row.batch_no, available, row.number_of_bags]));
                            frappe.model.set_value(cdt, cdn, "number_of_bags", "");
                        }
                    }
                }
            });
        }
        else if (frm.doc.receipt_type == "Warehouse Transfer" && frm.doc.from_warehouse && frm.doc.customer && row.batch_no) {
            frappe.call({
                method: "cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_total_batch_balance",
                args: {
                    customer: frm.doc.customer,
                    warehouse: frm.doc.from_warehouse,
                    batch_no: row.batch_no
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var available = r.message;
                        if (row.number_of_bags > available) {
                            frappe.msgprint(__("Row {0}: Insufficient balance for Batch {1}. Available: {2}, Requested: {3}",
                                [row.idx, row.batch_no, available, row.number_of_bags]));
                            frappe.model.set_value(cdt, cdn, "number_of_bags", "");
                        }
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Cold Storage Receipt', {
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
                    let options = "CSR-.YYYY.-";

                    // Construct new series
                    let new_series = `${abbr}-${options}`;

                    frm.set_df_property("naming_series", "options", new_series);
                    frm.set_value("naming_series", new_series);
                }
            });
        }
    },

    refresh: function (frm) {
        // Trigger company logic to set series on load if company exists is new
        if (frm.doc.company && frm.is_new()) {
            frm.trigger("company");
        }

        // Inject Custom CSS to resize QR Code image in form view
        const css = `
            div[data-fieldname="qr_code"] .attached-file img {
                width: 150px !important;
                height: 150px !important;
                max-width: none !important;
                max-height: none !important;
                margin-bottom: 10px;
            }
            div[data-fieldname="qr_code"] .attached-file {
                height: auto !important;
            }
        `;
        $("<style>").prop("type", "text/css").html(css).appendTo("head");

        // Filter Source Receipt (Parent Field)
        frm.set_query("source_receipt", function (doc) {
            if (doc.receipt_type == "Customer Transfer" && doc.from_customer) {
                return {
                    filters: {
                        "customer": doc.from_customer,
                        "warehouse": doc.warehouse,
                        "docstatus": 1
                    }
                };
            } else if (doc.receipt_type == "New Receipt") {
                return { filters: { "name": "INVALID" } };
            }
        });

        // Filter Batch No strict
        frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            if (doc.receipt_type == "Customer Transfer") {
                if (doc.source_receipt) {
                    return {
                        query: "cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_customer_batches",
                        filters: {
                            customer: doc.from_customer,
                            receipt: doc.source_receipt
                        }
                    };
                } else {
                    return { filters: { "customer": doc.from_customer } };
                }
            } else if (doc.receipt_type == "Warehouse Transfer") {
                if (doc.from_warehouse && doc.customer) {
                    return {
                        query: "cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch.get_customer_batches",
                        filters: {
                            customer: doc.customer,
                            warehouse: doc.from_warehouse,
                            goods_item: row.goods_item,
                            item_group: row.item_group
                        }
                    };
                } else {
                    return { filters: { "customer": doc.customer } };
                }
            } else {
                return {
                    filters: {
                        "customer": doc.customer
                    }
                };
            }
        });

        // Filter Goods Item based on Source Receipt
        frm.set_query("goods_item", "items", function (doc, cdt, cdn) {
            if (doc.receipt_type == "Customer Transfer" && doc.source_receipt) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_receipt_items",
                    filters: {
                        receipt: doc.source_receipt
                    }
                };
            } else if (doc.receipt_type == "Warehouse Transfer" && doc.customer && doc.from_warehouse) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_customer_warehouse_items",
                    filters: {
                        customer: doc.customer,
                        warehouse: doc.from_warehouse
                    }
                };
            }
        });

        // Filter Item Group based on Source Receipt
        frm.set_query("item_group", "items", function (doc, cdt, cdn) {
            if (doc.receipt_type == "Customer Transfer" && doc.source_receipt) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_receipt_item_groups",
                    filters: {
                        receipt: doc.source_receipt
                    }
                };
            } else if (doc.receipt_type == "Warehouse Transfer" && doc.customer && doc.from_warehouse) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_customer_warehouse_item_groups",
                    filters: {
                        customer: doc.customer,
                        warehouse: doc.from_warehouse
                    }
                };
            }
        });

        // Filter Warehouse based on From Customer (If Customer Transfer)
        frm.set_query("warehouse", function (doc) {
            if (doc.receipt_type == "Customer Transfer" && doc.from_customer) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_customer_warehouses",
                    filters: {
                        customer: doc.from_customer
                    }
                };
            }
        });

        // Filter From Warehouse based on Customer (If Warehouse Transfer)
        frm.set_query("from_warehouse", function (doc) {
            if (doc.receipt_type == "Warehouse Transfer" && doc.customer) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_customer_warehouses",
                    filters: {
                        customer: doc.customer
                    }
                };
            }
        });

        // Trigger Receipt Type Logic for UI state
        frm.trigger("receipt_type");
    },

    receipt_type: function (frm) {
        // Handle Field Visibility
        if (frm.doc.receipt_type == "New Receipt") {
            frm.set_value("from_customer", "");
            frm.set_value("from_warehouse", "");
        } else if (frm.doc.receipt_type == "Customer Transfer") {
            frm.set_value("from_warehouse", "");
        } else if (frm.doc.receipt_type == "Warehouse Transfer") {
            frm.set_value("from_customer", "");
        }

        // Legacy Grid Column logic removed as field is now in Parent
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
    }
});
