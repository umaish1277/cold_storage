import frappe
from frappe.model.document import Document

class ColdStorageReceipt(Document):
	def validate(self):
		pass

	def on_submit(self):
		# TODO: Implement Stock Entry creation for Bags if applicable
		pass

	def on_cancel(self):
		# TODO: Reverse Stock Entry
		pass
