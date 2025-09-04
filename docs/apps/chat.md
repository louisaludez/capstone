### Chat Module

Model: `chat.models.Message`
- sender_role, receiver_role, subject?, body, is_read, timestamps, sender_id

HTTP Views (not wired under `/chat/` in current router):
- `send_message` (csrf_exempt): POST JSON `{ sender_id, receiver_id, subject?, body }` using Django's `User` model; persists a `Message`. Returns JSON.

Example:
```bash
curl -X POST http://localhost:8000/chat/send/ \
  -H 'Content-Type: application/json' \
  -d '{"sender_id":1,"receiver_id":2,"subject":"Hi","body":"Hello there"}'
```

WebSocket Consumer: `chat/consumers.py:ChatConsumer`
- Path pattern must include `room_name` kwarg (see Channels routing).
- On connect: requires authenticated user; joins base room and role room.
- Receive JSON: `{ body, sender_id, receiver_role, subject? }`
  - Validates roles, persists `Message`, broadcasts to role rooms.
- Message delivered to sender and to users whose roles map to `receiver_role`.

Role utilities:
- `simplify_role`, `get_related_roles`, `is_valid_role`

Channels routing:
- WebSocket path: `ws/chat/<room_name>/` → `ChatConsumer`
