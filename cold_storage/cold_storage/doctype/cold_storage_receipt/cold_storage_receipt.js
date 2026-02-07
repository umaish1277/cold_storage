
frappe.ui.form.on('Cold Storage Receipt Item', {
    goods_item: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.goods_item) {
            frappe.db.get_value('Item', row.goods_item, 'item_group', function (value) {
                if (value && value.item_group) {
                    frappe.model.set_value(cdt, cdn, 'item_group', value.item_group);
                }
            });
        }
    },

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
    onload: function (frm) {
        if (frm.is_new()) {
            let default_company = (frm.doc.__onload && frm.doc.__onload.default_company) ? frm.doc.__onload.default_company : null;

            let set_comp = function (val) {
                if (val) {
                    frm.set_value("company", val);
                }
            };

            if (default_company) {
                set_comp(default_company);
            } else {
                frappe.db.get_single_value("Cold Storage Settings", "default_company", (value) => {
                    set_comp(value);
                });
            }

            // Clear old links if this is an amendment to prevent link validation errors
            if (frm.doc.amended_from) {
                frm.set_value("stock_entry", "");
                frm.set_value("transfer_loading_journal_entry", "");
            }
        }

        // Inject Custom CSS to resize QR Code image in form view
        const css = `
            div[data-fieldname="qr_code"] .attached-file img {
                width: 300px !important;
                height: 300px !important;
                max-width: none !important;
                max-height: none !important;
                margin-bottom: 10px;
            }
            div[data-fieldname="qr_code"] .attached-file {
                height: auto !important;
            }
        `;
        if (!$(`#qr-code-style`).length) {
            $("<style id='qr-code-style'>").prop("type", "text/css").html(css).appendTo("head");
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
        if (frm.is_new()) {
            let default_company = (frm.doc.__onload && frm.doc.__onload.default_company) ? frm.doc.__onload.default_company : null;

            let set_comp = function (val) {
                if (val && frm.doc.company !== val) {
                    frm.set_value("company", val);
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
                        "company": doc.company,
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
                return {
                    query: "cold_storage.get_customer_items_query.get_customer_batches",
                    filters: {
                        customer: doc.from_customer,
                        linked_receipt: doc.source_receipt,
                        company: doc.company
                    }
                };
            } else if (doc.receipt_type == "Warehouse Transfer") {
                return {
                    query: "cold_storage.get_customer_items_query.get_customer_batches",
                    filters: {
                        customer: doc.customer,
                        warehouse: doc.from_warehouse,
                        goods_item: row.goods_item,
                        item_group: row.item_group,
                        company: doc.company
                    }
                };
            } else {
                return {
                    filters: {
                        customer: doc.customer,
                        company: doc.company
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
                        receipt: doc.source_receipt,
                        company: doc.company
                    }
                };
            } else if (doc.receipt_type == "Warehouse Transfer" && doc.customer && doc.from_warehouse) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_customer_warehouse_items",
                    filters: {
                        customer: doc.customer,
                        warehouse: doc.from_warehouse,
                        company: doc.company
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
                        receipt: doc.source_receipt,
                        company: doc.company
                    }
                };
            } else if (doc.receipt_type == "Warehouse Transfer" && doc.customer && doc.from_warehouse) {
                return {
                    query: "cold_storage.cold_storage.doctype.cold_storage_receipt.cold_storage_receipt.get_customer_warehouse_item_groups",
                    filters: {
                        customer: doc.customer,
                        warehouse: doc.from_warehouse,
                        company: doc.company
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
                        customer: doc.from_customer,
                        company: doc.company
                    }
                };
            } else {
                return {
                    filters: {
                        company: doc.company
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
                        customer: doc.customer,
                        company: doc.company
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
