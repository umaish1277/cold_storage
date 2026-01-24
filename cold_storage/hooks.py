app_name = "cold_storage"
app_title = "Cold Storage"
app_publisher = ""
app_description = "Cold Storage operations + billing for ERPNext"
app_email = ""
app_license = "MIT"

doctype_list_js = {
    "Cold Storage Receive Goods": "public/js/receive_goods_list.js",
    "Cold Storage Dispatch Goods": "public/js/dispatch_goods_list.js",
}

app_include_js = [
    "cold_storage/public/js/workspace_approvals_refresh.js"
]

override_doctype_dashboards = {
    "Storage Batch": "cold_storage.cold_storage.config.storage_batch.get_data"
}

doc_events = {
    "Cold Storage Receive Goods": {
        "on_submit": "cold_storage.cold_storage.doctype.cold_storage_receive_goods.cold_storage_receive_goods.on_submit_create_docs"
    },
    "Cold Storage Dispatch Goods": {
        "on_submit": "cold_storage.cold_storage.doctype.cold_storage_dispatch_goods.cold_storage_dispatch_goods.on_submit_create_docs"
    },
}
