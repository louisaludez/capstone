# Generated migration for conversation_room field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_message_sender_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='conversation_room',
            field=models.CharField(blank=True, db_index=True, help_text="Room identifier for this conversation (e.g., 'chat_Admin_Cafe')", max_length=100),
        ),
    ]
