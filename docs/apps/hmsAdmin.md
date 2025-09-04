### Admin (hmsAdmin) Module

Role-protected views with `role_required('admin')`.

Key routes (see `hmsAdmin/urls.py`): home, messages, training, analytics, accounts, CRUD for users, activity pages for MCQ and Speech.

Selected APIs:
- POST `/hmsAdmin/accountsAdmin/add-user/` → `add_user` creates a user; checks unique username/email. JSON result.
- GET `/hmsAdmin/accountsAdmin/view-user/<id>/` → `view_user` returns JSON summary.
- POST `/hmsAdmin/accountsAdmin/edit-user/<id>/` → `edit_user` updates fields. JSON result.
- POST `/hmsAdmin/accountsAdmin/delete-user/<id>/` → `delete_user` deletes user. JSON result.
- GET `/hmsAdmin/api/occupancy-forecast/` → returns error JSON (placeholder).
- MCQ and Speech activity pages expose add/edit/delete and simulate endpoints.
