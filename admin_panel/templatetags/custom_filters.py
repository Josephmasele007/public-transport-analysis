from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    return getattr(obj, attr, '') 

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0