import frappe
from frappe.model.document import Document

class ColdStorageReceipt(Document):
	def validate(self):
		self.total_bags = sum([item.number_of_bags for item in self.items])


	def before_save(self):
		# Generate QR Code if not exists
		if not self.qr_code and self.name:
			import qrcode
			from frappe.utils.file_manager import save_file
			from io import BytesIO
			
			# Fetch Customer Name
			customer_name = frappe.db.get_value("Customer", self.customer, "customer_name") or self.customer
			
			# Summarize Items with Batch and Qty
			items_summary = "; ".join([f"{item.goods_item} ({item.number_of_bags} Bags, Batch: {item.batch_no})" for item in self.items])
			
			qr_data = f"Receipt: {self.name}\nCustomer: {customer_name}\nWarehouse: {self.warehouse}\nItems: {items_summary}"
			qr = qrcode.make(qr_data)
			buffered = BytesIO()
			qr.save(buffered, format="PNG")
			img_str = buffered.getvalue()
			
			filename = f"QR-{self.name}.png"
			saved_file = save_file(filename, img_str, "Cold Storage Receipt", self.name, is_private=0)
			self.qr_code = saved_file.file_url

	def on_submit(self):
		# TODO: Implement Stock Entry creation for Bags if applicable
		self.status = "Submitted"
		self.notify_customer()
		pass

	def notify_customer(self):
		if not self.customer: return

		# specific logic to find email from Contact linked to Customer
		# or use standard 'email_id' if available in Customer
		contact_email = frappe.db.get_value("Contact", {"link_doctype": "Customer", "link_name": self.customer, "is_primary_contact": 1}, "email_id")
		if not contact_email:
			 contact_email = frappe.db.get_value("Contact", {"link_doctype": "Customer", "link_name": self.customer}, "email_id")

		if contact_email:
			subject = f"Goods Received: {self.name}"
			message = f"""
				<p>Dear Customer,</p>
				<p>We have received your goods.</p>
				<ul>
					<li><b>Receipt No:</b> {self.name}</li>
					<li><b>Date:</b> {self.receipt_date}</li>
					<li><b>Total Bags:</b> {self.total_bags if hasattr(self, 'total_bags') else 'Check Document'}</li>
				</ul>
				<p>Thank you for choosing us.</p>
			"""
			frappe.sendmail(recipients=[contact_email], subject=subject, message=message)
			frappe.msgprint(f"Notification sent to {contact_email}")

	def on_cancel(self):
		# TODO: Reverse Stock Entry
		pass
