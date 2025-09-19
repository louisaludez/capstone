from django import template
from datetime import date
from django.utils.html import format_html_join

register = template.Library()

@register.filter
def days_between(start_date, end_date):
    """Calculate days between two dates"""
    if start_date and end_date:
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        delta = end_date - start_date
        return delta.days
    return 0

@register.filter
def lookup(dictionary, key):
    """Look up a key in a dictionary"""
    if dictionary and key:
        return dictionary.get(key, '')
    return ''

@register.filter
def total_other_charges(guest):
    """Calculate total other charges for a guest"""
    if not guest:
        return 0
    
    total = 0
    try:
        total += float(guest.room_service_billing or 0)
        total += float(guest.laundry_billing or 0)
        total += float(guest.cafe_billing or 0)
        total += float(guest.excess_pax_billing or 0)
        total += float(guest.additional_charge_billing or 0)
    except (ValueError, TypeError):
        pass
    
    return total

@register.filter
def sum_quantities(items_queryset):
    try:
        return sum(int(it.quantity) for it in items_queryset.all())
    except Exception:
        return 0

@register.filter
def join_items_names(items_queryset):
    try:
        names = [it.item.name for it in items_queryset.all()]
        return ', '.join(names[:3]) + ('…' if len(names) > 3 else '')
    except Exception:
        return ''