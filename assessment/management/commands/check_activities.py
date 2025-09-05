from django.core.management.base import BaseCommand
from adminNew.models import Activity, ActivityItem, ActivityChoice
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check and create test activities for MCQ'

    def handle(self, *args, **options):
        # Check existing activities
        activities = Activity.objects.all()
        self.stdout.write(f"Found {activities.count()} activities in database")
        
        for activity in activities:
            self.stdout.write(f"- Activity {activity.id}: {activity.title}")
            self.stdout.write(f"  Items: {activity.items.count()}")
            for item in activity.items.all():
                self.stdout.write(f"    Item {item.item_number}: {item.scenario[:50]}...")
                self.stdout.write(f"      Choices: {item.choices.count()}")
        
        # Create test activity if none exist
        if activities.count() == 0:
            self.stdout.write("No activities found. Creating test activity...")
            
            # Get or create a user for the activity
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@example.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                user.set_password('admin123')
                user.save()
                self.stdout.write("Created admin user")
            
            # Create test activity
            activity = Activity.objects.create(
                title="Test MCQ Activity",
                description="A test multiple choice activity for debugging",
                scenario="This is a test scenario for the MCQ activity.",
                created_by=user
            )
            
            # Create test items
            item1 = ActivityItem.objects.create(
                activity=activity,
                item_number=1,
                scenario="What is the capital of the Philippines?"
            )
            
            # Create choices for item1
            ActivityChoice.objects.create(
                activity_item=item1,
                text="Manila",
                is_correct=True,
                display_order=1
            )
            ActivityChoice.objects.create(
                activity_item=item1,
                text="Cebu",
                is_correct=False,
                display_order=2
            )
            ActivityChoice.objects.create(
                activity_item=item1,
                text="Davao",
                is_correct=False,
                display_order=3
            )
            ActivityChoice.objects.create(
                activity_item=item1,
                text="Quezon City",
                is_correct=False,
                display_order=4
            )
            
            item2 = ActivityItem.objects.create(
                activity=activity,
                item_number=2,
                scenario="What is 2 + 2?"
            )
            
            # Create choices for item2
            ActivityChoice.objects.create(
                activity_item=item2,
                text="3",
                is_correct=False,
                display_order=1
            )
            ActivityChoice.objects.create(
                activity_item=item2,
                text="4",
                is_correct=True,
                display_order=2
            )
            ActivityChoice.objects.create(
                activity_item=item2,
                text="5",
                is_correct=False,
                display_order=3
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"Created test activity with ID {activity.id}")
            )
            self.stdout.write(f"Activity: {activity.title}")
            self.stdout.write(f"Items: {activity.items.count()}")
            for item in activity.items.all():
                self.stdout.write(f"  Item {item.item_number}: {item.choices.count()} choices")
        
        self.stdout.write(self.style.SUCCESS("Activity check completed!"))
