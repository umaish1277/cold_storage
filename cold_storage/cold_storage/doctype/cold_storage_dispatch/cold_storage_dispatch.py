import frappe
from frappe.model.document import Document
from frappe.utils import flt

@frappe.whitelist()
def get_bag_rate(bag_type):
    settings = frappe.get_single("Cold Storage Settings")
    for row in settings.bag_type_rates:
        if row.bag_type == bag_type:
            return flt(row.rate)
    return 0.0

class ColdStorageDispatch(Document):
	def validate(self):
		if not self.linked_receipt:
			frappe.throw("Please select a Linked Receipt")

		for row in self.items:
			# 1. Check if Batch exists in Receipt
			receipt_item = frappe.db.get_value("Cold Storage Receipt Item", 
				filters={"parent": self.linked_receipt, "batch_no": row.batch_no}, 
				fieldname=["number_of_bags"], 
				as_dict=True
			)
			
			if not receipt_item:
				frappe.throw(f"Batch {row.batch_no} not found in Receipt {self.linked_receipt}")

			received_qty = receipt_item.number_of_bags
			
			# 2. Calculate already dispatched quantity (Submitted Dispatches only)
			# We exclude current document using name != self.name, though self.name might be valid if updating draft
			# But we only care about SUBMITTED docs for accounting.
			dispatched_qty = frappe.db.sql("""
				SELECT SUM(d_item.number_of_bags)
				FROM `tabCold Storage Dispatch` d
				JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = d.name
				WHERE d.linked_receipt = %s 
				  AND d_item.batch_no = %s 
				  AND d.docstatus = 1
				  AND d.name != %s
			""", (self.linked_receipt, row.batch_no, self.name or "New Dispatch"), as_dict=False)[0][0] or 0
			
			available_qty = received_qty - dispatched_qty
			
			if row.number_of_bags > available_qty:
				frappe.throw(f"Row {row.idx}: Insufficient balance for Batch {row.batch_no}. Available: {available_qty}, Requested: {row.number_of_bags}")
		
		self.calculate_billing()
        
	def calculate_billing(self):
		settings = frappe.get_single("Cold Storage Settings")
		
		# Create a map of Bag Type -> Rates
		# Keys:
		# (Item, BagType) -> Specific
		# (None, BagType) -> Generic
		rate_map = {}
		if settings.bag_type_rates:
			for row in settings.bag_type_rates:
				# Use None for empty goods_item
				item_key = row.goods_item if row.goods_item else None
				key = (item_key, row.bag_type)
				
				rate_map[key] = {
					"handling": flt(row.rate),
					"loading": flt(row.loading_rate)
				}
		
		total_handling = 0
		total_loading = 0
		
		for item in self.items:
			# Fetch Rates Priority:
			# 1. Specific Match (Item + Bag)
			# 2. Generic Match (Bag only)
			
			found_rates = None
			
			# 1. Specific
			if (item.goods_item, item.bag_type) in rate_map:
				found_rates = rate_map[(item.goods_item, item.bag_type)]
			
			# 2. Generic (if not found specific)
			if not found_rates and (None, item.bag_type) in rate_map:
				found_rates = rate_map[(None, item.bag_type)]
			
			# Fallback or Defaults
			
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
			taxable_amount = self.total_amount + self.total_loading_amount
			self.total_gst_amount = taxable_amount * (flt(self.gst_rate) / 100)
		else:
			self.total_gst_amount = 0
			
		self.grand_total = self.total_amount + self.total_loading_amount + self.total_gst_amount

		# Set In Words
		from frappe.utils import money_in_words
		company_currency = frappe.get_cached_value('Company',  self.company,  'default_currency')
		self.in_words = money_in_words(self.grand_total, company_currency)

	def on_submit(self):
		# The original on_submit logic for Sales Invoice creation
		if not self.items:
			return

		# Create Sales Invoice
		si = frappe.new_doc("Sales Invoice")
		si.customer = self.customer
		si.company = self.company
		si.posting_date = self.dispatch_date
		si.due_date = self.dispatch_date
		
		receipt = frappe.get_doc("Cold Storage Receipt", self.linked_receipt)
        
		days = frappe.utils.date_diff(self.dispatch_date, receipt.receipt_date)
		if days < 1: days = 1
		
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
					"qty": row.number_of_bags * duration,
					"rate": rate,
					"description": f"Storage Charges ({billing_type}) for {row.number_of_bags} bags (Batch {row.batch_no}) {description_suffix} @ {rate}/{billing_type[:-2] if billing_type != 'Daily' else 'Day'}",
					"uom": "Nos"
				})
			
			# Loading Charge
			loading_rate = row.loading_rate or 0.0
			if loading_rate > 0:
				si.append("items", {
					"item_code": "Cold Storage Service",
					"qty": row.number_of_bags, # One time charge
					"rate": loading_rate,
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
            
		si.save()
		frappe.msgprint(f"Sales Invoice <a href='/app/sales-invoice/{si.name}'>{si.name}</a> created.")
