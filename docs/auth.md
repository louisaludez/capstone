### Authentication and Roles

Auth model: `users.models.CustomUser` extends `AbstractUser` with a `role` CharField.

Roles (selected):
- personnel, admin, manager
- supervisor_laundry, supervisor_concierge, supervisor_cafe
- staff_laundry, staff_concierge, staff_cafe, staff_room_service

Role guard:
- `globals.decorator.role_required(required_role)` wraps a view with `login_required` and checks `request.user.role == required_role`.

Login flow:
- POST `/users/login/` expects `username`, `password`. Upon success, redirects by role.

Logout:
- GET `/users/logout/` clears session and redirects to login.

CSRF:
- Standard Django CSRF applies except where views are explicitly marked `@csrf_exempt`.
