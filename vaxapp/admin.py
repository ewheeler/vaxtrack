#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from .models import *

admin.site.register(Country)
admin.site.register(Region)
admin.site.register(Vaccine)
admin.site.register(CountryStock)
admin.site.register(StockLevel)
admin.site.register(Forecast)
admin.site.register(Delivery)
