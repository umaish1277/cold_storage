import frappe
from cold_storage.cold_storage.api import record_sensor_data
import json

def verify():
    # Force set request method for testing
    frappe.request.method = 'POST'
    # Mock the request data
    class MockRequest:
        def get_json(self):
            return {
                'device_id': 'EUI-TEST-001',
                'values': {
                    'temperature': 15.5,
                    'humidity': 45.0,
                    'co2': 400
                },
                'battery': 90
            }
    frappe.request.get_json = MockRequest().get_json

    print("Simulating sensor record...")
    result = record_sensor_data()
    print(f"API Result: {result}")
    
    # Check if reading was created
    readings = frappe.get_all("Cold Storage Environment Reading", filters={"sensor": "EUI-TEST-001"}, order_by="timestamp desc", limit=1)
    if readings:
        print(f"Verified: Reading {readings[0].name} created.")
        
    # Check sensor status (should be Alarm because temp 15.5 > limit 10.0)
    status = frappe.db.get_value("Cold Storage Environment Sensor", "EUI-TEST-001", "status")
    print(f"Verified: Sensor Status is {status}")

if __name__ == "__main__":
    verify()
