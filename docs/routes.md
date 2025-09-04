### Routes Overview

Root router: `hotelAi/urls.py`

Included apps and prefixes:
- `/` and `/staff/` → `staff.urls`
- `/users/` → `users.urls`
- `/adminNew/` → `adminNew.urls`
- `/laundry/` → `laundry.urls`
- `/cafe/` → `cafe.urls`
- `/room-service/` → `room_service.urls`
- `/concierge/` → `concierge.urls`
- `/activity/` → `activity.urls`
- `/housekeeping/` → `housekeeping.urls`
- `/assessment/` → `assessment.urls`
- `/guestbooking/` → `guestbooking.urls`
- `/chat/` → `chat.urls`

#### staff
- GET `/` → `staff.views.home` (role_required: personnel)
- GET `/message/` → `staff.views.message`
- GET `/view-reservations/` → `view_reservations` (role_required: personnel)
- POST `/book-room/` → `book_room` (role_required: personnel)
- GET `/rooms/` → `room_list` (role_required: personnel)
- GET `/get-guest/<int:guest_id>/` → `getGuest`
- GET `/ajax/get-reservations/` → `get_reservations_ajax`
- GET `/api/room-status/` → `room_status`
- POST `/api/checkout/` → `perform_checkout`

#### users
- GET `/users/signup/` → `RegisterView.as_view()`
- GET|POST `/users/login/` → `login`
- GET `/users/logout/` → `logout_view`

#### adminNew
- GET `/adminNew/` → `admin_home`
- GET `/adminNew/accounts/` → `admin_account`
- POST `/adminNew/accounts/add-user/` → `add_user`
- GET `/adminNew/accounts/view-user/<int:user_id>/` → `view_user`
- POST `/adminNew/accounts/edit-user/<int:user_id>/` → `edit_user`
- POST `/adminNew/accounts/delete-user/<int:user_id>/` → `delete_user`
- GET `/adminNew/reports/` → `admin_reports`
- GET `/adminNew/messenger/` → `admin_messenger`
- GET `/adminNew/reports/front-office/` → `admin_front_office_reports`
- GET `/adminNew/reports/cafe/` → `admin_cafe_reports`
- GET `/adminNew/reports/laundry/` → `admin_laundry_reports`
- GET `/adminNew/reports/housekeeping/` → `admin_housekeeping_reports`
- GET `/adminNew/reports/speech/` → `admin_speech_reports`
- GET `/adminNew/reports/mcq/` → `admin_mcq_reports`
- GET `/adminNew/training/` → `admin_training`
- GET `/adminNew/activity-materials/` → `admin_activity_materials`
- GET|POST `/adminNew/activity-materials/add-activity/` → `add_activity`
- POST `/adminNew/activity-materials/save/` → `save_activities`

#### hmsAdmin
- GET `/hmsAdmin/` routes defined in `hmsAdmin/urls.py` (not included at project level; reference kept for completeness)

#### cafe
- GET `/cafe/staff/home/` → `staff_cafe_home`
- GET `/cafe/search-items-ajax/` → `search_items_ajax`
- POST `/cafe/staff/create-order/` → `create_order` (csrf_exempt)
- GET `/cafe/staff/orders/` → `staff_cafe_orders`

#### laundry
- GET `/laundry/` → `staff_laundry_home`
- GET `/laundry/staff/<int:guest_id>` → `getGuest`
- GET `/laundry/messages/` → `staff_laundry_messages`
- GET `/laundry/orders/` → `staff_laundry_orders` (AJAX supports pagination)
- GET `/laundry/orders/<int:order_id>/view/` → `view_laundry_order`
- POST|GET `/laundry/orders/<int:order_id>/edit/` → `edit_laundry_order`
- POST `/laundry/orders/<int:order_id>/delete/` → `delete_laundry_order`
- POST `/laundry/orders/<int:order_id>/status/` → `update_order_status`
- POST `/laundry/staff/create-order/` → `create_laundry_order`

#### housekeeping
- GET `/housekeeping/` → `housekeeping_home`
- POST `/housekeeping/update_status/` → `update_status` (csrf_exempt)
- GET `/housekeeping/timeline/` → `timeline`
- GET `/housekeeping/task/<int:task_id>/view/` → `view_task`
- POST|GET `/housekeeping/task/<int:task_id>/edit/` → `edit_task`
- POST `/housekeeping/task/<int:task_id>/delete/` → `delete_task`

#### concierge
- GET `/concierge/` → `dashboard`
- GET `/concierge/timeline/` → `timeline`
- GET `/concierge/messenger/` → `messenger`
- GET `/concierge/book-reservations/` → `book_reservations`
- GET `/concierge/book-tours/` → `book_tours`

#### room_service
- GET `/room-service/` → `dashboard`
- GET `/room-service/notifications/` → `notifications`
- GET `/room-service/tasks/` → `tasks`
- GET `/room-service/timeline/` → `timeline`
- GET `/room-service/laundry/` → `room_service_laundry`
- GET `/room-service/housekeeping/` → `room_service_housekeeping`
- GET `/room-service/cafe/` → `room_service_cafe`
- GET `/room-service/mesenger/` → `messenger`

#### activity
- GET `/activity/` → `home`

#### assessment
- GET `/assessment/mcq/` → `mcq_home`
- GET `/assessment/speech/` → `speech_home`

#### guestbooking
- GET `/guestbooking/` → `guest_booking_home`
- GET `/guestbooking/results/` → `guest_booking_results`

#### chat
- Currently no HTTP endpoints registered under `/chat/` (see WebSocket consumer below and `chat/views.send_message` which is not wired here).

