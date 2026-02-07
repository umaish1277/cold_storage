import frappe
from cold_storage.get_customer_items_query import get_customer_batches
from cold_storage.api.permission import get_query_condition

def test():
    print("Starting verification tests...")
    
    # 1. Test get_customer_batches
    print("\n1. Testing get_customer_batches...")
    # Get a real customer for testing
    customer = frappe.db.get_value("Customer", {}, "name")
    if not customer:
        print("SKIP: No customer found in database")
    else:
        try:
            # Simulate a call from the frontend
            results = get_customer_batches("Batch", "", "batch_no", 0, 20, {"customer": customer})
            print(f"SUCCESS: get_customer_batches returned {len(results)} results for customer {customer}")
        except Exception as e:
            print(f"FAILED: get_customer_batches raised an error: {str(e)}")

    # 2. Test get_query_condition for Batch (should return "")
    print("\n2. Testing get_query_condition for Batch...")
    try:
        # Mocking frappe.local.form_dict
        frappe.local.form_dict.doctype = "Batch"
        condition = get_query_condition("Administrator")
        print(f"Condition for Batch: '{condition}'")
        if condition == "":
            print("SUCCESS: get_query_condition correctly returned empty string for Batch")
        else:
            print(f"FAILED: Expected empty string, got '{condition}'")
    except Exception as e:
        print(f"FAILED: get_query_condition raised an error: {str(e)}")
    finally:
        if 'doctype' in frappe.local.form_dict:
            del frappe.local.form_dict['doctype']

    # 3. Test get_query_condition for Customer (should return company filter)
    print("\n3. Testing get_query_condition for Customer...")
    try:
        frappe.local.form_dict.doctype = "Customer"
        # Using a non-admin user might return a filter or (1=2)
        condition = get_query_condition("Administrator")
        print(f"Condition for Customer (Admin): '{condition}'")
        if condition == "":
             print("SUCCESS: get_query_condition correctly returned empty string for Admin on Customer")
        else:
             print(f"FAILED: Expected empty string for Admin, got '{condition}'")
    except Exception as e:
        print(f"FAILED: get_query_condition raised an error: {str(e)}")
    finally:
        if 'doctype' in frappe.local.form_dict:
            del frappe.local.form_dict['doctype']

    print("\nVerification tests completed.")

if __name__ == "__main__":
    test()
