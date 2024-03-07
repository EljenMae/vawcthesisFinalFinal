from django import template

register = template.Library()

@register.filter
def get_latest_status(history):
    return history.latest('status_date_added') if history.exists() else None