import frappe

@frappe.whitelist()
def get_bag_type_filter(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(f"""
		SELECT DISTINCT bag_type 
		FROM `tabCold Storage Receipt Item`
		WHERE bag_type LIKE %(txt)s
		AND docstatus = 1
		LIMIT %(page_len)s OFFSET %(start)s
	""", {
		'txt': f"%{txt}%",
		'page_len': page_len,
		'start': start
	})
