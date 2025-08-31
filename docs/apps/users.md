### Users Module

Models: `users.models.CustomUser`

Fields:
- `role`: one of configured ROLE_CHOICES (see `docs/auth.md`).

#### GET `/users/signup/`
- Renders registration page (`RegisterView`).

#### GET|POST `/users/login/`
- POST form fields: `username`, `password`.
- On success: redirects based on role.
- On failure: re-renders with error.

#### GET `/users/logout/`
- Logs out and redirects to login.
