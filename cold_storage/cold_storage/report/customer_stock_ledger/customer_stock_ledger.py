import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Receipt Date"), "fieldname": "receipt_date", "fieldtype": "Date", "width": 100},
		{"label": _("Receipt"), "fieldname": "receipt", "fieldtype": "Link", "options": "Cold Storage Receipt", "width": 150},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
		{"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Data", "width": 120},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
		{"label": _("Days In Store"), "fieldname": "days_in_store", "fieldtype": "Int", "width": 100},
		{"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Int", "width": 100},
		{"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Int", "width": 100},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Int", "width": 100},
		{"label": _("Cumulative Balance"), "fieldname": "cumulative_balance", "fieldtype": "Int", "width": 140},
	]

	data = []
	
	conditions = ""
	if filters.get("customer"):
		conditions += f" AND p.customer = '{filters.get('customer')}'"
	if filters.get("batch_no"):
		conditions += f" AND c.batch_no LIKE '%{filters.get('batch_no')}%'"
	if filters.get("warehouse"):
		conditions += f" AND p.warehouse = '{filters.get('warehouse')}'"
	if filters.get("item_group"):
		conditions += f" AND c.item_group = '{filters.get('item_group')}'"
	if filters.get("item_code"):
		conditions += f" AND c.goods_item = '{filters.get('item_code')}'"
	if filters.get("from_date"):
		conditions += f" AND p.receipt_date >= '{filters.get('from_date')}'"
	if filters.get("to_date"):
		conditions += f" AND p.receipt_date <= '{filters.get('to_date')}'"
    
	# Fetch Receipts from Child Table
	receipts = frappe.db.sql(f"""
		SELECT 
            p.name as receipt, p.customer, p.warehouse, c.goods_item as item, c.item_group, c.batch_no, p.receipt_date, c.number_of_bags as in_qty 
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions}
	""", as_dict=True)

	total_in_qty = 0
	total_out_qty = 0
	total_balance = 0
	cumulative_balance = 0

	for r in receipts:
		# Calculate Out Qty from Dispatches
		out_qty = frappe.db.sql("""
			SELECT SUM(d_item.number_of_bags) 
			FROM `tabCold Storage Dispatch` d
			JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = d.name
			WHERE d.docstatus = 1 AND d_item.linked_receipt = %s AND d_item.batch_no = %s
		""", (r.receipt, r.batch_no), as_dict=False)[0][0] or 0
		
		balance = r.in_qty - out_qty
		
		days = frappe.utils.date_diff(frappe.utils.today(), r.receipt_date)

		if balance == 0 and not filters.get("show_zero_balance"):
			continue

		cumulative_balance += balance
			
		data.append({
			"receipt_date": r.receipt_date,
			"receipt": r.receipt,
			"customer": r.customer,
			"item": r.item,
			"item_group": r.item_group,
			"batch_no": r.batch_no,
			"warehouse": r.warehouse,
			"days_in_store": days,
			"in_qty": r.in_qty,
			"out_qty": out_qty,
			"balance": balance,
			"cumulative_balance": cumulative_balance
		})

		total_in_qty += r.in_qty
		total_out_qty += out_qty
		total_balance += balance

	if data:
		data.append({
			"receipt_date": "",
			"receipt": "",
			"customer": "",
			"item": "",
			"item_group": "",
			"batch_no": frappe.bold(_("Total")),
			"warehouse": "",
			"days_in_store": None,
			"in_qty": total_in_qty,
			"out_qty": total_out_qty,
			"balance": total_balance,
			"cumulative_balance": None
		})

	return columns, data

