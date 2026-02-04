import frappe
from frappe.model.naming import make_autoname

def run():
	print("Starting Cold Storage Data Cleanup...")
	
	# 1. Clear Cold Storage Dispatch and linked Sales Invoices
	dispatches = frappe.get_all("Cold Storage Dispatch", fields=["name", "docstatus", "sales_invoice"])
	for d in dispatches:
		print(f"Processing Dispatch: {d.name}")
		if d.docstatus == 1:
			doc = frappe.get_doc("Cold Storage Dispatch", d.name)
			doc.cancel()
		
	# 1. Clear Cold Storage Dispatch and linked Sales Invoices
	dispatches = frappe.get_all("Cold Storage Dispatch", fields=["name", "docstatus", "sales_invoice"])
	for d in dispatches:
		print(f"Processing Dispatch: {d.name}")
		if d.docstatus == 1:
			doc = frappe.get_doc("Cold Storage Dispatch", d.name)
			try:
				doc.cancel()
			except Exception as e:
				print(f"Failed to cancel Dispatch {d.name}: {e}")
		
		# Delete Sales Invoice if exists
		if d.sales_invoice:
			if frappe.db.exists("Sales Invoice", d.sales_invoice):
				si = frappe.get_doc("Sales Invoice", d.sales_invoice)
				if si.docstatus == 1:
					try:
						si.cancel()
					except Exception as e:
						print(f"Failed to cancel Invoice {d.sales_invoice}: {e}")
				
				# Clear the link first to avoid circular dependency check
				frappe.db.set_value("Cold Storage Dispatch", d.name, "sales_invoice", None)
				try:
					frappe.delete_doc("Sales Invoice", d.sales_invoice, ignore_permissions=True)
				except Exception as e:
					print(f"Failed to delete Invoice {d.sales_invoice}: {e}")
		
		try:
			frappe.delete_doc("Cold Storage Dispatch", d.name, ignore_permissions=True)
		except Exception as e:
			print(f"Failed to delete Dispatch {d.name}: {e}")

	# 2. Clear Cold Storage Receipt and linked Stock Entries / Journal Entries
	receipts = frappe.get_all("Cold Storage Receipt", fields=["name", "docstatus", "stock_entry", "transfer_loading_journal_entry"])
	for r in receipts:
		print(f"Processing Receipt: {r.name}")
		if r.docstatus == 1:
			doc = frappe.get_doc("Cold Storage Receipt", r.name)
			try:
				doc.cancel()
			except Exception as e:
				print(f"Failed to cancel Receipt {r.name}: {e}")
		
		# Ensure linked docs are deleted
		if r.stock_entry and frappe.db.exists("Stock Entry", r.stock_entry):
			se = frappe.get_doc("Stock Entry", r.stock_entry)
			if se.docstatus == 1: 
				try:
					se.cancel()
				except Exception as e:
					print(f"Failed to cancel Stock Entry {r.stock_entry}: {e}")
			try:
				frappe.delete_doc("Stock Entry", r.stock_entry, ignore_permissions=True)
			except Exception as e:
				print(f"Failed to delete Stock Entry {r.stock_entry}: {e}")
			
		if r.transfer_loading_journal_entry and frappe.db.exists("Journal Entry", r.transfer_loading_journal_entry):
			je = frappe.get_doc("Journal Entry", r.transfer_loading_journal_entry)
			if je.docstatus == 1:
				try:
					je.cancel()
				except Exception as e:
					print(f"Failed to cancel Journal Entry {r.transfer_loading_journal_entry}: {e}")
			try:
				frappe.delete_doc("Journal Entry", r.transfer_loading_journal_entry, ignore_permissions=True)
			except Exception as e:
				print(f"Failed to delete Journal Entry {r.transfer_loading_journal_entry}: {e}")

		try:
			frappe.delete_doc("Cold Storage Receipt", r.name, ignore_permissions=True)
		except Exception as e:
			print(f"Failed to delete Receipt {r.name}: {e}")

	# 3. Reset Naming Series
	# We need to find the series used and reset them in tabSeries
	# Usually they are like 'CS-CSR-.MM.-.YY.-' or similar
	# We can just clear the whole tabSeries or specific ones if we know the keys.
	# Better: Reset for 'CSR-', 'CSD-' prefixes
	
	series_to_reset = ["CSR-", "CSD-"]
	for prefix in series_to_reset:
		# Use wildcard to catch Company-prefixed series like 'CS-CSR-'
		count = frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s", (f"%{prefix}%",))
		print(f"Reset {count} series entries for {prefix}")
	
	# Also clear Global Defaults or other naming states if needed
	# But tabSeries is the main one for .#### naming
	
	frappe.db.commit()
	print("Cleanup Complete. Cold Storage is now fresh for data entry.")

if __name__ == "__main__":
	run()
