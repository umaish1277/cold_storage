import frappe
import json
from frappe import _
from frappe.utils import now_datetime, flt
from cold_storage.cold_storage import utils

@frappe.whitelist(allow_guest=True)
def record_sensor_data():
    """
    Webhook endpoint for SenseCAP / LoRaWAN gateway.
    Expected JSON payload structure (example):
    {
        "device_id": "EUI-12345678",
        "values": {
            "temperature": 25.4,
            "humidity": 60.5,
            "co2": 450
        },
        "battery": 85
    }
    """
    if frappe.request.method != "POST":
        frappe.throw(_("Connect with POST"), frappe.PermissionError)

    try:
        data = frappe.request.get_json()
    except Exception:
        frappe.throw(_("Invalid JSON payload"), frappe.ValidationError)

    if not data or not data.get("device_id"):
        return {"status": "error", "message": "Missing device_id"}

    device_id = data.get("device_id")
    values = data.get("values", {})
    battery = data.get("battery")

    # Find sensor
    sensor_name = frappe.db.get_value("Cold Storage Environment Sensor", {"sensor_id": device_id}, "name")
    
    if not sensor_name:
        # Auto-create sensor if not exists? Maybe later. For now, log error.
        frappe.log_error("IoT Alert", f"Record received for unknown sensor ID: {device_id}")
        return {"status": "error", "message": f"Sensor {device_id} not registered"}

    sensor = frappe.get_doc("Cold Storage Environment Sensor", sensor_name)
    
    # Record reading
    reading = frappe.get_doc({
        "doctype": "Cold Storage Environment Reading",
        "sensor": sensor.name,
        "timestamp": now_datetime(),
        "temperature": flt(values.get("temperature")),
        "humidity": flt(values.get("humidity")),
        "co2": flt(values.get("co2"))
    })
    reading.insert(ignore_permissions=True)

    # Update sensor status
    sensor.battery_percentage = flt(battery)
    sensor.last_reading = reading.timestamp
    sensor.status = "Online"
    
    # Check Alerts
    check_thresholds_and_alert(sensor, reading)
    
    sensor.save(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "reading": reading.name}

def check_thresholds_and_alert(sensor, reading):
    alerts = []
    
    # Temperature
    if sensor.temperature_limit_high and reading.temperature > sensor.temperature_limit_high:
        alerts.append(f"🌡 High Temperature: {reading.temperature}°C (Limit: {sensor.temperature_limit_high}°C)")
    elif sensor.temperature_limit_low and reading.temperature < sensor.temperature_limit_low:
        alerts.append(f"❄ Low Temperature: {reading.temperature}°C (Limit: {sensor.temperature_limit_low}°C)")
        
    # Humidity
    if sensor.humidity_limit_high and reading.humidity > sensor.humidity_limit_high:
        alerts.append(f"💧 High Humidity: {reading.humidity}% (Limit: {sensor.humidity_limit_high}%)")
        
    # CO2
    if sensor.co2_limit_high and reading.co2 > sensor.co2_limit_high:
        alerts.append(f"🌫 High CO2: {reading.co2} ppm (Limit: {sensor.co2_limit_high} ppm)")

    if alerts:
        sensor.status = "Alarm"
        
        # Construct Alert Message
        message = f"🚨 *Environment Alert: {sensor.sensor_name}*\n"
        message += f"Warehouse: {sensor.warehouse or 'Unknown'}\n\n"
        for a in alerts:
            message += f"• {a}\n"
        message += f"\nTime: {frappe.utils.format_datetime(reading.timestamp)}\n"
        message += f"\n_Please check the cold room immediately._"
        
        # Send to Managers (Assuming we send to same Daily Summary recipients or defined on sensor)
        # For now, let's fetch from WhatsApp Settings
        wa_settings = frappe.get_single("Cold Storage WhatsApp Settings")
        if wa_settings.enabled and wa_settings.summary_recipients:
            recipients = [r.strip() for r in wa_settings.summary_recipients.split('\n') if r.strip()]
            for number in recipients:
                utils.send_whatsapp(number, message)
        
        # Log Alert
        frappe.log_error(f"Environmental Alarm: {sensor.sensor_name}", message)
