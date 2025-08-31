### Laundry Module

Model: `LaundryTransaction`

#### GET `/laundry/`
- Renders staff laundry home with guests list.

#### GET `/laundry/messages/`
- Renders messenger view filtered by role pairs.

#### GET `/laundry/orders/`
- Query: `search`, `status`, `sort` (created_at, -created_at, guest__name, -guest__name, status, -status), `page`.
- Renders paginated list; AJAX requests return HTML snippet and pagination meta.

#### GET `/laundry/orders/<id>/view/`
- JSON details of a laundry order.

#### POST|GET `/laundry/orders/<id>/edit/`
- POST JSON to update `service_type`, `no_of_bags`, `specifications`, `status`, `payment_method`.
- Recomputes `total_amount`.

#### POST `/laundry/orders/<id>/delete/`
- Deletes the order.

#### POST `/laundry/orders/<id>/status/`
- Body JSON: `{ status }` to update status.

#### POST `/laundry/staff/create-order/`
- JSON or form data:
  - guest_id, room_number, no_bags, service_type, specifications?, date_time (YYYY-MM-DD), payment_method ('cash' or 'room' expected)
- Creates `LaundryTransaction`; if 'Charge to room' used upstream, view updates `Guest.laundry_billing`.

Model fields:
- guest(FK), booking(FK?), room_number, service_type, no_of_bags, specifications?, date_time, payment_method(cash|room), total_amount, status, created_at
- Save hook: if payment_method == 'room', increments `Guest.billing`
