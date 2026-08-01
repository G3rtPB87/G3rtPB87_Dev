from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Look up `key` in a dict from a template, e.g. {{ mydict|get_item:key }}."""
    return mapping.get(key)
