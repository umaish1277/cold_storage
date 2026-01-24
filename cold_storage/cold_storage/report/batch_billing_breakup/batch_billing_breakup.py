from __future__ import annotations
from frappe.utils import getdate
from cold_storage.cold_storage.utils.rate_engine import compute_storage_amount

def execute(filters=None):
    filters = filters or {}
    contract = filters.get("contract")
    ps = getdate(filters.get("from_date"))
    pe = getdate(filters.get("to_date"))
    chamber = filters.get("chamber")

    result = compute_storage_amount(contract, ps, pe, chamber=chamber)

    columns = [
        {"label": "Storage Batch", "fieldname": "storage_batch", "fieldtype": "Link", "options": "Storage Batch", "width": 160},
        {"label": "ERP Batch", "fieldname": "erp_batch", "fieldtype": "Link", "options": "Batch", "width": 120},
        {"label": "Item", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": "Chamber", "fieldname": "chamber", "fieldtype": "Link", "options": "Cold Storage Chamber", "width": 140},
        {"label": "In Date", "fieldname": "in_date", "fieldtype": "Datetime", "width": 150},
        {"label": "Out Date", "fieldname": "out_date", "fieldtype": "Datetime", "width": 150},
        {"label": "Jute Bal", "fieldname": "jute", "fieldtype": "Int", "width": 90},
        {"label": "Net Bal", "fieldname": "net", "fieldtype": "Int", "width": 90},
        {"label": "JEB", "fieldname": "jeb", "fieldtype": "Float", "width": 90},
        {"label": "Overlap Days", "fieldname": "days", "fieldtype": "Int", "width": 100},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 130},
    ]

    data = result["lines"][:]
    data.append({"storage_batch": "TOTAL", "amount": result["total"]})
    return columns, data
