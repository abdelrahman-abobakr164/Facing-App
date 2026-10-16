from django import template

register = template.Library()


@register.filter
def admins_first(users, admin_ids):
    admin_ids = set(admin_ids)
    return sorted(
        users,
        key=lambda u: (u.id not in admin_ids, u.username.lower()),
    )
