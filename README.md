# Cold Storage Management for Frappe

A premium, enterprise-grade Cold Storage Management application built on the Frappe Framework. This app streamlines the process of managing agricultural goods (Potatoes, Onions, etc.), automates complex billing, and integrates real-time IoT monitoring and predictive analytics.

## 🚀 Key Features

### 1. Inward & Outward Management
*   **Cold Storage Receipt**: Record incoming stock with Customer, Warehouse, and Batch details.
*   **Gate Pass System**: Automated generation of Gate Passes for secure movement.
*   **QR Code Ready**: Print Receipts with embedded QR codes for rapid retrieval.
*   **Mobile Entry**: Dedicated mobile-first UI for fast on-site data entry.

### 2. IoT Environment Monitoring (SenseCAP Integration)
*   **Real-Time Dashboard**: Monitor **CO2**, **Temperature**, and **Humidity** in real-time via SenseCAP S2103 LoRaWAN sensors.
*   **Proactive Alerts**: Automatic **WhatsApp notifications** if environmental thresholds are exceeded.
*   **Historical Trends**: Analyze climate stability with long-term time-series charts.

### 3. Predictive Analytics & Reporting
*   **Peak Season Forecast**: Predictive modeling of "Busy Seasons" based on historical intake/outtake volume.
*   **Storage Duration Analysis**: Automated calculation of average storage days per item.
*   **Warehouse Heatmaps**: Visual occupancy metrics for optimized floor planning.
*   **Inventory Aging**: Identify long-stored stock to prioritize dispatches.

### 4. Smart Billing & Account Sync
*   **Multi-Tier Pricing**: Define rates based on Item Group, Season, and Customer Tier (VIP, Gold, etc.).
*   **Flexible Cycles**: Support for Daily, Monthly, and Seasonal billing.
*   **ERPNext Sync**: One-click generation of Sales Invoices, Stock Entries, and Journal Entries.

### 5. Multi-Language & Urdu Support
*   **Localized Experience**: Unified support for **English** and **Urdu**.
*   **RTL Design**: Full Right-to-Left layout support for Urdu reports (PDF/XLSX).
*   **Premium Print Formats**: Modern, aesthetically pleasing designs for Receipts and Dispatches.

### 6. Automated Communications (WhatsApp)
*   **Activity Alerts**: Instant customer notifications for "Goods Received" and "Dispatched".
*   **Daily Summaries**: Automated daily volume reports sent to management via WhatsApp.
*   **Payment Reminders**: Scheduled reminders for overdue invoices.

## ⚙️ Configuration

1.  **Cold Storage Settings**: Define default company, global rates, and account mappings.
2.  **WhatsApp Settings**: Configure Twilio credentials and message templates.
3.  **Environment Sensors**: Register SenseCAP DevEUIs and set safety thresholds per chamber.

## 🛠 Installation

```bash
bench get-app cold_storage [repo-url]
bench --site [site-name] install-app cold_storage
bench --site [site-name] migrate
```

## 📜 License
MIT
