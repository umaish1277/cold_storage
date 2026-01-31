import frappe
from frappe.model.document import Document

class ColdStorageDispatch(Document):
	def validate(self):
		pass

	def on_submit(self):
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
