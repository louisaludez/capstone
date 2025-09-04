### Documentation Index

- Overview and routing: `docs/routes.md`
- Authentication and roles: `docs/auth.md`
- Utility decorators: `docs/utilities/role_required.md`

Per-app documentation:
- Staff: `docs/apps/staff.md`
- Users: `docs/apps/users.md`
- Admin (hmsAdmin): `docs/apps/hmsAdmin.md`
- Admin (adminNew): `docs/apps/adminNew.md`
- Cafe: `docs/apps/cafe.md`
- Laundry: `docs/apps/laundry.md`
- Housekeeping: `docs/apps/housekeeping.md`
- Concierge: `docs/apps/concierge.md`
- Room Service: `docs/apps/room_service.md`
- Guest Booking: `docs/apps/guestbooking.md`
- Chat and WebSocket: `docs/apps/chat.md`

Conventions:
- All paths shown are relative to the Django site root (see `hotelAi/urls.py`).
- Unless marked as CSRF-exempt, POST requests require CSRF tokens when using session auth.
- Endpoints with role restrictions require an authenticated session for a user whose `role` matches the requirement.
