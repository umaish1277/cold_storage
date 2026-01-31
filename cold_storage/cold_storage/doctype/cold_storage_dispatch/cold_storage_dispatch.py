import frappe
from frappe.model.document import Document

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
		default_rate = settings.default_handling_charge_per_bag or 0
		
		total_handling = 0
		
		for item in self.items:
			# Set default rate if not set
			if not item.rate:
				item.rate = default_rate
				
			# Calculate item amount
			item.amount = frappe.utils.flt(item.rate) * frappe.utils.flt(item.number_of_bags)
			total_handling += item.amount
			
		self.total_amount = total_handling
		
		# Calculate GST
		if self.gst_applicable:
			 # If gst_rate is not set, maybe should error? Or assume 0.
			 rate = frappe.utils.flt(self.gst_rate)
			 self.total_gst_amount = (total_handling * rate) / 100.0
		else:
			 self.total_gst_amount = 0
			 self.gst_rate = 0
			 
		self.grand_total = self.total_amount + self.total_gst_amount

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
			
			si.append("items", {
				"item_code": "Cold Storage Service",
				"qty": row.number_of_bags * duration,
				"rate": rate,
				"description": f"Storage Charges ({billing_type}) for {row.number_of_bags} bags (Batch {row.batch_no}) {description_suffix} @ {rate}/{billing_type[:-2] if billing_type != 'Daily' else 'Day'}",
				"uom": "Nos"
			})
		
		si.set_missing_values() # Fetches taxes etc
		si.save()
		frappe.msgprint(f"Sales Invoice <a href='/app/sales-invoice/{si.name}'>{si.name}</a> created.")
