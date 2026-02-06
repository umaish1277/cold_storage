import frappe

def get_query_condition(user):
	if not user: user = frappe.session.user

	if "System Manager" in frappe.get_roles(user) or user == "Administrator":
		return ""

	# Get companies assigned to user via User Permissions
	companies = frappe.get_all("User Permission", filters={
		"user": user,
		"allow": "Company"
	}, pluck="for_value")

	if not companies:
		# If no company is assigned, restricted users should not see anything
		return "(1=2)"

	companies_str = ", ".join([frappe.db.escape(c) for c in companies])
	return f"company in ({companies_str})"
