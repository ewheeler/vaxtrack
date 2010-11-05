#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import sys
from datetime import date
from datetime import datetime
from datetime import timedelta

import xlrd
import hashlib
import boto

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import setup_environ
from django.template.defaultfilters import slugify

from decimal import Decimal as D

from vaxapp.models import *

def import_who(file=None):
    '''
    opv-50
    measles
    tt-10
    dtp-hepbhib-1
    yf-1
    bcg-10
    '''
    book = xlrd.open_workbook(file)
    sheets = book.sheet_names()
    country_names = Country.objects.values_list('printable_name', flat=True)
    sheet = None
    for s in sheets:
        if s in country_names:
            sheet = book.sheet_by_name(s)
            country = Country.objects.get(printable_name=s)
            break

    if sheet is not None:
        sdb = boto.connect_sdb()
        domain = sdb.create_domain('countrystockdata')

        titles = []
        stocks = []
        for r in range(int(sheet.nrows)):
            types = sheet.row_types(r)
            values = sheet.row_values(r)
            if types.count(1) == types.count(2):
                # expecting two words (1) and two numbers (2)
                if country.name != values[0].upper():
                    # TODO better check and error?
                    print 'country name mismatch'
                    break

                year = int(values[1])
                # 1 January of whatever year
                first_of_year = date(year, 1, 1)

                # day of year 1-365 (sometimes 366)
                day_of_year = int(values[2][-3:])

                # subtrack 1 from day_of_year because we are 
                # adding to 1 January rather than 0 January
                day = first_of_year + timedelta(day_of_year-1)

                vax = values[2][:-4]
                try:
                    vaccine = Vaccine.lookup_slug(vax)
                    vax_slug = vaccine.slug
                except Exception, e:
                    print e
                    print 'cannot find vax: %s' % (vax)
                    continue

                amount = int(values[3])
                stocks.append(values)
                try:
                    item_name = hashlib.md5()
                    item_name.update(str(country.iso2_code))
                    item_name.update(str(vax_slug))
                    item_name.update("SL")
                    item_name.update(str(day))
                    item_name.update(str(amount))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country.iso2_code))
                    item.add_value("supply", str(vax_slug))
                    item.add_value("type", "SL")
                    item.add_value("date", str(day))
                    item.add_value("year", str(year))
                    item.add_value("amount", str(amount))
                    item.save()
                    print item
                except Exception, e:
                    print 'error creating stock level'
                    print e

                cs, csc = CountryStock.objects.get_or_create(vaccine=vaccine, country=country)
            else:
                titles.append(values)
        print len(titles)
        print len(stocks)
