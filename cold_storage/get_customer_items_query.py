
import frappe

@frappe.whitelist()
def get_customer_batches(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	item_group = filters.get("item_group")
	goods_item = filters.get("goods_item")
	warehouse = filters.get("warehouse")
	linked_receipt = filters.get("linked_receipt")
	
	if not customer:
		return []

	conditions = ["p.customer = %(customer)s", "p.docstatus = 1"]
	values = {"customer": customer, "txt": f"%{txt}%"}
	
	if linked_receipt:
		conditions.append("p.name = %(linked_receipt)s")
		values["linked_receipt"] = linked_receipt
	
	if warehouse:
		conditions.append("p.warehouse = %(warehouse)s")
		values["warehouse"] = warehouse

	if goods_item:
		conditions.append("c.goods_item = %(goods_item)s")
		values["goods_item"] = goods_item

	if item_group:
		conditions.append("c.item_group = %(item_group)s")
		values["item_group"] = item_group
		
	conditions.append("c.batch_no LIKE %(txt)s")
	
	where_clause = " AND ".join(conditions)

	return frappe.db.sql(f"""
		SELECT DISTINCT c.batch_no
		FROM `tabCold Storage Receipt` p
		JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
		WHERE {where_clause}
		LIMIT %(start)s, %(page_len)s
	""", {**values, "start": start, "page_len": page_len})

@frappe.whitelist()
def get_customer_items(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	warehouse = filters.get("warehouse")
	linked_receipt = filters.get("linked_receipt")
	
	if not customer:
		return []

	conditions = ["p.customer = %(customer)s", "p.docstatus = 1"]
	values = {"customer": customer, "txt": f"%{txt}%"}
	
	if linked_receipt:
		conditions.append("p.name = %(linked_receipt)s")
		values["linked_receipt"] = linked_receipt

	if warehouse:
		conditions.append("p.warehouse = %(warehouse)s")
		values["warehouse"] = warehouse

	conditions.append("c.goods_item LIKE %(txt)s")
	
	where_clause = " AND ".join(conditions)

	return frappe.db.sql(f"""
		SELECT DISTINCT c.goods_item
		FROM `tabCold Storage Receipt` p
		JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
		WHERE {where_clause}
		LIMIT %(start)s, %(page_len)s
	""", {**values, "start": start, "page_len": page_len})

@frappe.whitelist()
def get_customer_item_groups(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	goods_item = filters.get("goods_item")
	warehouse = filters.get("warehouse")
	linked_receipt = filters.get("linked_receipt")
	
	if not customer:
		return []

	conditions = ["p.customer = %(customer)s", "p.docstatus = 1"]
	values = {"customer": customer, "txt": f"%{txt}%"}
	
	if linked_receipt:
		conditions.append("p.name = %(linked_receipt)s")
		values["linked_receipt"] = linked_receipt

	if warehouse:
		conditions.append("p.warehouse = %(warehouse)s")
		values["warehouse"] = warehouse

	if goods_item:
		conditions.append("c.goods_item = %(goods_item)s")
		values["goods_item"] = goods_item

	conditions.append("c.item_group LIKE %(txt)s")
	
	where_clause = " AND ".join(conditions)

	return frappe.db.sql(f"""
		SELECT DISTINCT c.item_group
		FROM `tabCold Storage Receipt` p
		JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
		WHERE {where_clause}
		LIMIT %(start)s, %(page_len)s
	""", {**values, "start": start, "page_len": page_len})

@frappe.whitelist()
def get_customer_warehouses(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	if not customer:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT warehouse
		FROM `tabCold Storage Receipt`
		WHERE customer = %(customer)s AND docstatus = 1 AND warehouse LIKE %(txt)s
		LIMIT %(start)s, %(page_len)s
	""", {"customer": customer, "txt": f"%{txt}%", "start": start, "page_len": page_len})

@frappe.whitelist()
def get_receipt_warehouses(doctype, txt, searchfield, start, page_len, filters):
	linked_receipt = filters.get("linked_receipt")
	if not linked_receipt:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT warehouse
		FROM `tabCold Storage Receipt`
		WHERE name = %(linked_receipt)s AND docstatus = 1 AND warehouse LIKE %(txt)s
		LIMIT %(start)s, %(page_len)s
	""", {"linked_receipt": linked_receipt, "txt": f"%{txt}%", "start": start, "page_len": page_len})
