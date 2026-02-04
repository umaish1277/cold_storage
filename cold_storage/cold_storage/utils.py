import frappe

@frappe.whitelist()
def get_item_group_filter(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(f"""
		SELECT DISTINCT item_group 
		FROM `tabCold Storage Receipt Item`
		WHERE item_group LIKE %(txt)s
		AND docstatus = 1
		LIMIT %(page_len)s OFFSET %(start)s
	""", {
		'txt': f"%{txt}%",
		'page_len': page_len,
		'start': start
	})

@frappe.whitelist()
def get_active_batches_count(filters=None):
        return frappe.db.sql("""
        SELECT COUNT(*) FROM (
            SELECT c.batch_no, SUM(c.qty) as balance FROM (
                SELECT ri.batch_no, ri.number_of_bags as qty
                FROM `tabCold Storage Receipt Item` ri
                JOIN `tabCold Storage Receipt` r ON ri.parent = r.name
                WHERE r.docstatus = 1
                
                UNION ALL
                
                SELECT di.batch_no, -di.number_of_bags as qty
                FROM `tabCold Storage Dispatch Item` di
                JOIN `tabCold Storage Dispatch` d ON di.parent = d.name
                WHERE d.docstatus = 1
            ) c
            GROUP BY c.batch_no
            HAVING SUM(c.qty) > 0
        ) as active_batches
    """)[0][0]

from frappe.utils import flt, getdate, nowdate

def validate_future_date(date_val, label="Date"):
	if date_val and getdate(date_val) > getdate(nowdate()):
		frappe.throw(f"{label} cannot be in the future")

def get_bag_rate(item_group, billing_type, goods_item=None):
	# Fetch all rates in one go to minimize DB calls if called in loop?
	# Usually settings is a singleton, so frappe.get_single caches it.
	settings = frappe.get_single("Cold Storage Settings")
	
	# Priority 1: Specific Match
	for row in settings.bag_type_rates:
		if row.billing_type == billing_type and row.item_group == item_group:
			if row.goods_item and row.goods_item == goods_item:
				return flt(row.rate)
				 
	# Priority 2: Generic Match (No Goods Item)
	for row in settings.bag_type_rates:
		if row.billing_type == billing_type and row.item_group == item_group and not row.goods_item:
			return flt(row.rate)
			
	return 0.0

def get_batch_balance(linked_receipt, batch_no, current_dispatch=None):
	if not linked_receipt or not batch_no:
		return 0
	
	received_qty = frappe.db.get_value("Cold Storage Receipt Item", 
		filters={"parent": linked_receipt, "batch_no": batch_no}, 
		fieldname="number_of_bags"
	) or 0
	
	# Check dispatches
	conditions = "d_item.linked_receipt = %s AND d_item.batch_no = %s AND d.docstatus = 1"
	values = [linked_receipt, batch_no]
	
	if current_dispatch:
		conditions += " AND d.name != %s"
		values.append(current_dispatch)
		
	dispatched_qty = frappe.db.sql(f"""
		SELECT SUM(d_item.number_of_bags)
		FROM `tabCold Storage Dispatch` d
		JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = d.name
		WHERE {conditions}
	""", tuple(values))[0][0] or 0
	
	return flt(received_qty) - flt(dispatched_qty)

def get_total_batch_balance(customer, warehouse, batch_no):
	# Optimized N+1 fix: Single query aggregation
	return frappe.db.sql("""
		SELECT 
			(
				SELECT IFNULL(SUM(ri.number_of_bags), 0)
				FROM `tabCold Storage Receipt` r
				JOIN `tabCold Storage Receipt Item` ri ON ri.parent = r.name
				WHERE r.customer = %(customer)s 
				  AND r.warehouse = %(warehouse)s 
				  AND ri.batch_no = %(batch_no)s 
				  AND r.docstatus = 1
			) - (
				SELECT IFNULL(SUM(di.number_of_bags), 0)
				FROM `tabCold Storage Dispatch` d
				JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
				WHERE d.customer = %(customer)s 
				  AND di.warehouse = %(warehouse)s 
				  AND di.batch_no = %(batch_no)s 
				  AND d.docstatus = 1
			) as balance
	""", {
		"customer": customer,
		"warehouse": warehouse,
		"batch_no": batch_no
	})[0][0] or 0


import requests
import json

def send_whatsapp(number, message):
	"""
	Send WhatsApp message using configured provider settings.
	"""
	settings = frappe.get_single("Cold Storage WhatsApp Settings")
	if not settings.enabled:
		return

	if not number:
		frappe.log_error("WhatsApp Error", "No recipient number provided")
		return

	if settings.provider == "Twilio":
		send_via_twilio(settings, number, message)
	else:
		frappe.log_error("WhatsApp Error", f"Unsupported provider: {settings.provider}")

def send_via_twilio(settings, to_number, message):
	if not settings.account_sid or not settings.auth_token or not settings.sender_number:
		frappe.log_error("WhatsApp Error", "Missing Twilio credentials")
		return

	url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.account_sid}/Messages.json"
	
	# Twilio requires whatsapp: prefix
	if not to_number.startswith("whatsapp:"):
		to_number = f"whatsapp:{to_number}"
	
	from_number = settings.sender_number
	if not from_number.startswith("whatsapp:"):
		from_number = f"whatsapp:{from_number}"

	payload = {
		'From': from_number,
		'To': to_number,
		'Body': message
	}

	try:
		response = requests.post(
			url, 
			data=payload, 
			auth=(settings.account_sid, settings.auth_token)
		)
		
		if response.status_code not in [200, 201]:
			frappe.log_error("WhatsApp Twilio Error", f"Status: {response.status_code}, Response: {response.text}")
		else:
			# Optional: Log success or store message ID
			pass
			
	except Exception as e:
		frappe.log_error("WhatsApp Exception", str(e))

@frappe.whitelist()
def get_total_warehouses_count(filters=None):
	default_company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
	if not default_company:
		return 0
	return frappe.db.count("Warehouse", {
		"company": default_company,
		"disabled": 0,
		"is_group": 0
	})
@frappe.whitelist()
def get_total_outgoing_bills(filters=None):
	default_company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
	if not default_company:
		return 0
	
	from frappe.utils import getdate, nowdate
	today = getdate(nowdate())
	year_start = f"{today.year}-01-01"
	year_end = f"{today.year}-12-31"

	result = frappe.db.sql("""
		SELECT SUM(base_net_total)
		FROM `tabSales Invoice`
		WHERE company = %s
		  AND docstatus = 1
		  AND posting_date BETWEEN %s AND %s
	""", (default_company, year_start, year_end))
	
	return flt(result[0][0]) if result else 0.0
