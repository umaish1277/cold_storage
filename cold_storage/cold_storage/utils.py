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

@frappe.whitelist()
def get_active_batches_count(filters=None):
    return frappe.db.sql("""
        SELECT COUNT(*) FROM (
            SELECT c.batch_no, SUM(c.qty) as balance FROM (
                SELECT ri.batch_no, ri.number_of_bags as qty
                FROM `tabCold Storage Receipt Item` ri
                JOIN `tabCold Storage Receipt` r ON ri.parent = r.name
                WHERE r.docstatus = 1
                
                UNION ALL
                
                SELECT di.batch_no, -di.number_of_bags as qty
                FROM `tabCold Storage Dispatch Item` di
                JOIN `tabCold Storage Dispatch` d ON di.parent = d.name
                WHERE d.docstatus = 1
            ) c
            GROUP BY c.batch_no
            HAVING SUM(c.qty) > 0
        ) as active_batches
    """)[0][0]
