import frappe
from frappe.utils import getdate, nowdate, flt, format_date
from cold_storage.cold_storage import utils

def send_daily_summary():
	"""
	Scheduled task to send daily intake/outtake summary to managers via WhatsApp.
	"""
	settings = frappe.get_single("Cold Storage WhatsApp Settings")
	if not settings.enabled or not settings.daily_summary_enabled:
		return

	if not settings.summary_recipients:
		return

	today = nowdate()
	
	# 1. Aggregate Intake (Receipts)
	intake_data = frappe.db.sql("""
		SELECT COUNT(name), SUM(total_bags)
		FROM `tabCold Storage Receipt`
		WHERE receipt_date = %s AND docstatus = 1
	""", (today,))[0]
	
	total_receipts = intake_data[0] or 0
	total_intake_bags = flt(intake_data[1]) or 0

	# 2. Aggregate Outtake (Dispatches)
	outtake_data = frappe.db.sql("""
		SELECT COUNT(DISTINCT d.name), SUM(di.number_of_bags)
		FROM `tabCold Storage Dispatch` d
		JOIN `tabCold Storage Dispatch Item` di ON di.parent = d.name
		WHERE d.dispatch_date = %s AND d.docstatus = 1
	""", (today,))[0]
	
	total_dispatches = outtake_data[0] or 0
	total_outtake_bags = flt(outtake_data[1]) or 0

	# 3. Format Message
	message = f"*Daily Summary - {format_date(today)}*\n\n"
	message += f"📦 *Intake (Receipts)*\n"
	message += f"• Total Bags: {intake_data[1] or 0}\n"
	message += f"• Documents: {total_receipts}\n\n"
	
	message += f"🚚 *Outtake (Dispatches)*\n"
	message += f"• Total Bags: {outtake_data[1] or 0}\n"
	message += f"• Documents: {total_dispatches}\n\n"
	
	message += f"_Powered by Cold Storage Management System_"

	# 4. Send to Recipients
	recipients = [r.strip() for r in settings.summary_recipients.split('\n') if r.strip()]
	for number in recipients:
		utils.send_whatsapp(number, message)

	return "Summary sent to " + ", ".join(recipients)

def send_late_payment_reminders():
	"""
	Scheduled task to send WhatsApp reminders for overdue Sales Invoices.
	"""
	settings = frappe.get_single("Cold Storage WhatsApp Settings")
	if not settings.enabled or not settings.late_payment_reminders_enabled:
		return

	if not settings.late_payment_message_template:
		return

	today = nowdate()
	
	# Fetch overdue invoices: Submitted, Outstanding > 0, Due Date < Today
	overdue_invoices = frappe.get_all("Sales Invoice",
		filters={
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"due_date": ["<", today]
		},
		fields=["name", "customer", "due_date", "outstanding_amount"]
	)

	sent_count = 0
	for inv in overdue_invoices:
		# Use safe access for frappe.get_all results
		inv = frappe._dict(inv)
		
		# Get customer's mobile number
		mobile_no = frappe.db.get_value("Customer", inv.customer, "mobile_no")
		if not mobile_no:
			continue

		# Prepare message
		message = settings.late_payment_message_template.format(
			customer_name=inv.customer,
			invoice_number=inv.name,
			due_date=format_date(inv.due_date),
			outstanding_amount=inv.outstanding_amount
		)

		utils.send_whatsapp(mobile_no, message)
		sent_count += 1

	return f"Sent {sent_count} reminders"
