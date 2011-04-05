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

SDB_DOMAIN_TO_USE = getattr(settings, "SDB_DOMAIN", 'aprilcountrystocks')

# a few helper functions
def day_of_year_to_date(year, day_of_year):
    ''' Given a year and day of year (1-366),
        this function returns the date of given day. '''
    # 1 January of whatever year
    first_of_year = date(year, 1, 1)
    # subtrack 1 from day_of_year because we are
    # adding to 1 January rather than 0 January
    day_as_date = first_of_year + timedelta(day_of_year-1)
    return day_as_date

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

def reconcile_country_interactively(term):
    try:
        country = Country.objects.get(printable_name=term)
        return country
    except ObjectDoesNotExist:
        try:
            country = Country.lookup(term)
            if country is not None:
                return country
            else:
                print "Could not reconcile '%s'" % (term)
                # cast set as list to preserve order
                matches = list(Country.closest_to(term))
                for n, match in enumerate(matches):
                    print "Type %s for %s" % (n, match.name)
                choice = raw_input("Choose a match and press enter or press enter to skip:")
                if choice not in [None, "", " "]:
                    choice_num = int(choice)
                    country = matches[choice_num]
                    alt = AltCountry(country=country, alternate=term)
                    alt.save()
                    return country
                else:
                    return None
        except Exception, e:
            print 'BANG'
            print e
            import ipdb;ipdb.set_trace()

def reconcile_vaccine_interactively(term, country_pk):
    try:
        vaccine = Vaccine.objects.get(name__istartswith=term)
        return vaccine
    except MultipleObjectsReturned:
        try:
            print "MULTIPLE"
            matches = Vaccine.objects.filter(name__istartswith=term)
            print "Could not reconcile '%s'" % (term)
            # cast set as list to preserve order
            for n, match in enumerate(matches):
                print "Type %s for %s" % (n, match.name)
            choice = raw_input("Choose a match and press enter or press enter to skip:")
            if choice not in [None, "", " "]:
                choice_num = int(choice)
                vax = matches[choice_num]
                #alt = AltVaccine(vaccine=vax, alternate=term)
                #alt.save()
                return vax 
            else:
                return None
        except Exception, e:
            print 'BANG'
            print e
            import ipdb; ipdb.set_trace()
    except ObjectDoesNotExist:
        try:
            vaccine = Vaccine.country_aware_lookup(term, country_pk)
            if vaccine is not None:
                return vaccine 
            else:
                print ""
                print ""
                print "Could not reconcile '%s'" % (term)
                # cast set as list to preserve order
                matches, matches_in_stock = Vaccine.country_aware_closest_to(term, country_pk)
                if matches_in_stock is not None:
                    all_matches = list(set(matches.union(matches_in_stock)))
                    print "** indicates vaccine country has in stock"
                    print ""
                else:
                    all_matches = list(matches)
                for n, match in enumerate(all_matches):
                    if matches_in_stock is not None:
                        if match in matches_in_stock:
                            print " *%s* for %s" % (n, match)
                        else:
                            print "  %s  for %s" % (n, match)
                    else:
                        print " %s for %s" % (n, match)
                choice = raw_input("Choose a match and press enter or press enter to skip:")
                if choice not in [None, "", " "]:
                    choice_num = int(choice)
                    vax = all_matches[choice_num]
                    country = Country.objects.get(pk=country_pk)
                    alt = AltVaccine(vaccine=vax, country=country, alternate=term)
                    alt.save()
                    return vax 
                else:
                    return None
        except Exception, e:
            print 'BANG lookup'
            print e
            import ipdb;ipdb.set_trace()

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
            domain = sdb.create_domain(SDB_DOMAIN_TO_USE)

            titles = []
            stocks = []
            last_amount = 1

            # XXX temp
            products = []
            unmatched_products = []
            matched_groups = []

            skips = ["", " "]
            vax_skips = ["", " "]
            for r in range(int(sheet.nrows)):
                types = sheet.row_types(r)
                values = sheet.row_values(r)
                if types.count(1) == types.count(2):
                    # expecting two words (1) and two numbers (2)
                    try:
                        country = None
                        term = values[0]
                        if term not in skips:
                            country = reconcile_country_interactively(term)
                        if country is None:
                            if term not in skips:
                                print "cannot reconcile '%s'" % (term)
                                print "moving on..."
                                skips.append(term)
                                break

                    except Exception, e:
                        print 'BANG'
                        break

                    year = int(values[1])

                    # day of year 1-365 (sometimes 366)
                    day_of_year = int(values[2][-3:])

                    day = day_of_year_to_date(year, day_of_year)

                    vax = values[2][:-4]
                    try:
                        if vax not in vax_skips:
                            vaccine = reconcile_vaccine_interactively(vax, country.iso2_code)
                        if vaccine is None:
                            #print "cannot find vax: '%s'" % (vax)
                            if vax not in vax_skips:
                                print "cannot reconcile '%s'" % (vax)
                                print "moving on..."
                                vax_skips.append(vax)
                            if vax not in unmatched_products:
                                unmatched_products.append(vax)
                            continue
                        if isinstance(vaccine, str):
                            #print vaccine
                            if vax not in matched_groups:
                                matched_groups.append(vax)
                            continue
                        vax_slug = vaccine.slug
                        if vax_slug not in products:
                            products.append(vax_slug)
                    except Exception, e:
                        print e
                        print "cannot find vax: '%s'" % (vax)
                        continue

                    '''
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

                    cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                    cs_item = domain.new_item(cs_item_name)
                    cs_item.add_value("country", str(country.iso2_code))
                    cs_item.add_value("supply", str(vax_slug))
                    cs_item.add_value("type", "CS")
                    cs_item.save()
                    cs, csc = CountryStock.objects.get_or_create(vaccine=vaccine, country=country)
                    cs.md5_hash = cs_item_name
                    cs.save()
                    '''
                else:
                    titles.append(values)
            #print len(titles)
            #print len(stocks)
            print set(products)
            print set(unmatched_products)
            print set(matched_groups)
            import ipdb; ipdb.set_trace()


def import_allocation_table(file="UNICEF SD - 2008 YE Allocations + Country Office Forecasts 2008.xls"):
    target_sheet = 'allocations'
    book = xlrd.open_workbook(file)

    if book.datemode not in (0,1):
        return "oops. unknown datemode!"

    def xldate_to_datetime(xldate):
        return datetime.datetime(*xlrd.xldate_as_tuple(xldate, book.datemode))

    def xldate_to_date(xldate):
        if isinstance(xldate, int):
            return xldate_to_datetime(xldate).date()
        else:
            return None

    sheets = book.sheet_names()
    sheet = None
    if target_sheet in sheets:
        sheet = book.sheet_by_name(target_sheet)

    if sheet is None:
        return "oops. expecting sheet named '%s'" % (target_sheet)

    column_names = sheet.row_values(0)

    # XXX temp
    products = []
    unmatched_products = []
    matched_groups = []

    skips = ['', ' ']
    for r in range(int(sheet.nrows))[1:]:
        rd = dict(zip(column_names, sheet.row_values(r)))
        try:
            country = None
            if rd['Country'] not in skips:
                country = reconcile_country_interactively(rd['Country'])
            if country is None:
                if rd['Country'] not in skips:
                    print "cannot reconcile '%s'" % (rd['Country'])
                    print "moving on..."
                    skips.append(rd['Country'])
                continue
        except Exception, e:
            print 'BANG'
            print e
            import ipdb;ipdb.set_trace()
            #continue

        # XXX temporary
        '''
        chad = Country.objects.get(iso2_code='TD')
        senegal = Country.objects.get(iso2_code='SN')
        mali = Country.objects.get(iso2_code='ML')

        if country not in [senegal, chad, mali]:
            continue
        '''

        vaccine = Vaccine.lookup_slug(rd['Product'])
        if vaccine is None:
            #print "oops. could not find vaccine '%s'" % (rd['Product'])
            if rd['Product'] not in unmatched_products:
                unmatched_products.append(rd['Product'])
            continue

        if isinstance(vaccine, str):
            #print vaccine
            if rd['Product'] not in matched_groups:
                matched_groups.append(rd['Product'])
            continue

        vax_slug = vaccine.slug
        if vax_slug not in products:
            products.append(vax_slug)
        # XXX temporary
        '''
        targets = [u'bcg-10',u'measles',u'dtp-10',u'tt-10',u'dtp-hepb-2',u'yf-1',u'dtp-hepbhib-1',u'opv-50']
        if vax_slug not in targets:
            continue


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
            domain = sdb.create_domain(SDB_DOMAIN_TO_USE)

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
                    allocation_type = 'FP'

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
            try:
                cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                cs_item = domain.new_item(cs_item_name)
                cs_item.add_value("country", str(country.iso2_code))
                cs_item.add_value("supply", str(vax_slug))
                cs_item.add_value("type", "CS")
                cs_item.save()
                cs, csc = CountryStock.objects.get_or_create(vaccine=vaccine, country=country)
                cs.md5_hash = cs_item_name
                cs.save()
            except Exception, e:
                print 'error creating countrystock item'
                print e
                import ipdb;ipdb.set_trace()
        '''
    print set(products)
    print set(unmatched_products)
    print set(matched_groups)
    import ipdb; ipdb.set_trace()


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

    column_names = sheet.row_values(0)

    # XXX temp
    products = []
    unmatched_products = []
    matched_groups = []

    skips = ["", " "]
    for r in range(int(sheet.nrows))[1:]:
        rd = dict(zip(column_names, sheet.row_values(r)))
        try:
            country = None
            if rd['Country'] not in skips:
                country = reconcile_country_interactively(rd['Country'])
            if country is None:
                if rd['Country'] not in skips:
                    print "cannot reconcile '%s'" % (rd['Country'])
                    print "moving on..."
                    skips.append(rd['Country'])
                continue
        except Exception, e:
            continue

        # XXX temporary
        '''
        chad = Country.objects.get(iso2_code='TD')
        senegal = Country.objects.get(iso2_code='SN')
        mali = Country.objects.get(iso2_code='ML')

        if country not in [senegal, chad, mali]:
            continue
        '''

        vaccine = Vaccine.lookup_slug(rd['Product'])
        if vaccine is None:
            #print "oops. could not find vaccine '%s'" % (rd['Product'])
            if rd['Product'] not in unmatched_products:
                unmatched_products.append(rd['Product'])
            continue

        if isinstance(vaccine, str):
            #print vaccine
            if rd['Product'] not in matched_groups:
                matched_groups.append(rd['Product'])
            continue

        vax_slug = vaccine.slug
        # XXX temporary
        '''
        targets = [u'bcg-10',u'measles',u'dtp-10',u'tt-10',u'dtp-hepb-2',u'yf-1',u'dtp-hepbhib-1',u'opv-50']
        if vax_slug not in targets:
            continue
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
            domain = sdb.create_domain(SDB_DOMAIN_TO_USE)

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

            try:
                cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                cs_item = domain.new_item(cs_item_name)
                cs_item.add_value("country", str(country.iso2_code))
                cs_item.add_value("supply", str(vax_slug))
                cs_item.add_value("type", "CS")
                cs_item.save()
                cs, csc = CountryStock.objects.get_or_create(vaccine=vaccine, country=country)
                cs.md5_hash = cs_item_name
                cs.save()
            except Exception, e:
                print 'error creating countrystock item'
                print e
        '''
    print set(products)
    print set(unmatched_products)
    print set(matched_groups)
    import ipdb; ipdb.set_trace()

def import_country_forecasting_data(file="UNICEF SD - 2010 Country Forecasting Data.xls", yr="2010"):
    sheetname = "forecasting %s" % (yr)
    book = xlrd.open_workbook(file)

    if book.datemode not in (0,1):
        return "oops. unknown datemode!"

    def xldate_to_datetime(xldate):
        return datetime(*xlrd.xldate_as_tuple(xldate, book.datemode))

    def xldate_to_date(xldate):
        if isinstance(xldate, int):
            return xldate_to_datetime(xldate).date()
        else:
            return None

    sheets = book.sheet_names()
    sheet = None
    if sheetname in sheets:
        sheet = book.sheet_by_name(sheetname)

    if sheet is None:
        return "oops. expecting sheet named '%s'" % (sheetname)

    column_names = sheet.row_values(0)

    # XXX temp
    products = []
    unmatched_products = []
    matched_groups = []

    skips = ["", " "]
    for r in range(int(sheet.nrows))[1:]:
        rd = dict(zip(column_names, sheet.row_values(r)))
        try:
            country = None
            if rd['Country'] not in skips:
                country = reconcile_country_interactively(rd['Country'])
            if country is None:
                if rd['Country'] not in skips:
                    print "cannot reconcile '%s'" % (rd['Country'])
                    print "moving on..."
                    skips.append(rd['Country'])
                continue
        except Exception, e:
            continue

        # XXX temporary
        '''
        chad = Country.objects.get(iso2_code='TD')
        senegal = Country.objects.get(iso2_code='SN')
        mali = Country.objects.get(iso2_code='ML')

        if country not in [senegal, chad, mali]:
            continue
        '''

        vaccine = Vaccine.lookup_slug(rd['Product'])
        if vaccine is None:
            #print "oops. could not find vaccine '%s'" % (rd['Product'])
            if rd['Product'] not in unmatched_products:
                unmatched_products.append(rd['Product'])
            continue

        if isinstance(vaccine, str):
            #print vaccine
            if rd['Product'] not in matched_groups:
                matched_groups.append(rd['Product'])
            continue

        vax_slug = vaccine.slug
        if vax_slug not in products:
            products.append(vax_slug)
        # XXX temporary
        '''
        targets = [u'bcg-10',u'measles',u'dtp-10',u'tt-10',u'dtp-hepb-2',u'yf-1',u'dtp-hepbhib-1',u'opv-50']
        if vax_slug not in targets:
            continue

        allocation_type = 'CF'

        amount = int(rd['Total no. of doses'])

        year = int(yr)

        if amount is not None:
            sdb = boto.connect_sdb()
            domain = sdb.create_domain(SDB_DOMAIN_TO_USE)

            try:
                item_name = hashlib.md5()
                item_name.update(str(country.iso2_code))
                item_name.update(str(vax_slug))
                item_name.update(allocation_type)
                item_name.update(str(amount))

                item = domain.new_item(item_name.hexdigest())
                item.add_value("country", str(country.iso2_code))
                item.add_value("supply", str(vax_slug))
                item.add_value("type", allocation_type)
                item.add_value("year", str(year))
                item.add_value("amount", str(amount))
                item.save()
                print item
            except Exception, e:
                print 'error creating stock level'
                print e

            try:
                cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                cs_item = domain.new_item(cs_item_name)
                cs_item.add_value("country", str(country.iso2_code))
                cs_item.add_value("supply", str(vax_slug))
                cs_item.add_value("type", "CS")
                cs_item.save()
                cs, csc = CountryStock.objects.get_or_create(vaccine=vaccine, country=country)
                cs.md5_hash = cs_item_name
                cs.save()
            except Exception, e:
                print 'error creating countrystock item'
                print e
                import ipdb;ipdb.set_trace()
        '''
    print set(products)
    print set(unmatched_products)
    print set(matched_groups)
    import ipdb; ipdb.set_trace()
