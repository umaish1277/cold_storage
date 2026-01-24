# ERPNext Cold Storage (Frappe/ERPNext v17)

This app provides a Cold Storage operations + billing module for ERPNext v17.

## Features
- Receive Goods workflow: creates Storage Batch + Bag Receipt + Stock Entry (+ optional Sales Invoice)
- Dispatch Goods workflow: creates Stock Entry + Bag Issue and updates Storage Batch balances
- Rate engine: Net/Jute bags, 2 Net = 1 Jute Equivalent Bag (JEB), seasonal proration, optional monthly minimum
- Workflows: Draft → Pending Approval → Approved (Submit) for Receive/Dispatch
- Bell 🔔 notifications when Receive/Dispatch enters Pending Approval
- Bulk Approve / Reject from List View (Supervisor+)
- Cold Storage Approvals desk page (mobile-friendly)
- Workspace + dashboard cards/charts
- Reports: Gate Register, Utilization Trend, Billing Breakup (batch-wise), Aging, Bag balances, Outstanding, etc.

## Install (inside an ERPNext v17 bench)

```bash
bench get-app https://github.com/<you>/<repo>.git
bench --site <site> install-app cold_storage
bench --site <site> migrate
bench --site <site> clear-cache
bench build
bench restart
```

## First-time setup
1. Create roles:
   - Cold Storage Gate Operator
   - Cold Storage Supervisor
   - Cold Storage Billing User
   - Cold Storage Manager
   - Cold Storage Auditor
2. Create:
   - Cold Storage Season
   - Cold Storage Rate Card (Rule: Storage / Per Jute Eq Bag / Rate Per Season)
   - Cold Storage Chamber (link to Warehouse)
   - Storage Contract (customer + season + rate card)
