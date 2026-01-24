# Data migration to populate conversation_room for existing messages
from django.db import migrations

def populate_conversation_room(apps, schema_editor):
    Message = apps.get_model('chat', 'Message')
    
    def simplify_role(role):
        mapping = {
            'staff_personnel': 'Personnel', 'manager_personnel': 'Personnel', 'personnel': 'Personnel', 'staff': 'Personnel', 'manager': 'Personnel',
            'staff_concierge': 'Concierge', 'manager_concierge': 'Concierge',
            'staff_laundry': 'Laundry', 'manager_laundry': 'Laundry',
            'staff_cafe': 'Cafe', 'manager_cafe': 'Cafe',
            'staff_room_service': 'Room Service', 'manager_room_service': 'Room Service',
            'admin': 'Admin', 'Admin': 'Admin'
        }
        return mapping.get(role, role)
    
    # Update all messages that don't have conversation_room
    for message in Message.objects.filter(conversation_room='').exclude(conversation_room__isnull=False) | Message.objects.filter(conversation_room__isnull=True):
        # Compute conversation room from sender_service or sender_role and receiver_role
        sender_context = simplify_role(message.sender_service) if message.sender_service else simplify_role(message.sender_role)
        receiver_context = simplify_role(message.receiver_role)
        conv_roles = sorted([sender_context, receiver_context])
        conversation_room = f"chat_{'_'.join([r.replace(' ', '_') for r in conv_roles])}"
        message.conversation_room = conversation_room
        message.save(update_fields=['conversation_room'])

def reverse_populate_conversation_room(apps, schema_editor):
    # No need to reverse - just leave conversation_room as is
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_message_conversation_room'),
    ]

    operations = [
        migrations.RunPython(populate_conversation_room, reverse_populate_conversation_room),
    ]
