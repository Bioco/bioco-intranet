from django import template
from django.conf import settings

register = template.Library()

# settings value
@register.simple_tag
def settings_value(name):
    # dont serve arbitrary settings
    whitelist = ('SITE_NAME', 'SITE_URL', 'SITE_MY_NAME', 'SITE_MY_URL', 
        'EMAIL_HOST_USER', 'LINK_REL_STATUTEN', 'LINK_REL_REGLEMENT', 
        'MAP_CENTER_LAT', 'MAP_CENTER_LONG', 'MAP_CENTER_ZOOM'
    )
    if name in whitelist:
        return getattr(settings, name, "")
    return '[not permitted]'
 
