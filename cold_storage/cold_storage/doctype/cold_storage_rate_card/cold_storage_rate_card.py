import frappe
from frappe.model.document import Document

class ColdStorageRateCard(Document):
	def validate(self):
		if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
			frappe.throw("Valid From cannot be after Valid To")
