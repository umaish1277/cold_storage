from __future__ import annotations
import frappe

def execute(filters=None):
    filters = filters or {}
    customer = filters.get("customer")
    contract = filters.get("contract")

    columns = [
        {"label":"Contract","fieldname":"contract","fieldtype":"Link","options":"Storage Contract","width":180},
        {"label":"Customer","fieldname":"customer","fieldtype":"Link","options":"Customer","width":220},
        {"label":"Invoices","fieldname":"invoices","fieldtype":"Int","width":90},
        {"label":"Outstanding","fieldname":"outstanding","fieldtype":"Currency","width":140},
    ]

    params = {}
    cond = " where si.docstatus=1 and si.outstanding_amount > 0 and si.cold_storage_contract is not null and si.cold_storage_contract != ''"
    if customer:
        cond += " and si.customer=%(customer)s"; params["customer"] = customer
    if contract:
        cond += " and si.cold_storage_contract=%(contract)s"; params["contract"] = contract

    rows = frappe.db.sql(
        f"""
        select si.cold_storage_contract as contract,
               si.customer as customer,
               count(*) as invoices,
               coalesce(sum(si.outstanding_amount),0) as outstanding
        from `tabSales Invoice` si
        {cond}
        group by si.cold_storage_contract, si.customer
        order by si.customer, si.cold_storage_contract
        """,
        params,
        as_dict=True,
    )
    return columns, rows
