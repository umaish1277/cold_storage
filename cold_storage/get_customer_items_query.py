import frappe

@frappe.whitelist()
def get_customer_batches(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	company = filters.get("company")
	linked_receipt = filters.get("linked_receipt")
	warehouse = filters.get("warehouse")
	goods_item = filters.get("goods_item")
	item_group = filters.get("item_group")

	if not customer:
		return []

	# Case 1: Complex search based on receipt history (for Transfers)
	if linked_receipt or warehouse or goods_item or item_group:
		f = {"docstatus": 1, "customer": customer}
		if company: f["company"] = company
		if linked_receipt: f["name"] = linked_receipt
		if warehouse: f["warehouse"] = warehouse
		
		# Inner filters for child table
		item_f = {}
		if goods_item: item_f["goods_item"] = goods_item
		if item_group: item_f["item_group"] = item_group
		if txt: item_f["batch_no"] = ["like", f"%{txt}%"]
		
		# We still use SQL for the complex join case as it's cleaner than nested get_all
		results = frappe.get_all("Cold Storage Receipt Item", 
			filters={**item_f, "parent": ["in", frappe.get_all("Cold Storage Receipt", filters=f, pluck="name")]},
			fields=["batch_no"],
			distinct=True,
			start=start, page_length=page_len, as_list=1
		)
		return [[r[0], r[0]] for r in results if r[0]]

	# Case 2: Simple search based on Batch table (preferred for New Receipt)
	f = {"customer": customer}
	if company: f["company"] = company
	if txt: f["name"] = ["like", f"%{txt}%"]

	batches = frappe.get_all("Batch", filters=f, fields=["name"], start=start, page_length=page_len, as_list=1)
	return [[b[0], b[0]] for b in batches]

@frappe.whitelist()
def get_customer_items(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	if not customer: return []
	
	f = {"customer": customer, "docstatus": 1}
	if filters.get("company"): f["company"] = filters.get("company")
	if filters.get("linked_receipt"): f["name"] = filters.get("linked_receipt")
	if filters.get("warehouse"): f["warehouse"] = filters.get("warehouse")
	
	receipts = frappe.get_all("Cold Storage Receipt", filters=f, pluck="name")
	if not receipts: return []
	
	item_f = {"parent": ["in", receipts]}
	if txt: item_f["goods_item"] = ["like", f"%{txt}%"]
	
	items = frappe.get_all("Cold Storage Receipt Item", filters=item_f, fields=["goods_item"], distinct=True, as_list=1)
	return [[i[0], i[0]] for i in items]

@frappe.whitelist()
def get_customer_item_groups(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	if not customer: return []
	
	f = {"customer": customer, "docstatus": 1}
	if filters.get("company"): f["company"] = filters.get("company")
	if filters.get("linked_receipt"): f["name"] = filters.get("linked_receipt")
	if filters.get("warehouse"): f["warehouse"] = filters.get("warehouse")
	
	receipts = frappe.get_all("Cold Storage Receipt", filters=f, pluck="name")
	if not receipts: return []
	
	item_f = {"parent": ["in", receipts]}
	if filters.get("goods_item"): item_f["goods_item"] = filters.get("goods_item")
	if txt: item_f["item_group"] = ["like", f"%{txt}%"]
	
	groups = frappe.get_all("Cold Storage Receipt Item", filters=item_f, fields=["item_group"], distinct=True, as_list=1)
	return [[g[0], g[0]] for g in groups]

@frappe.whitelist()
def get_customer_warehouses(doctype, txt, searchfield, start, page_len, filters):
	customer = filters.get("customer")
	if not customer: return []
	
	f = {"customer": customer, "docstatus": 1}
	if filters.get("company"): f["company"] = filters.get("company")
	if txt: f["warehouse"] = ["like", f"%{txt}%"]
	
	warehouses = frappe.get_all("Cold Storage Receipt", filters=f, fields=["warehouse"], distinct=True, as_list=1)
	return [[w[0], w[0]] for w in warehouses]

@frappe.whitelist()
def get_receipt_warehouses(doctype, txt, searchfield, start, page_len, filters):
	receipt = filters.get("linked_receipt")
	if not receipt: return []
	
	f = {"name": receipt, "docstatus": 1}
	if txt: f["warehouse"] = ["like", f"%{txt}%"]
	
	warehouses = frappe.get_all("Cold Storage Receipt", filters=f, fields=["warehouse"], distinct=True, as_list=1)
	return [[w[0], w[0]] for w in warehouses]
