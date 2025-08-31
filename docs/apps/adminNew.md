### Admin (adminNew) Module

Admin-oriented dashboard and content management.

Key endpoints:
- GET `/adminNew/` → dashboard metrics
- GET `/adminNew/accounts/` → users list
- POST `/adminNew/accounts/add-user/` → add user (JSON response)
- GET `/adminNew/accounts/view-user/<id>/` → JSON summary
- POST `/adminNew/accounts/edit-user/<id>/` → update user (JSON)
- POST `/adminNew/accounts/delete-user/<id>/` → delete user (JSON)
- Reports: `/adminNew/reports/*` pages summarize billing from `Guest` fields
- Training and activity materials:
  - GET `/adminNew/activity-materials/`
  - GET|POST `/adminNew/activity-materials/add-activity/` to edit one activity and its choices
  - POST `/adminNew/activity-materials/save/` bulk create/update/delete via JSON payload

Models:
- `Activity(title, description, scenario, timer_seconds, created_by, is_active, timestamps)`
- `ActivityChoice(activity, text, is_correct, display_order)`
