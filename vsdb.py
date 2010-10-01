#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from vaxapp.models import *
import boto
from boto.sdb.db import model
from boto.sdb.db import property
from boto.sdb.db import manager

# not sure how to use these models exactly...
# http://groups.google.com/group/boto-users/browse_thread/thread/3bc0feb15183cf2a/3e44b4e7bbd44fae?lnk=gst&q=sdb#3e44b4e7bbd44fae
# http://cloudcarpenters.com/blog/simpledb_primer_with_python_and_boto/
class CountryStock(model.Model):
    country = property.StringProperty()
    supply = property.StringProperty()
    type = property.StringProperty()
    date = property.DateProperty()
    amount = property.IntegerProperty()


def mali():
    sdb = boto.connect_sdb()
    cs = sdb.get_domain('countrystocks')
    return cs.select("SELECT * FROM `countrystocks` WHERE `country`='ML'")

def chad():
    sdb = boto.connect_sdb()
    cs = sdb.get_domain('countrystocks')
    return cs.select("SELECT * FROM `countrystocks` WHERE `country`='TD'")

def forecast_for_year(country, year):
    sdb = boto.connect_sdb()
    cs = sdb.get_domain('countrystocks')
    query = "SELECT * FROM `countrystocks` WHERE `country`='%s' AND `date`='%s' order by `date` asc" % (country, year)
    return cs.select(query)
