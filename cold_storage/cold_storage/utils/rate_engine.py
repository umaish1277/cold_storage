from __future__ import annotations
import frappe
from frappe.utils import getdate

def jeb_from_counts(jute: float, net: float) -> float:
    return float(jute or 0) + (float(net or 0) / 2.0)

def inclusive_days(a, b) -> int:
    a = getdate(a); b = getdate(b)
    return max((b - a).days + 1, 0)

def overlap_days(start1, end1, start2, end2) -> int:
    s = max(getdate(start1), getdate(start2))
    e = min(getdate(end1), getdate(end2))
    if e < s:
        return 0
    return inclusive_days(s, e)

def get_rate_per_season(rate_card_name: str) -> float:
    rc = frappe.get_doc("Cold Storage Rate Card", rate_card_name)
    for r in rc.charge_rules:
        if (r.charge_type == "Storage") and (r.billing_basis == "Per Jute Eq Bag"):
            return float(r.rate or 0)
    for r in rc.charge_rules:
        if r.charge_type == "Storage":
            return float(r.rate or 0)
    return 0.0

def get_season_days(season_name: str) -> int:
    season = frappe.get_doc("Cold Storage Season", season_name)
    return max(inclusive_days(season.start_date, season.end_date), 1)

def compute_storage_amount(contract_name: str, period_start, period_end, chamber: str | None = None):
    sc = frappe.get_doc("Storage Contract", contract_name)
    ps = getdate(period_start); pe = getdate(period_end)

    season_days = 1
    if sc.season:
        season_days = get_season_days(sc.season)

    rate_per_season = get_rate_per_season(sc.rate_card)

    params = {"contract": contract_name, "ps": ps, "pe": pe}
    ch_cond = ""
    if chamber:
        ch_cond = " and chamber=%(chamber)s"
        params["chamber"] = chamber

    batches = frappe.db.sql(
        f"""
        select name, batch, item, chamber, in_date, out_date,
               coalesce(jute_in,0) as jute_in, coalesce(jute_out,0) as jute_out,
               coalesce(net_in,0) as net_in, coalesce(net_out,0) as net_out
        from `tabStorage Batch`
        where docstatus=1
          and contract=%(contract)s
          and in_date <= %(pe)s
          and (out_date is null or out_date >= %(ps)s)
          {ch_cond}
        order by in_date asc
        """,
        params,
        as_dict=True,
    )

    lines = []
    total = 0.0
    for b in batches:
        end = b["out_date"] or pe
        days = overlap_days(b["in_date"], end, ps, pe)
        if days <= 0:
            continue
        jute = float(b["jute_in"]) - float(b["jute_out"])
        net = float(b["net_in"]) - float(b["net_out"])
        jeb = jeb_from_counts(jute, net)
        amount = float(jeb) * float(rate_per_season) * (float(days) / float(season_days)) if rate_per_season else 0.0
        total += amount
        lines.append({
            "storage_batch": b["name"],
            "erp_batch": b["batch"],
            "item": b["item"],
            "chamber": b["chamber"],
            "in_date": b["in_date"],
            "out_date": b["out_date"],
            "jute": jute,
            "net": net,
            "jeb": jeb,
            "days": days,
            "amount": amount,
        })

    min_monthly = float(getattr(sc, "min_monthly_amount", 0) or 0)
    if min_monthly and sc.get("billing_cycle") == "Monthly":
        total = max(total, min_monthly)

    return {"total": total, "lines": lines, "rate_per_season": rate_per_season, "season_days": season_days}
