import frappe

def run():
	print("Starting Comprehensive Cold Storage Data Cleanup...")
	
	company = frappe.db.get_single_value("Cold Storage Settings", "default_company")
	if not company:
		print("Error: Default Company not found in Cold Storage Settings.")
		return

	print(f"Target Company: {company}")

	# 1. Clear Transactions
	print("Clearing Transactional Data...")
	
	# Dispatch & linked Sales Invoices
	dispatches = frappe.get_all("Cold Storage Dispatch", filters={"company": company}, fields=["name", "sales_invoice"])
	for d in dispatches:
		print(f"Deleting Dispatch: {d.name}")
		if d.sales_invoice and frappe.db.exists("Sales Invoice", d.sales_invoice):
			frappe.db.set_value("Cold Storage Dispatch", d.name, "sales_invoice", None)
			try:
				frappe.delete_doc("Sales Invoice", d.sales_invoice, ignore_permissions=True, force=True)
			except Exception as e:
				print(f"Could not delete Invoice {d.sales_invoice}: {e}")
		
		frappe.delete_doc("Cold Storage Dispatch", d.name, ignore_permissions=True, force=True)

	# Receipt & linked Stock Entries / Journals
	receipts = frappe.get_all("Cold Storage Receipt", filters={"company": company}, fields=["name", "stock_entry", "transfer_loading_journal_entry"])
	for r in receipts:
		print(f"Deleting Receipt: {r.name}")
		if r.stock_entry and frappe.db.exists("Stock Entry", r.stock_entry):
			frappe.db.set_value("Cold Storage Receipt", r.name, "stock_entry", None)
			try:
				frappe.delete_doc("Stock Entry", r.stock_entry, ignore_permissions=True, force=True)
			except Exception as e:
				print(f"Could not delete Stock Entry {r.stock_entry}: {e}")
		
		if r.transfer_loading_journal_entry and frappe.db.exists("Journal Entry", r.transfer_loading_journal_entry):
			frappe.db.set_value("Cold Storage Receipt", r.name, "transfer_loading_journal_entry", None)
			try:
				frappe.delete_doc("Journal Entry", r.transfer_loading_journal_entry, ignore_permissions=True, force=True)
			except Exception as e:
				print(f"Could not delete Journal Entry {r.transfer_loading_journal_entry}: {e}")
		
		frappe.delete_doc("Cold Storage Receipt", r.name, ignore_permissions=True, force=True)

	# 2. Clear Accounting & Ledger
	print("Clearing GL and Ledger Entries...")
	# Delete GL Entry, Stock Ledger Entry, Payment Ledger Entry for the company
	ledger_doctypes = ["GL Entry", "Stock Ledger Entry", "Payment Ledger Entry"]
	for dt in ledger_doctypes:
		count = frappe.db.sql(f"DELETE FROM `tab{dt}` WHERE company = %s", (company,))
		print(f"Deleted records from {dt}: {count}")

	# 3. Clear Master Data
	print("Clearing Master Data (Warehouses & Customers)...")
	
	warehouses = frappe.get_all("Warehouse", filters={"company": company}, fields=["name"])
	for w in warehouses:
		print(f"Deleting Warehouse: {w.name}")
		try:
			frappe.delete_doc("Warehouse", w.name, ignore_permissions=True, force=True)
		except Exception as e:
			print(f"Could not delete Warehouse {w.name}: {e}")

	customers = frappe.get_all("Customer", fields=["name"])
	for c in customers:
		print(f"Deleting Customer: {c.name}")
		try:
			frappe.delete_doc("Customer", c.name, ignore_permissions=True, force=True)
		except Exception as e:
			print(f"Could not delete Customer {c.name}: {e}")

	items = frappe.get_all("Item", fields=["name"])
	for i in items:
		print(f"Deleting Item: {i.name}")
		try:
			frappe.delete_doc("Item", i.name, ignore_permissions=True, force=True)
		except Exception as e:
			print(f"Could not delete Item {i.name}: {e}")

	item_groups = frappe.get_all("Item Group", filters={"name": ["!=", "All Item Groups"]}, fields=["name"])
	for ig in item_groups:
		print(f"Deleting Item Group: {ig.name}")
		try:
			frappe.delete_doc("Item Group", ig.name, ignore_permissions=True, force=True)
		except Exception as e:
			print(f"Could not delete Item Group {ig.name}: {e}")

	batches = frappe.get_all("Batch", fields=["name"])
	for b in batches:
		print(f"Deleting Batch: {b.name}")
		try:
			frappe.delete_doc("Batch", b.name, ignore_permissions=True, force=True)
		except Exception as e:
			print(f"Could not delete Batch {b.name}: {e}")

	# 4. Reset Naming Series
	print("Resetting Naming Series...")
	series_to_reset = ["CSR-", "CSD-"]
	for prefix in series_to_reset:
		frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s", (f"%{prefix}%",))
	
	frappe.db.commit()
	print("Comprehensive Cleanup Complete.")

if __name__ == "__main__":
	run()
