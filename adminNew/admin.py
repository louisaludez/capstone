from django.contrib import admin
from .models import Activity, ActivityItem, ActivityChoice, SpeechActivity


class ActivityChoiceInline(admin.TabularInline):
    model = ActivityChoice
    extra = 1


class ActivityItemInline(admin.TabularInline):
    model = ActivityItem
    extra = 1
    inlines = [ActivityChoiceInline]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")
    inlines = [ActivityItemInline]


@admin.register(ActivityItem)
class ActivityItemAdmin(admin.ModelAdmin):
    list_display = ("activity", "item_number", "timer_seconds")
    list_filter = ("activity",)
    inlines = [ActivityChoiceInline]


@admin.register(ActivityChoice)
class ActivityChoiceAdmin(admin.ModelAdmin):
    list_display = ("activity_item", "text", "is_correct", "display_order")
    list_filter = ("is_correct",)
    search_fields = ("text",)


@admin.register(SpeechActivity)
class SpeechActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "timer_seconds", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "description")
