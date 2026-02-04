frappe.pages['mobile-receipt-entry'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Mobile Receipt Entry',
		single_column: true
	});

	$(wrapper).find('.layout-main-section').empty().append(`
		<div id="mobile-entry-container" class="mobile-container">
			<div class="form-section">
				<div class="field-row">
					<label>Customer</label>
					<div id="customer-picker"></div>
				</div>
				<div class="field-row">
					<label>Warehouse</label>
					<div id="warehouse-picker"></div>
				</div>
				<div class="field-row">
					<label>Vehicle No</label>
					<input type="text" id="vehicle_no" class="form-control" placeholder="ABC-1234">
				</div>
				<div class="grid-row">
					<div class="field-row">
						<label>Driver Name</label>
						<input type="text" id="driver_name" class="form-control" placeholder="John Doe">
					</div>
					<div class="field-row">
						<label>Driver Phone</label>
						<input type="tel" id="driver_phone" class="form-control" placeholder="0300-1234567" value="+92 ">
					</div>
				</div>
			</div>

			<div class="items-section">
				<h3>Items</h3>
				<div id="items-list"></div>
				<button class="btn btn-secondary btn-block mt-3" id="add-item-btn">
					<i class="fa fa-plus"></i> Add Item
				</button>
			</div>

			<div class="actions-section mt-4">
				<button class="btn btn-primary btn-lg btn-block" id="submit-receipt-btn">
					Submit Receipt
				</button>
			</div>
		</div>

		<style>
			#mobile-entry-container {
				width: 100%;
				padding: 15px;
				background: #f8f9fa;
				min-height: 80vh;
			}
			.form-section, .items-section {
				background: white;
				padding: 20px;
				border-radius: 12px;
				box-shadow: 0 4px 12px rgba(0,0,0,0.05);
				margin-bottom: 20px;
			}
			.field-row {
				margin-bottom: 15px;
			}
			.field-row label {
				font-size: 13px;
				font-weight: 600;
				color: #666;
				margin-bottom: 5px;
				display: block;
			}
			.form-control {
				border-radius: 8px;
				border: 1px solid #ddd;
				padding: 12px;
				font-size: 16px;
			}
			.grid-row {
				display: grid;
				grid-template-columns: 1fr 1fr;
				gap: 15px;
			}
			.item-card {
				background: #fdfdfd;
				border: 1px solid #eee;
				border-radius: 8px;
				padding: 15px;
				margin-bottom: 10px;
				position: relative;
			}
			.item-card .remove-item {
				position: absolute;
				top: 5px;
				right: 5px;
				color: #dc3545;
				cursor: pointer;
			}
			.btn-primary {
				background: #2c3e50;
				border-color: #2c3e50;
				padding: 15px;
				font-weight: 600;
				font-size: 18px;
				border-radius: 10px;
			}
			.btn-secondary {
				border-radius: 8px;
			}
			h3 {
				font-size: 18px;
				margin-bottom: 15px;
				color: #2c3e50;
			}
		</style>
	`);

	// Initialize Controls
	var customer_field = frappe.ui.form.make_control({
		parent: $(wrapper).find('#customer-picker'),
		df: {
			fieldtype: 'Link',
			options: 'Customer',
			fieldname: 'customer',
			placeholder: 'Search Customer...'
		},
		render_input: true
	});

	var warehouse_field = frappe.ui.form.make_control({
		parent: $(wrapper).find('#warehouse-picker'),
		df: {
			fieldtype: 'Link',
			options: 'Warehouse',
			fieldname: 'warehouse',
			placeholder: 'Search Warehouse...',
			get_query: function () {
				return { filters: { is_group: 0 } };
			}
		},
		render_input: true
	});

	// Default Company & Warehouse
	frappe.db.get_single_value("Cold Storage Settings", "default_company").then(val => {
		wrapper.default_company = val;
	});

	// Items Handling
	var items = [];
	function render_items() {
		var container = $(wrapper).find('#items-list').empty();
		items.forEach((item, index) => {
			var card = $(`
				<div class="item-card">
					<i class="fa fa-times remove-item" data-index="${index}"></i>
					<div class="field-row">
						<label>Item</label>
						<div class="item-link-container" data-index="${index}"></div>
					</div>
					<div class="grid-row">
						<div class="field-row">
							<label>Bags</label>
							<input type="number" class="form-control item-qty" data-index="${index}" value="${item.qty || ''}">
						</div>
						<div class="field-row">
							<label>Batch</label>
							<div class="batch-link-container" data-index="${index}"></div>
						</div>
					</div>
				</div>
			`).appendTo(container);

			// Small Hack for Link Field in dynamic row
			var item_link = frappe.ui.form.make_control({
				parent: card.find('.item-link-container'),
				df: {
					fieldtype: 'Link',
					options: 'Item',
					fieldname: 'item_code',
					placeholder: 'Select Product',
					change: function () {
						items[index].item_code = this.get_value();
						// Fetch item group automatically
						if (items[index].item_code) {
							frappe.db.get_value('Item', items[index].item_code, 'item_group').then(r => {
								items[index].item_group = r.message.item_group;
							});
						}
					}
				},
				render_input: true
			});
			if (item.item_code) item_link.set_value(item.item_code);

			var batch_link = frappe.ui.form.make_control({
				parent: card.find('.batch-link-container'),
				df: {
					fieldtype: 'Link',
					options: 'Batch',
					fieldname: 'batch_no',
					placeholder: 'Select or Type Batch',
					get_query: function () {
						let customer = customer_field.get_value();
						let item_code = items[index].item_code;
						return {
							filters: {
								customer: customer || "",
								item: item_code || ""
							}
						};
					},
					change: function () {
						items[index].batch = this.get_value();
					}
				},
				render_input: true
			});
			if (item.batch) batch_link.set_value(item.batch);
		});
	}

	$(wrapper).find('#add-item-btn').click(() => {
		items.push({ item_code: '', qty: 0, batch: '', item_group: '' });
		render_items();
	});

	$(wrapper).on('click', '.remove-item', function () {
		items.splice($(this).data('index'), 1);
		render_items();
	});

	$(wrapper).on('change', '.item-qty', function () {
		items[$(this).data('index')].qty = $(this).val();
	});

	// Submit
	$(wrapper).find('#submit-receipt-btn').click(() => {
		var data = {
			customer: customer_field.get_value(),
			warehouse: warehouse_field.get_value(),
			vehicle_no: $(wrapper).find('#vehicle_no').val(),
			driver_name: $(wrapper).find('#driver_name').val(),
			driver_phone: $(wrapper).find('#driver_phone').val(),
			items: items
		};

		// Validation: Check if there's at least one item with qty > 0
		let valid_items = items.filter(i => i.item_code && flt(i.qty) > 0);
		if (!data.customer || !data.warehouse || valid_items.length === 0) {
			frappe.msgprint(__('Please select Customer, Warehouse, and enter Quantity for at least one item.'));
			return;
		}

		frappe.dom.freeze(__('Creating Receipt...'));
		frappe.call({
			method: 'cold_storage.cold_storage.api.mobile_entry.submit_mobile_receipt',
			args: { data: data },
			callback: function (r) {
				frappe.dom.unfreeze();
				if (r.message) {
					frappe.show_alert({
						message: __('Receipt {0} created successfully', [r.message]),
						indicator: 'green'
					});
					// Reset Form ONLY on success
					customer_field.set_value('');
					$(wrapper).find('#vehicle_no, #driver_name').val('');
					$(wrapper).find('#driver_phone').val('+92 ');
					items = [];
					// Add one empty row back
					items.push({ item_code: '', qty: 0, batch: '', item_group: '' });
					render_items();
				}
			},
			error: function () {
				frappe.dom.unfreeze();
				// The data remains in 'items' and the form fields, so user can correct and retry.
			}
		});
	});

	// Default Row
	items.push({ item_code: '', qty: 0, batch: '', item_group: '' });
	render_items();
};
