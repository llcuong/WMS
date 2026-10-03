from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='has_any_group')
def has_any_group(user, group_names):
    """
    Check if user belongs to any of the groups in a comma-separated list.
    Example: user|has_any_group:"admin,manager"
    """
    group_list = [g.strip() for g in group_names.split(",")]
    return user.groups.filter(name__in=group_list).exists()
