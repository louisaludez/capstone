from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import Message

User = get_user_model()

def simplify_role(role):
    role_mapping = {
        'staff_personnel': 'Personnel',
        'manager_personnel': 'Personnel',
        'supervisor_personnel': 'Personnel',
        'personnel': 'Personnel',
        'staff': 'Personnel',
        'manager': 'Personnel',
        'staff_concierge': 'Concierge',
        'manager_concierge': 'Concierge',
        'supervisor_concierge': 'Concierge',
        'staff_laundry': 'Laundry',
        'manager_laundry': 'Laundry',
        'supervisor_laundry': 'Laundry',
        'staff_cafe': 'Cafe',
        'manager_cafe': 'Cafe',
        'supervisor_cafe': 'Cafe',
        'staff_room_service': 'Room Service',
        'manager_room_service': 'Room Service',
        'supervisor_room_service': 'Room Service',
        'admin': 'Admin',
        'SUPER_ADMIN': 'Admin'
    }
    return role_mapping.get(role, role)

def get_related_roles(role):
    role_mappings = {
        'Personnel': ['staff_personnel', 'manager_personnel', 'supervisor_personnel', 'Personnel', 'personnel', 'staff', 'manager'],
        'Concierge': ['staff_concierge', 'manager_concierge', 'supervisor_concierge', 'Concierge'],
        'Laundry': ['staff_laundry', 'manager_laundry', 'supervisor_laundry', 'Laundry'],
        'Cafe': ['staff_cafe', 'manager_cafe', 'supervisor_cafe', 'Cafe'],
        'Room Service': ['staff_room_service', 'manager_room_service', 'supervisor_room_service', 'Room Service'],
        'Admin': ['admin', 'Admin', 'SUPER_ADMIN']
    }
    for general_role, specific_roles in role_mappings.items():
        if role in specific_roles:
            return specific_roles
    return role_mappings.get(role, [role])

def is_valid_role(role):
    valid_roles = [
        'Personnel', 'Concierge', 'Laundry', 'Cafe', 'Room Service', 'Admin',
        'staff_personnel', 'manager_personnel',
        'staff_concierge', 'manager_concierge',
        'staff_laundry', 'manager_laundry',
        'staff_cafe', 'manager_cafe',
        'staff_room_service', 'manager_room_service',
        'supervisor_personnel', 'supervisor_concierge', 'supervisor_laundry', 'supervisor_cafe', 'supervisor_room_service',
        'admin', 'Admin', 'SUPER_ADMIN', 'personnel', 'staff', 'manager'
    ]
    return role in valid_roles

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Get the user from the scope
            self.user = self.scope["user"]
            if not self.user.is_authenticated:
                await self.close()
                return

            # Get the room name from the URL and clean it
            self.base_room_name = self.scope['url_route']['kwargs']['room_name']
            
            # Join the base room
            await self.channel_layer.group_add(self.base_room_name, self.channel_name)
            
            # Also join a room specific to this user's role
            self.user_role = self.user.role
            self.role_room = f"role_{simplify_role(self.user_role)}".replace(' ', '_')
            await self.channel_layer.group_add(self.role_room, self.channel_name)
            
            # Store all rooms we're connected to
            self.rooms = [self.base_room_name, self.role_room]
            
            # Store user roles for message filtering
            self.user_roles = set(get_related_roles(self.user_role))
            
            await self.accept()
            print(f"WebSocket connected for user {self.user.username} in rooms {self.rooms}")
        except Exception as e:
            print(f"Error in connect: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave all rooms
            for room in self.rooms:
                await self.channel_layer.group_discard(room, self.channel_name)
            print(f"WebSocket disconnected for user {self.user.username} from rooms {self.rooms}")
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            body = data['body']
            sender_id = data['sender_id']
            receiver_role = data['receiver_role']
            subject = data.get('subject', '')

            if not is_valid_role(receiver_role):
                print(f"Invalid receiver role: {receiver_role}")
                return

            sender = await sync_to_async(User.objects.get)(id=sender_id)
            sender_role = sender.role
            sender_username = sender.username

            if not is_valid_role(sender_role):
                print(f"Invalid sender role: {sender_role}")
                return

            # Save message to database
            message = await self.save_message(sender_id, receiver_role, subject, body)

            # Compute base conversation room (symmetric)
            conv_roles = sorted([simplify_role(sender_role), simplify_role(receiver_role)])
            base_room = f"chat_{'_'.join([r.replace(' ', '_') for r in conv_roles])}"

            # Prepare message data
            # Use actual role for display, but simplified role for room matching
            message_data = {
                'type': 'chat_message',
                'message_id': str(message.id),
                'body': body,
                'sender_id': sender_id,
                'sender_role': sender_role,  # Use actual role for display
                'sender_username': sender_username,
                'receiver_role': simplify_role(receiver_role),
                'subject': subject,
                'timestamp': str(message.created_at),
                'base_room': base_room,
            }

            # Get all related roles for the receiver
            receiver_roles = get_related_roles(receiver_role)
            
            # Send to all relevant role rooms
            sent_to_rooms = set()
            for role in receiver_roles:
                role_room = f"role_{simplify_role(role)}".replace(' ', '_')
                if role_room not in sent_to_rooms:
                    await self.channel_layer.group_send(role_room, message_data)
                    sent_to_rooms.add(role_room)
                    print(f"Sent message to room {role_room}")
            
            # Also send to sender's role room if different
            sender_role_room = f"role_{simplify_role(sender_role)}".replace(' ', '_')
            if sender_role_room not in sent_to_rooms:
                await self.channel_layer.group_send(sender_role_room, message_data)
                sent_to_rooms.add(sender_role_room)
                print(f"Sent message to sender's room {sender_role_room}")

            # Additionally, send to the conversation base room (symmetric room both UIs join)
            if base_room not in sent_to_rooms:
                await self.channel_layer.group_send(base_room, message_data)
                sent_to_rooms.add(base_room)
                print(f"Sent message to base room {base_room}")

            print(f"Message sent to rooms: {sent_to_rooms}")
        except Exception as e:
            print(f"Error in receive: {str(e)}")

    async def chat_message(self, event):
        try:
            # Get the receiver role and related roles
            receiver_role = event['receiver_role']
            receiver_roles = set(get_related_roles(receiver_role))
            sender_id = event['sender_id']
            sender_role = event.get('sender_role')
            sender_roles = set(get_related_roles(sender_role)) if sender_role else set()
            
            # Send the message if:
            # 1. The user is the sender, OR
            # 2. The user's roles overlap with the receiver roles
            should_receive = (
                str(self.user.id) == str(sender_id) or
                bool(self.user_roles.intersection(receiver_roles)) or
                bool(self.user_roles.intersection(sender_roles))
            )
            
            if should_receive:
                # Send message to WebSocket
                await self.send(text_data=json.dumps({
                    'message_id': event['message_id'],
                    'body': event['body'],
                    'sender_id': event['sender_id'],
                    'sender_role': event['sender_role'],
                    'sender_username': event['sender_username'],
                    'receiver_role': event['receiver_role'],
                    'subject': event['subject'],
                    'timestamp': event['timestamp']
                }))
                # delivered
                pass
        except Exception as e:
            print(f"Error in chat_message: {str(e)}")

    @sync_to_async
    def save_message(self, sender_id, receiver_role, subject, body):
        try:
            sender = User.objects.get(id=sender_id)
            sender_role = simplify_role(sender.role)
            message = Message.objects.create(
                sender_id=sender_id,
                sender_role=sender_role,
                receiver_role=receiver_role,
                subject=subject,
                body=body
            )
            return message
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            raise 