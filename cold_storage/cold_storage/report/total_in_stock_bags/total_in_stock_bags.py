import frappe
from frappe import _
from frappe.utils import add_days, date_diff, getdate, nowdate, add_months

def execute(filters=None):
    if not filters: filters = {}
    
    # Default filters if not present
    if not filters.get("from_date"):
        filters["from_date"] = add_months(nowdate(), -1)
    if not filters.get("to_date"):
        filters["to_date"] = nowdate()

    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 100}
    ]

    # Get Distinct Item Groups
    item_groups = frappe.db.sql("""
        SELECT DISTINCT item_group FROM `tabCold Storage Receipt Item` WHERE item_group IS NOT NULL
        UNION
        SELECT DISTINCT item_group FROM `tabCold Storage Dispatch Item` WHERE item_group IS NOT NULL
    """, as_dict=True)
    
    distinct_item_groups = sorted([row.item_group for row in item_groups if row.item_group])
    if not distinct_item_groups:
        distinct_item_groups = ["Unspecified"]

    for bt in distinct_item_groups:
        columns.append({
            "label": bt,
            "fieldname": frappe.scrub(bt),
            "fieldtype": "Int",
            "width": 100
        })

    # 1. Calculate Opening Balance (Before from_date)
    opening_in = frappe.db.sql("""
        SELECT c.item_group, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 AND p.receipt_date < %s
        GROUP BY c.item_group
    """, (filters["from_date"],), as_dict=True)

    opening_out = frappe.db.sql("""
        SELECT d_item.item_group, SUM(d_item.number_of_bags) as qty
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = d.name
        WHERE d.docstatus = 1 AND d.dispatch_date < %s
        GROUP BY d_item.item_group
    """, (filters["from_date"],), as_dict=True)

    balance = {bt: 0 for bt in distinct_item_groups}
    
    for row in opening_in:
        bt = row.item_group
        if bt in balance: balance[bt] += (row.qty or 0)
        
    for row in opening_out:
        bt = row.item_group
        if bt in balance: balance[bt] -= (row.qty or 0)


    # 2. Get Daily Movements (from_date to to_date)
    daily_in = frappe.db.sql("""
        SELECT p.receipt_date as date, c.item_group, SUM(c.number_of_bags) as qty
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 AND p.receipt_date BETWEEN %s AND %s
        GROUP BY p.receipt_date, c.item_group
    """, (filters["from_date"], filters["to_date"]), as_dict=True)

    daily_out = frappe.db.sql("""
        SELECT d.dispatch_date as date, d_item.item_group, SUM(d_item.number_of_bags) as qty
        FROM `tabCold Storage Dispatch` d
        JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = d.name
        WHERE d.docstatus = 1 AND d.dispatch_date BETWEEN %s AND %s
        GROUP BY d.dispatch_date, d_item.item_group
    """, (filters["from_date"], filters["to_date"]), as_dict=True)

    # Organize movements by date
    movements = {} # date -> {item_group: net_change}
    
    for row in daily_in:
        d = str(row.date)
        if d not in movements: movements[d] = {bt: 0 for bt in distinct_item_groups}
        if row.item_group in movements[d]:
            movements[d][row.item_group] += (row.qty or 0)
            
    for row in daily_out:
        d = str(row.date)
        if d not in movements: movements[d] = {bt: 0 for bt in distinct_item_groups}
        if row.item_group in movements[d]:
            movements[d][row.item_group] -= (row.qty or 0)

    # 3. Generate Timeseries Data
    data = []
    labels = []
    datasets_map = {bt: [] for bt in distinct_item_groups}
    total_dataset = []
    
    start_date = getdate(filters["from_date"])
    end_date = getdate(filters["to_date"])
    
    days = date_diff(end_date, start_date) + 1
    
    for i in range(days):
        current_date = add_days(start_date, i)
        date_str = str(current_date)
        labels.append(date_str)
        
        # Apply movements for this day
        if date_str in movements:
            for bt, change in movements[date_str].items():
                balance[bt] += change
        
        # Record balance
        row = {"date": date_str}
        daily_total = 0
        for bt in distinct_item_groups:
            row[frappe.scrub(bt)] = balance[bt]
            datasets_map[bt].append(balance[bt])
            daily_total += balance[bt]
        
        row["total"] = daily_total
        total_dataset.append(daily_total)
        
        data.append(row)

    # 4. Construct Chart
    datasets = []
    # Assign colors: bag types get standard colors, Total gets Black
    colors = ["#449CF0", "#ECAD4B", "#28a745", "#dc3545", "#ffc107", "#17a2b8"]
    
    for i, bt in enumerate(distinct_item_groups):
        datasets.append({
            "name": bt,
            "values": datasets_map[bt]
        })
        
    # Add Total dataset
    datasets.append({
        "name": "Total",
        "values": total_dataset
    })
    
    # Append Black color for Total
    colors = colors[:len(datasets)-1] + ["#000000"]

    chart = {
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "type": "line",
        "colors": colors
    }

    return columns, data, None, chart
