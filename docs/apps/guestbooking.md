### Guest Booking Module

#### GET `/guestbooking/`
- Renders search form for booking.

#### GET `/guestbooking/results/`
- Query params: `stayType`, `checkin`, `checkout`, `rooms`, `adults`, `children`, `childAges?`
- Filters `Room` by `capacity >= adults + children` and `status='available'`.
- Renders list of available rooms with details.
