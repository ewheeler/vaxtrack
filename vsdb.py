#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from vaxapp.models import *
import boto
from boto.sdb.db.model import Model
from boto.sdb.db.property import *
from boto.sdb.db.manager import sdbmanager

# not sure how to use these models exactly...
# http://groups.google.com/group/boto-users/browse_thread/thread/3bc0feb15183cf2a/3e44b4e7bbd44fae?lnk=gst&q=sdb#3e44b4e7bbd44fae
# http://cloudcarpenters.com/blog/simpledb_primer_with_python_and_boto/
class Vaxtrack(Model):
    country = StringProperty()
    supply = StringProperty()
    type = StringProperty()
    date = DateProperty()
    # added year to ease lookups because comparisons are lexicographic
    # http://docs.amazonwebservices.com/AmazonSimpleDB/2009-04-15/DeveloperGuide/index.html?UsingSelectOperators.html 
    year = IntegerProperty()
    amount = IntegerProperty()

CountryStock._manager = sdbmanager.SDBManager( CountryStock, "countrystockdata", None, None, 'sdb.amazonaws.com', None, None, None, False ) 
#sdbmanager.SDBConverter(Vaxtrack._manager).decode_prop(StringProperty(), i['country'])

def mali():
    sdb = boto.connect_sdb()
    cs = sdb.get_domain('countrystockdata')
    return cs.select("SELECT * FROM `countrystockdata` WHERE `country`='ML' AND `supply`='BCG'")

def chad():
    sdb = boto.connect_sdb()
    cs = sdb.get_domain('countrystockdata')
    return cs.select("SELECT * FROM `countrystockdata` WHERE `country`='TD' AND `supply`='BCG'")

def forecast_for_year(country, year, supply='BCG'):
    return _type_for_year(country, year, supply, 'CF')

def stocklevels_for_year(country, year, supply='BCG'):
    return _type_for_year(country, year, supply, 'SL')

def original_co_for_year(country, year, supply='BCG'):
    return _type_for_year(country, year, supply, 'CO')

def unicef_deliveries_for_year(country, year, supply='BCG'):
    return _type_for_year(country, year, supply, 'UN')

def future_on_po_for_year(country, year, supply='BCG'):
    return _type_for_year(country, year, supply, 'FP')

def future_on_forecast_for_year(country, year, supply='BCG'):
    return _type_for_year(country, year, supply, 'FF')

def _type_for_year(country, year, supply, type):
    sdb = boto.connect_sdb()
    cs = sdb.get_domain('countrystockdata')
    query = "SELECT * FROM `countrystockdata` WHERE `country`='%s' AND `year`='%s' AND `supply`='%s' AND `type`='%s'" % (country, year, supply, type)
    return cs.select(query)
