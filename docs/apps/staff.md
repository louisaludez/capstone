### Staff Module

URLs: see `docs/routes.md#staff`
Models: `Guest`, `Room`, `Booking`, `Payment` (from `staff/models.py`)

#### GET `/` (home)
- Role: personnel
- Renders `staff/home.html` with counts and room status/type metrics.

#### GET `/message/` (message)
- Query params: `receiver_role` (default: personnel)
- Renders messaging page; lists messages filtered by roles.

#### GET `/view-reservations/`
- Role: personnel
- Query params: `date=YYYY-MM-DD` (optional; defaults to today)
- Renders placeholder reservations view.

#### POST `/book-room/`
- Role: personnel
- Body: form-encoded
  - guest_name, guest_address, guest_zip_code, guest_email, guest_birth
  - room (room number), check_in, check_out (YYYY-MM-DD)
  - total_guests, adults, children
  - payment_method, card_number, exp_date, cvv, billing_address, current_balance
- Response: JSON
  - 200 on success: `{ success: true, message }`
  - 400 on validation error
  - 404 if room not found
  - 500 for server error

Example (curl):
```bash
curl -X POST -b cookies.txt -c cookies.txt \
  -d "guest_name=John Doe&guest_address=123 St&guest_email=john@example.com&guest_birth=1990-01-01&room=101&check_in=2025-09-01&check_out=2025-09-03&total_guests=2&adults=2&children=0&payment_method=cash" \
  http://localhost:8000/book-room/
```

#### GET `/get-guest/<guest_id>/`
- Returns guest details with bookings and payment summary.

#### GET `/ajax/get-reservations/`
- Query params: `page` (default 1)
- Returns paginated booking summary list.

#### GET `/api/room-status/`
- Query params: `date=YYYY-MM-DD` (required)
- Returns JSON: occupied rooms list, room counts, and counts by type.

#### POST `/api/checkout/`
- Role: personnel
- Body: form-encoded
  - guest_id, check_in, check_out, room, total_guests, adults, children, below_7
  - room_charges, room_service, laundry, cafe, excess_pax, additional_charges
  - payment_method, card_number, exp_date, cvv, billing_address, balance
- Responses: JSON 200/400/404/500

#### Models

`Guest`:
- name, address, zip_code?, email, date_of_birth, billing fields, created_at

`Room`:
- room_number (unique), room_type, status, capacity, price_per_night, amenities JSON, flags, timestamps
- Helpers: `is_available()`, `get_current_booking()`

`Booking`:
- guest(FK), room(CharField), booking_date, check_in_date, check_out_date, guests counts, status

`Payment`:
- booking(OneToOne), method, card fields, billing_address, total_balance, created_at
