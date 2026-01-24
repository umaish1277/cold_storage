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
        {"label":"Contract/Batch","fieldname":"contract","fieldtype":"Data","width":220},
        {"label":"Period / Detail","fieldname":"period","fieldtype":"Data","width":240},
        {"label":"Rate/Season (per JEB)","fieldname":"rate","fieldtype":"Currency","width":160},
        {"label":"Season Days","fieldname":"season_days","fieldtype":"Int","width":120},
        {"label":"Amount","fieldname":"total","fieldtype":"Currency","width":160},
    ]

    data = [{
        "contract": contract,
        "period": f"{ps} to {pe}",
        "rate": result["rate_per_season"],
        "season_days": result["season_days"],
        "total": result["total"],
    }]
    for ln in result["lines"]:
        data.append({
            "contract": ln["storage_batch"],
            "period": f"{ln['days']} days • {ln['jeb']} JEB • {ln['chamber']}",
            "rate": None,
            "season_days": None,
            "total": ln["amount"],
        })
    return columns, data
