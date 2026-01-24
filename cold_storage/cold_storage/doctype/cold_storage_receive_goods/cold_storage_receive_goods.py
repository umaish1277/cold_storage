from __future__ import annotations
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate

from cold_storage.cold_storage.utils.rate_engine import compute_storage_amount

class ColdStorageReceiveGoods(Document):
    def validate(self):
        self._compute_bag_totals()

    def _compute_bag_totals(self):
        jute = 0
        net = 0
        for r in (self.get("bags") or []):
            if r.bag_type == "Jute":
                jute += int(r.qty or 0)
            elif r.bag_type == "Net":
                net += int(r.qty or 0)
        self.total_jute_bags = jute
        self.total_net_bags = net

def on_submit_create_docs(doc: ColdStorageReceiveGoods, method=None):
    # 1) Storage Batch
    sb = frappe.new_doc("Storage Batch")
    sb.customer = doc.customer
    sb.contract = doc.contract
    sb.item = doc.item
    sb.batch = doc.batch
    sb.chamber = doc.chamber
    sb.warehouse = doc.warehouse
    sb.in_date = doc.receiving_datetime or now_datetime()
    sb.status = "In Storage"
    sb.jute_in = doc.total_jute_bags or 0
    sb.net_in = doc.total_net_bags or 0
    sb.jute_out = 0
    sb.net_out = 0
    sb.receive_goods = doc.name
    sb.insert(ignore_permissions=True)

    doc.db_set("generated_storage_batch", sb.name)

    # 2) Bag Receipt
    if frappe.db.exists("DocType", "Bag Receipt"):
        br = frappe.new_doc("Bag Receipt")
        br.customer = doc.customer
        br.contract = doc.contract
        br.posting_datetime = doc.receiving_datetime or now_datetime()
        br.reference = doc.reference
        br.storage_batch = sb.name
        for r in (doc.get("bags") or []):
            br.append("bags", {"bag_type": r.bag_type, "qty": r.qty})
        br.insert(ignore_permissions=True)
        br.submit()

    # 3) Stock Entry (Material Receipt)
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Receipt"
    se.company = frappe.defaults.get_user_default("Company") or frappe.db.get_default("company")
    se.posting_date = getdate(doc.receiving_datetime) if doc.receiving_datetime else getdate(now_datetime())
    se.posting_time = (doc.receiving_datetime or now_datetime()).strftime("%H:%M:%S")
    se.append("items", {
        "item_code": doc.item,
        "qty": doc.qty_stored,
        "uom": doc.uom or "Nos",
        "t_warehouse": doc.warehouse,
        "batch_no": doc.batch,
    })
    se.insert(ignore_permissions=True)
    se.submit()

    # 4) Optional Sales Invoice (draft) for given period (prorated seasonal)
    if doc.get("create_sales_invoice"):
        ps = doc.get("invoice_period_start")
        pe = doc.get("invoice_period_end")
        if ps and pe:
            result = compute_storage_amount(doc.contract, ps, pe)
            if result["total"] > 0:
                inv = frappe.new_doc("Sales Invoice")
                inv.customer = doc.customer
                inv.posting_date = getdate(now_datetime())
                inv.due_date = getdate(now_datetime())
                inv.cold_storage_contract = doc.contract
                inv.cold_storage_period_start = ps
                inv.cold_storage_period_end = pe
                inv.append("items", {
                    "item_code": doc.item,
                    "qty": 1,
                    "rate": result["total"],
                    "description": f"Cold Storage Charges ({ps} to {pe})",
                })
                inv.insert(ignore_permissions=True)
