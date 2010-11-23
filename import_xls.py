#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import re
import sys
import time
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
        sheet = book.sheet_by_name(s)

        if sheet is not None:
            sdb = boto.connect_sdb()
            domain = sdb.create_domain('countrystockdata')

            titles = []
            stocks = []
            last_amount = 1
            for r in range(int(sheet.nrows)):
                types = sheet.row_types(r)
                values = sheet.row_values(r)
                if types.count(1) == types.count(2):
                    # expecting two words (1) and two numbers (2)
                    try:
                        country = Country.lookup(values[0])
                    except Exception, e:
                        # TODO better check and error?
                        print "could not find country named '%s'" % (values[0])
                        break
                    if country is None:
                        print "could not find country named '%s'" % (values[0])
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
                    if amount == last_amount:
                        continue
                    else:
                        last_amount = amount

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


def only_digits(raw_str):
    cleaned = re.sub("[^0-9]", "", raw_str) 
    if cleaned != "":
        return cleaned
    else:
        return None

def first_monday_of_week(year, week):
    ''' Returns the date of the first monday of a given
        week number and year.'''
    d = date(int(year), 1, 4)  # The Jan 4th must be in week 1  according to ISO
    return d + timedelta(weeks=(int(week)-1), days=-d.weekday())

def import_allocation_table(file="UNICEF SD - 2008 YE Allocations + Country Office Forecasts 2008.xls"):
    target_sheet = 'allocations'
    book = xlrd.open_workbook(file)

    if book.datemode not in (0,1):
        return "oops. unknown datemode!"

    def xldate_to_datetime(xldate):
        return datetime(*xlrd.xldate_as_tuple(xldate, book.datemode))

    def xldate_to_date(xldate):
        return xldate_to_datetime(xldate).date()

    sheets = book.sheet_names()
    sheet = None
    if target_sheet in sheets:
        sheet = book.sheet_by_name(target_sheet)

    if sheet is None:
        return "oops. expecting sheet named '%s'" % (target_sheet)

    country_names = Country.objects.values_list('printable_name', flat=True)
    column_names = sheet.row_values(0)

    for r in range(int(sheet.nrows))[1:]:
        rd = dict(zip(column_names, sheet.row_values(r)))
        try:
            country = Country.lookup(rd['Country'])
        except Exception, e:
            continue

        senegal = Country.objects.get(iso2_code='SN')
        niger = Country.objects.get(iso2_code='NE')

        if country not in [senegal, niger]:
            continue

        vaccine = Vaccine.lookup_slug(rd['Product'])
        if vaccine is None:
            print "oops. could not find vaccine '%s'" % (rd['Product'])
            continue

        vax_slug = vaccine.slug
        allocation_type = None

        try:
            forecast_doses = int(rd['Doses- Forecast '])
        except ValueError:
            forecast_doses = None

        try:
            po_doses = int(rd['Doses- On PO'])
        except ValueError:
            po_doses = None

        try:
            co_forecast = int(rd['Doses- CO Forecast '])
        except ValueError:
            co_forecast = None

        year = int(rd['YYYY'])
        year_month = rd['YYYY-MM']
        year_week = rd['YYYY-WW']
        input_date = xldate_to_date(rd['Input Date'])
        approx_date = None

        file_type = rd['File Type']
        if file_type == 'Weekly':
            yr, week = year_week.split('-')
            approx_date = first_monday_of_week(yr, week)

        if file_type == 'Monthly':
            yr, month = year_month.split('-')
            approx_date = date(int(yr), int(month), 15)

        if approx_date is not None:
            sdb = boto.connect_sdb()
            domain = sdb.create_domain('countrystockdata')

            if forecast_doses > 0:
                amount = forecast_doses
                if approx_date <= date.today():
                    # original CO forecast (CO)
                    allocation_type = 'CO'
                else:
                    # future delivery on forecast (FF)
                    allocation_type = 'FF'

            if po_doses > 0:
                amount = po_doses
                if approx_date <= date.today():
                    # unicef deliveries (UN)
                    allocation_type = 'UN'
                else:
                    # future delivery on PO (FP)
                    allocation_type = 'FF'

            if co_forecast is not None:
                amount = co_forecast
                allocation_type = 'CF'

            if allocation_type is None:
                print 'unknown allocation_type!'
                print rd
                continue

            # TODO save row number
            try:
                item_name = hashlib.md5()
                item_name.update(str(country.iso2_code))
                item_name.update(str(vax_slug))
                item_name.update(allocation_type)
                item_name.update(str(approx_date))
                item_name.update(str(amount))

                item = domain.new_item(item_name.hexdigest())
                item.add_value("country", str(country.iso2_code))
                item.add_value("supply", str(vax_slug))
                item.add_value("type", allocation_type)
                item.add_value("date", str(approx_date))
                item.add_value("year", str(year))
                item.add_value("amount", str(amount))
                item.save()
                print item
            except Exception, e:
                print 'error creating stock level'
                print e
                import ipdb;ipdb.set_trace()


def import_country_forecasts(file="UNICEF SD -  Country Office Forecasts 2010.xls"):
    book = xlrd.open_workbook(file)

    if book.datemode not in (0,1):
        return "oops. unknown datemode!"

    def xldate_to_datetime(xldate):
        return datetime(*xlrd.xldate_as_tuple(xldate, book.datemode))

    def xldate_to_date(xldate):
        return xldate_to_datetime(xldate).date()

    sheets = book.sheet_names()
    sheet = None
    if 'allocations' in sheets:
        sheet = book.sheet_by_name('allocations')

    if sheet is None:
        return "oops. expecting sheet named 'allocations'"

    country_names = Country.objects.values_list('printable_name', flat=True)
    column_names = sheet.row_values(0)

    for r in range(int(sheet.nrows))[1:]:
        rd = dict(zip(column_names, sheet.row_values(r)))
        try:
            # TODO better country lookup
            country = Country.objects.get(printable_name=rd['Country'])
        except Exception, e:
            continue

        senegal = Country.objects.get(iso2_code='SN')
        niger = Country.objects.get(iso2_code='NE')

        if country not in [senegal, niger]:
            continue

        vaccine = Vaccine.lookup_slug(rd['Product'])
        if vaccine is None:
            print "oops. could not find vaccine '%s'" % (rd['Product'])
            continue

        vax_slug = vaccine.slug
        allocation_type = 'CF'

        amount = int(rd['Doses - CO Forecast'])

        year = int(rd['YYYY'])
        year_month = rd['YYYY-MM']
        year_week = rd['YYYY-WW']
        approx_date = None

        yr, month = year_month.split('-')
        approx_date = date(int(yr), int(month), 15)

        if approx_date is not None:
            sdb = boto.connect_sdb()
            domain = sdb.create_domain('countrystockdata')

            try:
                item_name = hashlib.md5()
                item_name.update(str(country.iso2_code))
                item_name.update(str(vax_slug))
                item_name.update(allocation_type)
                item_name.update(str(approx_date))
                item_name.update(str(amount))

                item = domain.new_item(item_name.hexdigest())
                item.add_value("country", str(country.iso2_code))
                item.add_value("supply", str(vax_slug))
                item.add_value("type", allocation_type)
                item.add_value("date", str(approx_date))
                item.add_value("year", str(year))
                item.add_value("amount", str(amount))
                item.save()
                print item
            except Exception, e:
                print 'error creating stock level'
                print e

