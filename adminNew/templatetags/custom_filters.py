from django import template
from datetime import date

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
