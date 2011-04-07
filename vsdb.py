#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from operator import itemgetter
import hashlib

from vaxapp.models import *
import boto
from boto.sdb.db.model import Model
from boto.sdb.db.property import *
from boto.sdb.db.manager import sdbmanager

SDB_DOMAIN_TO_USE = getattr(settings, "SDB_DOMAIN", 'mangocountrystocks')

# not sure how to use these models exactly...
# http://groups.google.com/group/boto-users/browse_thread/thread/3bc0feb15183cf2a/3e44b4e7bbd44fae?lnk=gst&q=sdb#3e44b4e7bbd44fae
# http://cloudcarpenters.com/blog/simpledb_primer_with_python_and_boto/
class Vaxtrack(Model):
    country = StringProperty()
    product = StringProperty()
    group = StringProperty()
    type = StringProperty()
    date = DateProperty()
    # added year to ease lookups because comparisons are lexicographic
    # http://docs.amazonwebservices.com/AmazonSimpleDB/2009-04-15/DeveloperGuide/index.html?UsingSelectOperators.html 
    year = IntegerProperty()
    amount = IntegerProperty()

#Vaxtrack._manager = sdbmanager.SDBManager( Vaxtrack, "countrystockdata", None, None, 'sdb.amazonaws.com', None, None, None, False ) 
# boto models don't seem to work exactly as expected (some stuff is not implemented),
# so here is an alternate interface... that hopefully can be swapped out easily
# if boto's model implementation improves
field_types = {
    'country' : StringProperty(),
    'product' : StringProperty(),
    'group' : StringProperty(),
    'type' : StringProperty(),
    'date' : DateProperty(),
    'year' : IntegerProperty(),
    'amount' : IntegerProperty(),
}

def _decode_item(item):
    ''' Decodes all string values from boto Items into appropriate
        python types based on field_types mapping. Returns a dict. '''
    dict = {}
    for field in field_types.iterkeys():
        if field in item:
            # use boto's decoding methods to give us proper date objects
            # instead of strings
            decoded = sdbmanager.SDBConverter(Vaxtrack._manager).decode_prop(field_types[field], item[field])
            # boto's models encode integers (and longs) before saving to sdb
            # by adding the largest possible integer to your value before
            # saving to sdb
            # http://github.com/boto/boto/commit/6829e6cb491a8c8d07dbe78ac3ef1d67d6fe89f6
            # my guess is that this allows one to use order_by on sdb
            # integer attributes (since all comparisons are lexicographic).
            # 
            # since we did not encode our integers in this way (TODO?),
            # we have to undo the decoding step (subtracting the max int)
            if field in ['year', 'amount']:
                decoded += 2147483648
            dict.update({field:decoded})
    return dict 

def decode_results(results):
    ''' Decodes all results from a boto SelectResultSet.
        Returns a list of dicts. '''
    #return [_decode_item(result) for result in results]
    decoded_results = []
    for result in results:
        dict = {}
        for field in field_types.iterkeys():
            if field in result:
                # use boto's decoding methods to give us proper date objects
                # instead of strings
                decoded = sdbmanager.SDBConverter(Vaxtrack._manager).decode_prop(field_types[field], result[field])
                # boto's models encode integers (and longs) before saving to sdb
                # by adding the largest possible integer to your value before
                # saving to sdb
                # http://github.com/boto/boto/commit/6829e6cb491a8c8d07dbe78ac3ef1d67d6fe89f6
                # my guess is that this allows one to use order_by on sdb
                # integer attributes (since all comparisons are lexicographic).
                # 
                # since we did not encode our integers in this way (TODO?),
                # we have to undo the decoding step (subtracting the max int)
                if field in ['year', 'amount']:
                    decoded += 2147483648
                dict.update({field:decoded})
        decoded_results.append(dict)
    return decoded_results

def sort_results_asc(list, attr):
    return sorted(list, key=itemgetter(attr))

def sort_results_desc(list, attr):
    return sorted(list, key=itemgetter(attr), reverse=True)

cached_year_results = {}
def sdb_type_for_year(country, year, product, type):

    vaccine = Vaccine.objects.get(slug=product)
    group = vaccine.group.slug

    # TODO cache results better!
    search = hashlib.md5()
    search.update(str(country))
    search.update(str(year))
    search.update(str(group))
    search.update(str(type))
    hashed = search.hexdigest()

    if hashed in cached_year_results:
        result = cached_year_results[hashed]
    else:
        sdb = boto.connect_sdb()
        cs = sdb.get_domain(SDB_DOMAIN_TO_USE)
        query = "SELECT * FROM `%s` WHERE `country`='%s' AND `year`='%s' AND `group`='%s' AND `type`='%s'" % (SDB_DOMAIN_TO_USE, country, year, group, type)
        result = cs.select(query)
        cached_year_results.update({hashed:result})

    return result

cached_results = {}
def sdb_get_all_type(country, product, type):

    vaccine = Vaccine.objects.get(slug=product)
    group = vaccine.group.slug

    # TODO cache results better!
    search = hashlib.md5()
    search.update(str(country))
    search.update(str(group))
    search.update(str(type))
    hashed = search.hexdigest()

    if hashed in cached_results:
        result = cached_results[hashed]
    else:
        sdb = boto.connect_sdb()
        cs = sdb.get_domain(SDB_DOMAIN_TO_USE)
        query = "SELECT * FROM `%s` WHERE `country`='%s' AND `group`='%s' AND `type`='%s'" % (SDB_DOMAIN_TO_USE, country, group, type)
        result = cs.select(query)
        cached_results.update({hashed:result})

    return result

def sdb_get_all_cs():
    sdb = boto.connect_sdb()
    cs = sdb.get_domain(SDB_DOMAIN_TO_USE)
    query = "SELECT * FROM `%s` WHERE `type`='CS'" % (SDB_DOMAIN_TO_USE)
    result = cs.select(query)
    return result

def sdb_clear_all_except_sl():
    sdb = boto.connect_sdb()
    cs = sdb.get_domain(SDB_DOMAIN_TO_USE)
    query = "SELECT * FROM `%s` WHERE `type`!='SL'" % (SDB_DOMAIN_TO_USE)
    result = cs.select(query)
    for res in result:
        res.delete()

group_cached_year_results = {}
def group_type_for_year(country, year, group_slug, type):

    # TODO cache results better!
    search = hashlib.md5()
    search.update(str(country))
    search.update(str(year))
    search.update(str(group_slug))
    search.update(str(type))
    hashed = search.hexdigest()

    if hashed in cached_year_results:
        result = cached_year_results[hashed]
    else:
        sdb = boto.connect_sdb()
        cs = sdb.get_domain(SDB_DOMAIN_TO_USE)
        query = "SELECT * FROM `%s` WHERE `country`='%s' AND `year`='%s' AND `group`='%s' AND `type`='%s'" % (SDB_DOMAIN_TO_USE, country, year, group_slug, type)
        result = cs.select(query)
        group_cached_year_results.update({hashed:result})

    return result

group_cached_results = {}
def group_all_type(country, group_slug, type):

    # TODO cache results better!
    search = hashlib.md5()
    search.update(str(country))
    search.update(str(group_slug))
    search.update(str(type))
    hashed = search.hexdigest()

    if hashed in cached_results:
        result = cached_results[hashed]
    else:
        sdb = boto.connect_sdb()
        cs = sdb.get_domain(SDB_DOMAIN_TO_USE)
        query = "SELECT * FROM `%s` WHERE `country`='%s' AND `group`='%s' AND `type`='%s'" % (SDB_DOMAIN_TO_USE, country, group_slug, type)
        result = cs.select(query)
        group_cached_results.update({hashed:result})

    return result


def multikeysort(items, columns):
    from operator import itemgetter
    comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]  
    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(fn(left), fn(right))
            if result:
                return mult * result
        else:
            return 0
    return sorted(items, cmp=comparer)

# PRODUCT API
def all_stocklevels_desc(country, product):
    return sort_results_desc(decode_results(sdb_get_all_type(country, product, 'SL')), 'date')

def all_stocklevels_asc(country, product):
    return sort_results_asc(decode_results(sdb_get_all_type(country, product, 'SL')), 'date')

def all_forecasts_asc(country, product):
    return sort_results_asc(decode_results(sdb_get_all_type(country, product, 'CF')), 'year')

def all_deliveries_for_type_asc(country, product, type):
    return sort_results_asc(decode_results(sdb_get_all_type(country, product, type)), 'date')

def forecast_for_year(country, product, year):
    return decode_results(sdb_type_for_year(country, year, product, 'CF'))

def type_for_year_asc(country, product, type, year):
    return sorted(decode_results(sdb_type_for_year(country, year, product, type)), key=itemgetter('date'))

def type_for_year(country, product, type, year):
    return decode_results(sdb_type_for_year(country, year, product, type))

# GROUP API
def get_group_all_stocklevels_desc(country, group):
    return sort_results_desc(decode_results(group_all_type(country, group, 'SL')), 'date')

def get_group_all_stocklevels_asc(country, group):
    return sort_results_asc(decode_results(group_all_type(country, group, 'SL')), 'date')

def get_group_all_forecasts_asc(country, group):
    return sort_results_asc(decode_results(group_all_type(country, group, 'CF')), 'year')

def get_group_all_deliveries_for_type_asc(country, group, type):
    return sort_results_asc(decode_results(group_all_type(country, group, type)), 'date')

def get_group_forecast_for_year(country, group, year):
    return decode_results(group_type_for_year(country, year, group, 'CF'))

def get_group_type_for_year_asc(country, group, type, year):
    return sorted(decode_results(group_type_for_year(country, year, group, type)), key=itemgetter('date'))

def get_group_type_for_year(country, group, type, year):
    return decode_results(group_type_for_year(country, year, group, type))

