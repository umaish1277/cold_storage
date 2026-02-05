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
