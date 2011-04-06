#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import hashlib

from django.core.exceptions import MiddlewareNotUsed
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from vaxapp.models import *
import vsdb

# XXX TODO
# this should be eliminated in favor of a recurring
# celery task.. so a running install will be able to
# update itself with new countrystocks that are created
# in sdb by data-processing EC2s
#
# but until then ...

class StartupMiddlewareHack():
    def __init__(self):
        print 'SYNCHRONIZING COUNTRYSTOCKS...'
        # get all countrystocks from cloud
    	sdb_cs = vsdb.sdb_get_all_cs()

        for cs in sdb_cs:
            try:
                my_cs = CountryStock.objects.get(md5_hash = cs.name)
                # if a countrystock with same hash exists locally,
                # move on to the next one
                continue

            except ObjectDoesNotExist:
                # otherwise if a matching countrystock does not
                # exist locally, create it
                try:
                    # get the vaccine and country
                    vaccine = Vaccine.objects.get(slug=cs['product'])
                    country = Country.objects.get(iso2_code=cs['country'])

                except ObjectDoesNotExist:
                    # if vaccine or country lookup fails, move on
                    print 'PROBLEM WITH VACCINE SLUG OR COUNTRY CODE'
                    print 'MAKE SURE FIXTURES HAVE BEEN LOADED'
                    continue

                except KeyError:
                    # if vaccine or country lookup fails, move on
                    print 'PROBLEM WITH COUNTRY STOCK'
                    print 'MAKE SURE SDB DOMAIN SETTING IS CORRECT'
                    continue

                # create countrystock if its not here locally
                countrystock = CountryStock(country=country, group=vaccine.group)
                countrystock.save()
                # save hash to local db so it will be found next time around
                countrystock.set_md5()
                print 'NEW COUNTRYSTOCK:'
                print countrystock

        # finally, tell django not to use this 
        # middleware for any subsequent requests
        # (so this only runs once at first request)
        raise MiddlewareNotUsed
