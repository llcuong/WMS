from django import template

register = template.Library()


@register.filter
def dict_item(dictionary, key):
    return dictionary.get(key, [])


@register.filter
def range_to(start, end):
    return range(int(start), int(end)+1)