### Housekeeping Module

Model: `Housekeeping`

#### GET `/housekeeping/`
- Renders summary grid for rooms 1–12 showing latest status per room.

#### POST `/housekeeping/update_status/` (csrf_exempt)
- Form fields: `room_no`, `status`, `request_type`
- Looks up `Booking` by room to resolve guest name.
- Upserts `Housekeeping(room_number, guest_name, request_type)` with new status.
- JSON response with message.

#### GET `/housekeeping/timeline/`
- Paginated list of housekeeping tasks.

#### GET `/housekeeping/task/<id>/view/`
- JSON details of task.

#### POST|GET `/housekeeping/task/<id>/edit/`
- POST form fields to update task; returns JSON on success.

#### POST `/housekeeping/task/<id>/delete/`
- Deletes task; JSON success.

Model fields:
- room_number, guest_name?, request_type?, status?, created_at
