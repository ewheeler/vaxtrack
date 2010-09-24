#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os

from django.conf.urls.defaults import *
from django.contrib import admin
import views

admin.autodiscover()

urlpatterns = patterns('',
    # serve assets via django, during development
    url(r'^assets/js/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/javascripts"}),
    url(r'^$', views.index),
    url(r'^charts/(?P<country_pk>\w+)-(?P<vaccine_abbr>\w+).png$', views.chart_country, name="chart-country"),
    url(r'^admin/', include(admin.site.urls)),
)
