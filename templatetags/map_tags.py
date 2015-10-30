from django import template

register = template.Library()


@register.inclusion_tag('maps/widgets/load.html')
def show_network_load():
    return {}
