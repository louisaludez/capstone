from django.contrib import admin
from .models import Activity, ActivityChoice


class ActivityChoiceInline(admin.TabularInline):
    model = ActivityChoice
    extra = 1


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "timer_seconds", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description", "scenario")
    inlines = [ActivityChoiceInline]


@admin.register(ActivityChoice)
class ActivityChoiceAdmin(admin.ModelAdmin):
    list_display = ("activity", "text", "is_correct", "display_order")
    list_filter = ("is_correct",)
    search_fields = ("text",)
