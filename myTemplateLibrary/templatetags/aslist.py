from django import template

register = template.Library()


@register.simple_tag
def aslist(*args):
    return args
