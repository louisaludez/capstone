from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register([
    # Add your models here to be registered in the admin interface
    Room,Checkin
])