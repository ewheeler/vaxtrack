#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import template
from django.utils.encoding import force_unicode
register = template.Library()

def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name.
        Thanks Fotinakis! http://stackoverflow.com/questions/844746/performing-a-getattr-style-lookup-in-a-django-template/1112236#1112236"""

    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and value.has_key(arg):
        return force_unicode(value[arg])
    else:
        return u""


register.filter('getattribute', getattribute)
