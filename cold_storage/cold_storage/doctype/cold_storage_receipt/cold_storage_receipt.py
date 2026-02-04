import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

class ColdStorageReceipt(Document):
	def onload(self):
		default_company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
		if not self.company:
			self.company = default_company
		self.set_onload("default_company", default_company)

	def set_missing_values(self):
		if not self.company:
			self.company = frappe.db.get_single_value("Cold Storage Settings", "default_company")

	def validate(self):
		# Server-side fallback for company if not set
		if not self.company:
			self.company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
		
		if not self.company:
			frappe.throw("Company is mandatory. Please set 'Default Company' in Cold Storage Settings.")

		from cold_storage.cold_storage import utils
		self.total_bags = sum([item.number_of_bags for item in self.items])
		
		# Validation: Check for positive number of bags
		for item in self.items:
			if item.number_of_bags <= 0:
				frappe.throw(f"Row {item.idx}: Number of Bags must be greater than 0")

		# Validation: Check for Future Date
		utils.validate_future_date(self.receipt_date, "Receipt Date")

		# Check Customer Transfer Validity
		if self.receipt_type == "Customer Transfer":
			if not self.source_receipt:
				frappe.throw("Source Receipt is mandatory for Customer Transfer.")
			
			source_doc = frappe.get_doc("Cold Storage Receipt", self.source_receipt)
			if source_doc.customer != self.from_customer:
				frappe.throw(f"Source Receipt {self.source_receipt} does not belong to the selected From Customer {self.from_customer}")
			
			if source_doc.warehouse != self.warehouse:
				frappe.throw(f"Source Receipt {self.source_receipt} is in warehouse '{source_doc.warehouse}', but current receipt is for '{self.warehouse}'. Warehouses must match.")

			# Validate Available Balance in Source Receipt
			# Global Balance Check (Optional if Batch Check is strict, but good to keep)
			dispatched_count = frappe.db.sql("""
				SELECT SUM(d_item.number_of_bags) 
				FROM `tabCold Storage Dispatch` p
				JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = p.name
				WHERE d_item.linked_receipt = %s AND p.docstatus = 1
			""", (self.source_receipt))
			
			already_dispatched = dispatched_count[0][0] or 0
			current_transfer_qty = self.total_bags
			available_qty = source_doc.total_bags - already_dispatched
			
			if current_transfer_qty > available_qty:
				frappe.throw(f"Insufficient total balance in Source Receipt {self.source_receipt}. Available: {available_qty}, Requested: {current_transfer_qty}")

			# Validate Batch-Level Availability
			from cold_storage.cold_storage.doctype.cold_storage_dispatch.cold_storage_dispatch import get_batch_balance
			for item in self.items:
				if item.batch_no:
					batch_avl = get_batch_balance(self.source_receipt, item.batch_no)
					if item.number_of_bags > batch_avl:
						frappe.throw(f"Row {item.idx}: Insufficient balance for Batch {item.batch_no}. Available: {batch_avl}, Requested: {item.number_of_bags}")

		# Link Batch to Customer
		if self.customer:
			for item in self.items:
				if item.batch_no:
					if frappe.db.exists("Batch", item.batch_no):
						batch = frappe.get_doc("Batch", item.batch_no)
						if not batch.customer:
							batch.customer = self.customer
							batch.db_set("customer", self.customer)
						elif batch.customer != self.customer:
							# Optional: Warn if batch belongs to another customer?
							pass


	def autoname(self):
		if not self.company:
			frappe.throw("Company is mandatory for naming")
		
		abbr = frappe.db.get_value("Company", self.company, "abbr")
		if not abbr:
			frappe.throw(f"Abbreviation not found for Company {self.company}")
			
		# series e.g. "CSR-.MM.-.YY.-"
		series = self.naming_series or "CSR-.MM.-.YY.-"
		
		# Prevent double prefixing if frontend already added it
		if not series.startswith(abbr):
			series = f"{abbr}-{series}"
			
		from frappe.model.naming import make_autoname
		self.name = make_autoname(f"{series}.####")

	def before_save(self):
		# Generate/Update QR Code
		if self.name:
			import qrcode
			from frappe.utils.file_manager import save_file, remove_file
			from io import BytesIO
			
			# Fetch Customer Name
			customer_name = frappe.db.get_value("Customer", self.customer, "customer_name") or self.customer
			
			# Summarize Items with Batch and Qty
			items_summary = "; ".join([f"{item.goods_item} ({item.number_of_bags} Bags, Batch: {item.batch_no})" for item in self.items])
			
			qr_data = f"Receipt: {self.name}\nCustomer: {customer_name}\nWarehouse: {self.warehouse}\nItems: {items_summary}"
			
			# Increase size (default box_size is 10, setting to 40 for very high quality/large)
			qr = qrcode.QRCode(version=1, box_size=40, border=2)
			qr.add_data(qr_data)
			qr.make(fit=True)
			img = qr.make_image(fill_color="black", back_color="white")
			
			buffered = BytesIO()
			img.save(buffered, format="PNG")
			img_str = buffered.getvalue()
			
			filename = f"QR-{self.name}.png"
			
			# Delete old file to ensure refresh
			if self.qr_code:
				try:
					# Find the File doc and remove it
					file_doc = frappe.get_all("File", filters={"file_url": self.qr_code}, fields=["name"])
					for f in file_doc:
						remove_file(f.name)
				except:
					pass

			saved_file = save_file(filename, img_str, "Cold Storage Receipt", self.name, is_private=0, df="qr_code")
			self.qr_code = saved_file.file_url

	def on_submit(self):
		if self.receipt_type == "Customer Transfer":
			self.create_transfer_dispatch(
				source_customer=self.from_customer,
				source_warehouse=self.warehouse, # Warehouse same
				billing_type="Daily" # Default/Mock or fetch from somewhere?
			)

		# Warehouse Transfer is now handled directly via Stock Entry (Material Transfer) in make_stock_entry
		if self.receipt_type == "Warehouse Transfer":
			self.make_transfer_loading_journal_entry()

		self.status = "Submitted"
		self.make_stock_entry()

		self.status = "Submitted"
		self.notify_customer()

	def make_transfer_loading_journal_entry(self):
		settings = frappe.get_single("Cold Storage Settings")
		
		# Skip if accounts are not configured
		if not settings.transfer_loading_expense_account or not settings.transfer_loading_payable_account:
			frappe.msgprint("Transfer Loading charges skipped: Expense/Payable accounts not set in Cold Storage Settings.")
			return

		# Determine rate
		is_intra = (self.from_warehouse == self.warehouse)
		rate = settings.intra_warehouse_loading_rate if is_intra else settings.inter_warehouse_loading_rate
		
		if not rate or rate <= 0:
			return

		# Calculate equated bags: 1 Jute Bag = 2 Net Bags (Net Bag = 0.5 Jute Bag equivalent)
		# Logic follows Item Group as requested
		equated_bags = 0
		for item in self.items:
			if item.item_group == "Net Bag":
				equated_bags += flt(item.number_of_bags) * 0.5
			else:
				# Default to Jute Bag (1:1) if it's Jute Bag or any other group
				equated_bags += flt(item.number_of_bags)


		amount = flt(rate) * flt(equated_bags)
		if amount <= 0:
			return

		self.transfer_loading_amount = amount

		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = self.receipt_date
		je.company = self.company
		je.remark = f"Loading Charges for Warehouse Transfer: {self.name} ({'Intra' if is_intra else 'Inter'}-Warehouse)"

		# Debit: Expense Account
		je.append("accounts", {
			"account": settings.transfer_loading_expense_account,
			"debit_in_account_currency": amount,
		})

		# Credit: Payable/Cash Account
		je.append("accounts", {
			"account": settings.transfer_loading_payable_account,
			"credit_in_account_currency": amount,
		})


		je.insert()
		je.submit()

		self.db_set("transfer_loading_journal_entry", je.name)
		self.db_set("transfer_loading_amount", amount)
		frappe.msgprint(f"Journal Entry <a href='/app/journal-entry/{je.name}'>{je.name}</a> created for transfer loading charges.")

	def make_stock_entry(self):

		if not self.items:
			return

		se = frappe.new_doc("Stock Entry")
		
		# Determine Purpose and Warehouse Logic
		if self.receipt_type == "Warehouse Transfer":
			se.purpose = "Material Transfer"
			se.from_warehouse = self.from_warehouse
			se.to_warehouse = self.warehouse
		else:
			se.purpose = "Material Receipt"
			se.to_warehouse = self.warehouse
			
		se.set_stock_entry_type()
		se.company = self.company
		se.posting_date = self.receipt_date
		se.remarks = f"Against Cold Storage Receipt: {self.name}"
		
		for item in self.items:
			item_row = {
				"item_code": item.goods_item,
				"qty": item.number_of_bags,
				"transfer_qty": item.number_of_bags,
				"batch_no": item.batch_no,
				"uom": frappe.db.get_value("Item", item.goods_item, "stock_uom") or "Nos",
				"conversion_factor": 1.0,
				"use_serial_batch_fields": 1
			}
			
			if self.receipt_type == "Warehouse Transfer":
				item_row["s_warehouse"] = self.from_warehouse
				item_row["t_warehouse"] = self.warehouse
			else:
				item_row["t_warehouse"] = self.warehouse
				item_row["basic_rate"] = 0.0
				
			se.append("items", item_row)
			
		se.set_missing_values()
		se.insert()
		se.submit()
		
		self.db_set("stock_entry", se.name)
		frappe.msgprint(f"Stock Entry <a href='/app/stock-entry/{se.name}'>{se.name}</a> created.")
		
	def create_transfer_dispatch(self, source_customer, source_warehouse, billing_type):
		# Auto-create Dispatch for the Source from SINGLE Source Receipt (for Customer Transfer)
		
		# If Customer Transfer, we use the self.source_receipt
		# If Warehouse Transfer, we might use FIFO or still need to pick receipts logic 
		# (Warehouse Transfer logic TBD strictly, but assuming FIFO or similar if no source selected)
		
		# For current scope: Customer Transfer uses self.source_receipt
		
		linked_receipt = None
		if self.receipt_type == "Customer Transfer":
			linked_receipt = self.source_receipt
		
		# If we have a specific linked receipt, valid items against it
		items_to_dispatch = []
		
		for item in self.items:
			if linked_receipt:
				# Balance check should have happened in validate()
				items_to_dispatch.append(item)
			else:
				# FIFO or Lookup Logic for Warehouse Transfer (if needed later)
				# For now, simplistic fallback or placeholder
				pass
		
		if items_to_dispatch and linked_receipt:
			dispatch = frappe.new_doc("Cold Storage Dispatch")
			dispatch.company = self.company
			dispatch.customer = source_customer
			dispatch.dispatch_date = self.receipt_date
			dispatch.billing_type = billing_type
			dispatch.remarks = f"Auto-generated Transfer to {self.customer} via Receipt {self.name}"
			
			for i in items_to_dispatch:
				dispatch.append("items", {
					"goods_item": i.goods_item,
					"item_group": i.item_group,
					"batch_no": i.batch_no,
					"number_of_bags": i.number_of_bags,
					"linked_receipt": linked_receipt,
					"warehouse": source_warehouse,
					"rate": 0
				})
			
			dispatch.insert()
			dispatch.submit()
			frappe.msgprint(f"Dispatcher {dispatch.name} created for transfer from {source_customer}.")

	def notify_customer(self):
		if not self.customer: return

		# Email Logic
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
		# Validation: Check for linked dispatches
		linked_dispatches = frappe.db.sql("""
			SELECT p.name 
			FROM `tabCold Storage Dispatch` p
			JOIN `tabCold Storage Dispatch Item` d_item ON d_item.parent = p.name
			WHERE d_item.linked_receipt = %s AND p.docstatus != 2
		""", (self.name))
		
		if linked_dispatches:
			frappe.throw(f"Cannot cancel Receipt because linked Dispatch {linked_dispatches[0][0]} exists. Please cancel the Dispatch first.")

		if self.stock_entry:
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			if se.docstatus == 1:
				se.cancel()
				frappe.msgprint(f"Stock Entry {se.name} cancelled.")

		if self.transfer_loading_journal_entry:
			je = frappe.get_doc("Journal Entry", self.transfer_loading_journal_entry)
			if je.docstatus == 1:
				je.cancel()
				frappe.msgprint(f"Journal Entry {je.name} for transfer loading charges cancelled.")


@frappe.whitelist()
def get_customer_warehouses(doctype, txt, searchfield, start, page_len, filters):
	# Returns warehouses where the specific customer has active receipts
	customer = filters.get("customer")
	if not customer:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT warehouse
		FROM `tabCold Storage Receipt`
		WHERE customer = %s AND docstatus = 1 AND warehouse LIKE %s
		LIMIT %s, %s
	""", (customer, f"%{txt}%", start, page_len))

@frappe.whitelist()
def get_receipt_items(doctype, txt, searchfield, start, page_len, filters):
	# Returns Items present in a specific Receipt
	receipt = filters.get("receipt")
	if not receipt:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT i.goods_item, i.goods_item as name
		FROM `tabCold Storage Receipt Item` i
		WHERE i.parent = %s AND i.goods_item LIKE %s
		LIMIT %s, %s
	""", (receipt, f"%{txt}%", start, page_len))

@frappe.whitelist()
def get_receipt_item_groups(doctype, txt, searchfield, start, page_len, filters):
	# Returns Item Groups present in a specific Receipt
	receipt = filters.get("receipt")
	if not receipt:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT i.item_group, i.item_group as name
		FROM `tabCold Storage Receipt Item` i
		WHERE i.parent = %s AND i.item_group LIKE %s
		LIMIT %s, %s
	""", (receipt, f"%{txt}%", start, page_len))

@frappe.whitelist()
def get_customer_warehouse_items(doctype, txt, searchfield, start, page_len, filters):
	# Returns Items for a specific customer in a specific warehouse
	customer = filters.get("customer")
	warehouse = filters.get("warehouse")
	if not customer or not warehouse:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT i.goods_item, i.goods_item as name
		FROM `tabCold Storage Receipt Item` i
		JOIN `tabCold Storage Receipt` p ON i.parent = p.name
		WHERE p.customer = %s AND p.warehouse = %s AND p.docstatus = 1 AND i.goods_item LIKE %s
		LIMIT %s, %s
	""", (customer, warehouse, f"%{txt}%", start, page_len))

@frappe.whitelist()
def get_customer_warehouse_item_groups(doctype, txt, searchfield, start, page_len, filters):
	# Returns Item Groups for a specific customer in a specific warehouse
	customer = filters.get("customer")
	warehouse = filters.get("warehouse")
	if not customer or not warehouse:
		return []

	return frappe.db.sql(f"""
		SELECT DISTINCT i.item_group, i.item_group as name
		FROM `tabCold Storage Receipt Item` i
		JOIN `tabCold Storage Receipt` p ON i.parent = p.name
		WHERE p.customer = %s AND p.warehouse = %s AND p.docstatus = 1 AND i.item_group LIKE %s
		LIMIT %s, %s
	""", (customer, warehouse, f"%{txt}%", start, page_len))
