
from django.contrib import admin
from .models import *

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'status', 'capacity', 'price_per_night', 'is_available']
    list_filter = ['room_type', 'status', 'is_accessible', 'has_balcony', 'has_ocean_view']
    search_fields = ['room_number', 'description']
    list_editable = ['status', 'price_per_night']
    ordering = ['room_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('room_number', 'room_type', 'capacity', 'price_per_night')
        }),
        ('Status & Description', {
            'fields': ('status', 'description')
        }),
        ('Features', {
            'fields': ('is_accessible', 'has_balcony', 'has_ocean_view', 'amenities')
        }),
    )

admin.site.register(Guest)
admin.site.register(Booking)
admin.site.register(Payment)