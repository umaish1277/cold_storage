import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Bag Type"), "fieldname": "bag_type", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": _("Batch No"), "fieldname": "batch_no", "fieldtype": "Data", "width": 120},
		{"label": _("Receipt"), "fieldname": "receipt", "fieldtype": "Link", "options": "Cold Storage Receipt", "width": 150},
		{"label": _("Receipt Date"), "fieldname": "receipt_date", "fieldtype": "Date", "width": 100},
        {"label": _("Days In Store"), "fieldname": "days_in_store", "fieldtype": "Int", "width": 100},
		{"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Int", "width": 100},
		{"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Int", "width": 100},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Int", "width": 100},
	]

	data = []
	
	conditions = ""
	if filters.get("customer"):
		conditions += f" AND customer = '{filters.get('customer')}'"
	if filters.get("batch_no"):
		conditions += f" AND batch_no LIKE '%{filters.get('batch_no')}%'"
	if filters.get("warehouse"):
		conditions += f" AND p.warehouse = '{filters.get('warehouse')}'"
	if filters.get("bag_type"):
		conditions += f" AND c.bag_type = '{filters.get('bag_type')}'"
    
	# Fetch Receipts from Child Table
	receipts = frappe.db.sql(f"""
		SELECT 
            p.name as receipt, p.customer, c.goods_item as item, c.bag_type, c.batch_no, p.receipt_date, c.number_of_bags as in_qty 
        FROM `tabCold Storage Receipt` p
        JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
        WHERE p.docstatus = 1 {conditions}
	""", as_dict=True)

	for r in receipts:
		# Calculate Out Qty from Dispatches
        # Dispatch logic might need looking at batch no + receipt combo
		out_qty = frappe.db.sql("""
			SELECT SUM(d_item.number_of_bags) 
            FROM `tabCold Storage Dispatch` d
            JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = d.name
            WHERE d.docstatus = 1 AND d.linked_receipt = %s AND d_item.batch_no = %s
		""", (r.receipt, r.batch_no), as_dict=False)[0][0] or 0
        
		balance = r.in_qty - out_qty
        
		days = frappe.utils.date_diff(frappe.utils.today(), r.receipt_date)

		if balance == 0 and not filters.get("show_zero_balance"):
			continue
            
		data.append({
			"customer": r.customer,
			"item": r.item,
            "bag_type": r.bag_type,
			"batch_no": r.batch_no,
			"receipt": r.receipt,
            "receipt_date": r.receipt_date,
            "days_in_store": days,
			"in_qty": r.in_qty,
			"out_qty": out_qty,
			"balance": balance
		})

	return columns, data

@frappe.whitelist()
def get_bag_type_filter(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(f"""
		SELECT DISTINCT bag_type 
		FROM `tabCold Storage Receipt Item`
		WHERE bag_type LIKE %(txt)s
		AND docstatus = 1
		LIMIT %(page_len)s OFFSET %(start)s
	""", {
		'txt': f"%{txt}%",
		'page_len': page_len,
		'start': start
	})
