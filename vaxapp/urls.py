#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os

from django.conf.urls.defaults import *
from django.contrib import admin
import authority
import views
import nexus
import gargoyle

# sets up the default nexus site by detecting all nexus_modules.py files
nexus.autodiscover()
gargoyle.autodiscover()

admin.autodiscover()
authority.autodiscover()

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('vax.vaxapp',),
}

urlpatterns = patterns('',
    # serve assets via django, during development
    url(r'^assets/js/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/javascripts"}),
    url(r'^assets/flashcanvas/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/flashcanvas"}),
    url(r'^assets/css/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/stylesheets"}),
    url(r'^assets/images/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/images"}),
    url(r'^assets/icons/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/icons"}),
    url(r'^assets/csv/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/csvs"}),
    url(r'^assets/xls/(?P<path>.*)$', "django.views.static.serve",
    {"document_root": os.path.dirname(__file__) + "/static/xls"}),
    url(r'^$', views.index_dev),
    url(r'^dev/$', views.index_dev),
    url(r'^classic/$', views.index),
    url(r'^alerts/(?P<country_pk>\w+)/(?P<group_slug>[\w-]+)$', views.alerts, name="alerts"),
    url(r'^sit-as-of/(?P<country_pk>\w+)/(?P<group_slug>[\w-]+)$', views.sit_as_of, name="sit-as-of"),
    url(r'^stats/(?P<country_pk>\w+)/(?P<group_slug>[\w-]+)$', views.stats, name="stats"),
    url(r'^csv/(?P<country_pk>\w+)/(?P<group_slug>[\w-]+)/(?P<sit_year>\d+)/(?P<sit_month>.*)/(?P<sit_day>\d+)/$', views.get_data),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^uploads/$', views.uploads, name='uploads'),
    url(r'^upload/revert/$', views.revert_upload, name='revert-upload'),
    url(r'^upload/(?P<up_id>[\w-]+)/$', views.upload, name='upload'),
    url(r'^entry/$', views.entry, name='entry'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name':'login.html'}, name="login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name':'loggedout.html'}, name="logout"),
    url(r'^register/$', views.register, name='register'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    url(r'^translations/', include('rosetta.urls'), name='rosetta'),
    url(r'^authority/', include('authority.urls')),
    url(r'^nexus/', include(nexus.site.urls)),
)
