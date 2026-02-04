import frappe
from frappe.model.document import Document
from frappe.utils import flt

from cold_storage.cold_storage import utils

@frappe.whitelist()
def get_bag_rate(item_group, billing_type, goods_item=None):
	return utils.get_bag_rate(item_group, billing_type, goods_item)

@frappe.whitelist()
def get_batch_balance(linked_receipt, batch_no, current_dispatch=None):
	return utils.get_batch_balance(linked_receipt, batch_no, current_dispatch)

@frappe.whitelist()
def get_total_batch_balance(customer, warehouse, batch_no):
	return utils.get_total_batch_balance(customer, warehouse, batch_no)


class ColdStorageDispatch(Document):
	def onload(self):
		default_company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
		if not self.company:
			self.company = default_company
		self.set_onload("default_company", default_company)

	def set_missing_values(self):
		if not self.company:
			self.company = frappe.db.get_single_value("Cold Storage Settings", "default_company")

	def autoname(self):
		if not self.company:
			frappe.throw("Company is mandatory for naming")
			
		if not frappe.db.exists("Company", self.company):
			frappe.throw(f"Invalid Company: '{self.company}'. Please verify 'Default Company' in Cold Storage Settings.")

		
		abbr = frappe.db.get_value("Company", self.company, "abbr")
		if not abbr:
			frappe.throw(f"Abbreviation not found for Company {self.company}")
			
		# series e.g. "CSD-.YYYY.-"
		series = self.naming_series or "CSD-.YYYY.-"
		
		# Prevent double prefixing if frontend already added it
		if not series.startswith(abbr):
			series = f"{abbr}-{series}"
		
		from frappe.model.naming import make_autoname
		self.name = make_autoname(f"{series}.####")

	def validate(self):
		# Server-side fallback for company if not set
		if not self.company:
			self.company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
		
		if not self.company:
			frappe.throw("Company is mandatory. Please set 'Default Company' in Cold Storage Settings.")

		# Validation: Check for Future Date
		utils.validate_future_date(self.dispatch_date, "Dispatch Date")
             
		for row in self.items:
			if not row.linked_receipt:
				frappe.throw(f"Row {row.idx}: Please select a Linked Receipt")
			
			if not row.warehouse:
				frappe.throw(f"Row {row.idx}: Please select a Warehouse")
			
			if row.number_of_bags <= 0:
				frappe.throw(f"Row {row.idx}: Number of Bags must be greater than 0")

			# 1. Check if Batch exists in Receipt
			# Optimized: Using shared balance logic
			available_qty = get_batch_balance(row.linked_receipt, row.batch_no, self.name)
			
			if row.number_of_bags > available_qty:
				frappe.throw(f"Row {row.idx}: Insufficient balance for Batch {row.batch_no}. Available: {available_qty}, Requested: {row.number_of_bags}")
		
		self.calculate_billing()
        
	def calculate_billing(self):
		settings = frappe.get_single("Cold Storage Settings")
		
		# Create a map of Item Group -> Rates
		# Keys:
		# (Item, ItemGroup, BillingType) -> Specific
		# (None, ItemGroup, BillingType) -> Generic
		rate_map = {}
		if settings.bag_type_rates:
			for row in settings.bag_type_rates:
				# Use None for empty goods_item
				item_key = row.goods_item if row.goods_item else None
				key = (item_key, row.item_group, row.billing_type)
				
				rate_map[key] = {
					"handling": flt(row.rate),
					"loading": flt(row.loading_rate)
				}
		
		total_handling = 0
		total_loading = 0
		
		billing_type = self.billing_type
		
		for item in self.items:
			# Fetch Rates Priority:
			# 1. Specific Match (Item + ItemGroup + Billing)
			# 2. Generic Match (ItemGroup + Billing)
			
			found_rates = None
			
			# 1. Specific
			if (item.goods_item, item.item_group, billing_type) in rate_map:
				found_rates = rate_map[(item.goods_item, item.item_group, billing_type)]
			
			# 2. Generic (if not found specific)
			if not found_rates and (None, item.item_group, billing_type) in rate_map:
				found_rates = rate_map[(None, item.item_group, billing_type)]
			
			# Fallback or Defaults
			if not item.rate:
				item.rate = found_rates["handling"] if found_rates else 0.0
			
			if not item.loading_rate:
				item.loading_rate = found_rates["loading"] if found_rates else 0.0
			
			# Calculate item amounts
			item.amount = flt(item.rate) * flt(item.number_of_bags)
			item.loading_amount = flt(item.loading_rate) * flt(item.number_of_bags)
			
			total_handling += item.amount
			total_loading += item.loading_amount
			
		self.total_amount = total_handling
		self.total_loading_amount = total_loading
		
		# GST API
		if self.gst_applicable:
			# GST applies to both? Usually yes on services.
			taxable_amount = flt(self.total_amount) + flt(self.total_loading_amount)
			self.total_gst_amount = taxable_amount * (flt(self.gst_rate) / 100)
		else:
			self.total_gst_amount = 0
			
		self.grand_total = flt(self.total_amount) + flt(self.total_loading_amount) + flt(self.total_gst_amount)

		# Set In Words
		from frappe.utils import money_in_words
		company_currency = frappe.get_cached_value('Company',  self.company,  'default_currency')
		self.in_words = money_in_words(self.grand_total, company_currency)



	def make_stock_entry(self):
		if not self.items:
			return

		# Amendment Handling
		old_se = None
		if self.amended_from:
			old_se = frappe.db.get_value("Cold Storage Dispatch", self.amended_from, "stock_entry")

		# Group items by warehouse for separate stock entries
		warehouse_items = {}
		for item in self.items:
			if item.warehouse not in warehouse_items:
				warehouse_items[item.warehouse] = []
			warehouse_items[item.warehouse].append(item)
		
		stock_entries = []
		for warehouse, items in warehouse_items.items():
			se = frappe.new_doc("Stock Entry")
			
			if old_se and frappe.db.exists("Stock Entry", old_se):
				se.amended_from = old_se
				# Only use amended_from for the first SE created if there are multiple warehouses
				# This is a simplification; usually dispatches are from one warehouse anyway in this app context
				old_se = None 
			se.purpose = "Material Issue"
			se.set_stock_entry_type()
			se.from_warehouse = warehouse
			se.company = self.company
			se.posting_date = self.dispatch_date
			se.remarks = f"Against Cold Storage Dispatch: {self.name}"
			
			for item in items:
				se.append("items", {
					"item_code": item.goods_item,
					"s_warehouse": warehouse,
					"qty": item.number_of_bags,
					"transfer_qty": item.number_of_bags,
					"batch_no": item.batch_no,
					"uom": frappe.db.get_value("Item", item.goods_item, "stock_uom") or "Nos",
					"conversion_factor": 1.0,
					"use_serial_batch_fields": 1
				})
				
			se.set_missing_values()
			se.insert()
			se.submit()
			stock_entries.append(se.name)
		
		# Store first stock entry (for backward compatibility)
		if stock_entries:
			self.db_set("stock_entry", stock_entries[0])
			frappe.msgprint(f"Stock Entry(s) created: {', '.join([f'<a href=\'/app/stock-entry/{se}\'>{se}</a>' for se in stock_entries])}")

	def on_submit(self):
		self.make_stock_entry()
		# The original on_submit logic for Sales Invoice creation
		if not self.items:
			return

		# Create Sales Invoice
		si = frappe.new_doc("Sales Invoice")
		si.customer = self.customer
		si.company = self.company
		si.posting_date = self.dispatch_date
		si.due_date = self.dispatch_date
		si.set_posting_time = 1
		si.currency = frappe.get_cached_value('Company', self.company, 'default_currency')
		
		# Get first item's receipt for billing calculation
		first_receipt = self.items[0].linked_receipt if self.items else None
		if first_receipt:
			receipt = frappe.get_doc("Cold Storage Receipt", first_receipt)
			days = frappe.utils.date_diff(self.dispatch_date, receipt.receipt_date)
			if days < 1: days = 1
		else:
			days = 1
		
		# Billing Calculation
		billing_type = self.billing_type
		duration = days
		description_suffix = f"for {days} days"

		if billing_type == "Monthly":
			import math
			duration = math.ceil(days / 30)
			description_suffix = f"for {duration} months ({days} days)"
		elif billing_type == "Seasonal":
			duration = 1
			description_suffix = f"for Season ({days} days)"

		# Ensure service item exists
		if not frappe.db.exists("Item", "Cold Storage Service"):
			item = frappe.new_doc("Item")
			item.item_code = "Cold Storage Service"
			item.item_group = "Services"
			item.is_stock_item = 0
			item.save()

		for row in self.items:
			rate = row.rate or 0.0
			
			if rate > 0:
				si.append("items", {
					"item_code": "Cold Storage Service",
					"qty": flt(row.number_of_bags) * flt(duration),
					"rate": flt(rate),
					"description": f"Storage Charges ({billing_type}) for {row.number_of_bags} bags (Batch {row.batch_no}) {description_suffix} @ {rate}/{billing_type[:-2] if billing_type != 'Daily' else 'Day'}",
					"uom": "Nos"
				})
			
			# Loading Charge
			loading_rate = row.loading_rate or 0.0
			if loading_rate > 0:
				si.append("items", {
					"item_code": "Cold Storage Service",
					"qty": flt(row.number_of_bags), # One time charge
					"rate": flt(loading_rate),
					"description": f"Loading/Unloading Charges for {row.number_of_bags} bags (Batch {row.batch_no}) @ {loading_rate}/Bag",
					"uom": "Nos"
				})
		
		si.set_missing_values() # Fetches taxes from template if any
        
        # Add GST on Services if applicable
		if self.gst_applicable:
			settings = frappe.get_single("Cold Storage Settings")
			if not settings.gst_on_services_account:
				frappe.throw("Please configure 'GST on Services Account' in Cold Storage Settings")
				
			si.append("taxes", {
				"charge_type": "On Net Total",
				"account_head": settings.gst_on_services_account,
				"rate": self.gst_rate,
				"description": "GST on Services",
                "cost_center": si.company # Or fetch default
			})
		
		# Reset totals to prevent NoneType error in validation
		si.base_grand_total = 0.0
		si.grand_total = 0.0
		si.base_rounded_total = 0.0
		si.rounded_total = 0.0
		si.base_net_total = 0.0

		if si.items:
			try:
				si.save()
				si.submit()
			except Exception as e:
				frappe.msgprint(f"Warning: Sales Invoice {si.name} was created but could not be auto-submitted. Error: {str(e)}")
		
			# Link Invoice to Dispatch
			self.db_set("sales_invoice", si.name)
			
			# Send Notification
			self.notify_customer(si.grand_total)
			
			frappe.msgprint(f"Sales Invoice <a href='/app/sales-invoice/{si.name}'>{si.name}</a> created and submitted.")

	def notify_customer(self, amount):
		if not self.customer: return
		
		# Email Logic
		contact_email = frappe.db.get_value("Contact", {"link_doctype": "Customer", "link_name": self.customer, "is_primary_contact": 1}, "email_id")
		if not contact_email:
				contact_email = frappe.db.get_value("Contact", {"link_doctype": "Customer", "link_name": self.customer}, "email_id")

		if contact_email:
			subject = f"Goods Dispatched: {self.name}"
			message = f"""
				<p>Dear Customer,</p>
				<p>Your goods have been dispatched.</p>
				<ul>
					<li><b>Dispatch No:</b> {self.name}</li>
					<li><b>Date:</b> {self.dispatch_date}</li>
					<li><b>Total Amount:</b> {frappe.format(amount, currency=self.currency) if amount else 'N/A'}</li>
				</ul>
				<p>The invoice has been generated.</p>
				<p>Thank you.</p>
			"""
			frappe.sendmail(recipients=[contact_email], subject=subject, message=message)
	def on_cancel(self):
		if self.stock_entry:
			try:
				se = frappe.get_doc("Stock Entry", self.stock_entry)
				if se.docstatus == 1:
					se.cancel()
					frappe.msgprint(_("Linked Stock Entry {0} cancelled").format(se.name))
			except Exception as e:
				frappe.msgprint(_("Note: Linked Stock Entry {0} could not be automatically cancelled: {1}").format(self.stock_entry, str(e)))

		if self.sales_invoice:
			try:
				si = frappe.get_doc("Sales Invoice", self.sales_invoice)
				if si.docstatus == 1:
					si.cancel()
					frappe.msgprint(_("Linked Sales Invoice {0} cancelled").format(si.name))
			except Exception as e:
				frappe.msgprint(_("Note: Linked Sales Invoice {0} could not be automatically cancelled: {1}").format(self.sales_invoice, str(e)))






@frappe.whitelist()
def get_customer_batches(doctype, txt, searchfield, start, page_len, filters):
	# Returns Batches available for a specific customer
	customer = filters.get("customer")
	receipt = filters.get("receipt")
	warehouse = filters.get("warehouse")
	goods_item = filters.get("goods_item")
	item_group = filters.get("item_group")
	
	if not customer:
		return []

	conditions = "p.customer = %s AND p.docstatus = 1"
	values = [customer]
	
	if receipt:
		conditions += " AND p.name = %s"
		values.append(receipt)
	
	if warehouse:
		conditions += " AND p.warehouse = %s"
		values.append(warehouse)

	if goods_item:
		conditions += " AND c.goods_item = %s"
		values.append(goods_item)

	if item_group:
		conditions += " AND c.item_group = %s"
		values.append(item_group)
		
	conditions += " AND c.batch_no IS NOT NULL AND c.batch_no != '' AND c.batch_no LIKE %s"
	values.append(f"%{txt}%")

	# Fetch candidates
	data = frappe.db.sql(f"""
		SELECT DISTINCT c.batch_no
		FROM `tabCold Storage Receipt` p
		JOIN `tabCold Storage Receipt Item` c ON c.parent = p.name
		WHERE {conditions}
		LIMIT %s, %s
	""", tuple(values + [start, page_len]), as_dict=True)

	results = []
	for row in data:
		balance = 0
		if receipt:
			balance = get_batch_balance(receipt, row.batch_no)
		elif warehouse and customer:
			balance = get_total_batch_balance(customer, warehouse, row.batch_no)
		
		# Return format: [Value, Description/Label]
		# Use pipe separator for clear distinction
		label = f"{row.batch_no} | Avl: {balance}" if (receipt or warehouse) else row.batch_no
		results.append([row.batch_no, label])
		
	return results


