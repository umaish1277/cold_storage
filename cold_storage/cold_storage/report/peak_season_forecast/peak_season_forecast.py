import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart

def get_columns():
	return [
		{"label": _("Month"), "fieldname": "month_name", "fieldtype": "Data", "width": 120},
		{"label": _("Avg. Intake (Bags)"), "fieldname": "avg_intake", "fieldtype": "Float", "width": 140},
		{"label": _("Avg. Outtake (Bags)"), "fieldname": "avg_outtake", "fieldtype": "Float", "width": 140},
		{"label": _("Total Activity"), "fieldname": "total_volume", "fieldtype": "Float", "width": 140},
		{"label": _("Busy Index"), "fieldname": "busy_index", "fieldtype": "Float", "width": 100},
		{"label": _("Forecast Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]

def get_data(filters):
	import calendar
	
	# 1. Fetch Month-wise Averages (Historical)
	# Intake
	intake_data = frappe.db.sql("""
		SELECT MONTH(receipt_date) as month, SUM(total_bags) / COUNT(DISTINCT YEAR(receipt_date)) as avg_bags
		FROM `tabCold Storage Receipt`
		WHERE docstatus = 1
		GROUP BY MONTH(receipt_date)
	""", as_dict=1)
	
	# Outtake
	outtake_data = frappe.db.sql("""
		SELECT MONTH(d.dispatch_date) as month, SUM(di.number_of_bags) / COUNT(DISTINCT YEAR(d.dispatch_date)) as avg_bags
		FROM `tabCold Storage Dispatch` d
		JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
		WHERE d.docstatus = 1
		GROUP BY MONTH(d.dispatch_date)
	""", as_dict=1)

	intake_map = {d.get("month"): flt(d.get("avg_bags")) for d in intake_data}
	outtake_map = {d.get("month"): flt(d.get("avg_bags")) for d in outtake_data}

	# 2. Identify Active Seasons
	active_seasons = frappe.get_all("Cold Storage Season", 
		filters={"is_active": 1}, 
		fields=["season_name", "from_date", "to_date"]
	)

	data = []
	volumes = []
	for m in range(1, 13):
		intake = intake_map.get(m, 0)
		outtake = outtake_map.get(m, 0)
		total = intake + outtake
		volumes.append(total)
		
		data.append({
			"month_num": m,
			"month_name": calendar.month_name[m],
			"avg_intake": intake,
			"avg_outtake": outtake,
			"total_volume": total,
		})

	# 3. Calculate Busy Index and Status
	avg_annual_volume = sum(volumes) / 12 if volumes else 0
	
	for row in data:
		idx = (row["total_volume"] / avg_annual_volume) if avg_annual_volume > 0 else 0
		row["busy_index"] = round(idx, 2)
		
		# Overlay Season logic
		is_in_season = False
		m_num = row["month_num"]
		for s in active_seasons:
			start_m = getdate(s.from_date).month
			end_m = getdate(s.to_date).month
			if start_m <= m_num <= end_m:
				is_in_season = True
				break
		
		# Category logic
		if idx > 1.5 or (idx > 1.1 and is_in_season):
			row["status"] = "Peak"
		elif idx > 1.0:
			row["status"] = "High"
		elif idx > 0.6:
			row["status"] = "Medium"
		else:
			row["status"] = "Low"

	return data

def get_chart(data):
	labels = [d["month_name"][:3] for d in data]
	intake_vals = [d["avg_intake"] for d in data]
	outtake_vals = [d["avg_outtake"] for d in data]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Avg Intake"), "values": intake_vals},
				{"name": _("Avg Outtake"), "values": outtake_vals},
			]
		},
		"type": "line",
		"colors": ["#4CAF50", "#FF5722"]
	}
