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

SDB_DOMAIN_TO_USE = getattr(settings, "SDB_DOMAIN", 'papayacountrystocks')

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

def reconcile_country_silently(term):
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
                #TODO guess? or skip?
                #return matches[0]
                return None
        except Exception, e:
            print 'BANG'
            print e

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
                alt = AltVaccine(vaccine=vax, alternate=term)
                alt.save()
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
                    try:
                        choice_num = int(choice)
                        vax = all_matches[choice_num]
                    except ValueError:
                        vax = Vaccine.objects.get(slug=choice)
                    country = Country.objects.get(iso2_code=country_pk)
                    alt = AltVaccine(vaccine=vax, country=country, alternate=term)
                    alt.save()
                    return vax 
                else:
                    return None
        except Exception, e:
            print 'BANG lookup'
            print e
            import ipdb; ipdb.set_trace()

def reconcile_vaccine_silently(term, country_pk):
    try:
        vaccine = Vaccine.objects.get(name__istartswith=term)
        return vaccine
    except MultipleObjectsReturned:
        try:
            #TODO guess? or skip?
            #matches = Vaccine.objects.filter(name__istartswith=term)
            #return matches[0]
            return None
        except Exception, e:
            print 'BANG'
            print e
    except ObjectDoesNotExist:
        try:
            vaccine = Vaccine.country_aware_lookup(term, country_pk)
            if vaccine is not None:
                return vaccine
            else:
                matches, matches_in_stock = Vaccine.country_aware_closest_to(term, country_pk)
                if matches_in_stock is not None:
                    all_matches = list(set(matches.union(matches_in_stock)))
                else:
                    all_matches = list(matches)
                #TODO guess? or skip?
                #return all_matches[0]
                return None
        except Exception, e:
            print 'BANG lookup'
            print e

def import_who(file=None, interactive=True, dry_run=False, upload=None):
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
                            if interactive:
                                country = reconcile_country_interactively(term)
                            else:
                                country = reconcile_country_silently(term)
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
                            if interactive:
                                vaccine = reconcile_vaccine_interactively(vax, country.iso2_code)
                            else:
                                vaccine = reconcile_vaccine_silently(vax, country.iso2_code)
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
                        vax_group = vaccine.group.slug
                        if vax_slug not in products:
                            products.append(vax_slug)
                    except Exception, e:
                        print e
                        print "cannot find vax: '%s'" % (vax)
                        continue

                    amount = int(values[3])
                    if amount == last_amount:
                        continue
                    else:
                        last_amount = amount

                    stocks.append(values)
                    try:
                        if not dry_run:
                            item_name = hashlib.md5()
                            item_name.update(str(country.iso2_code))
                            item_name.update(str(vax_slug))
                            item_name.update(str(vax_group))
                            item_name.update("SL")
                            item_name.update(str(day))
                            item_name.update(str(amount))

                            item = domain.new_item(item_name.hexdigest())
                            item.add_value("country", str(country.iso2_code))
                            item.add_value("product", str(vax_slug))
                            item.add_value("group", str(vax_group))
                            item.add_value("type", "SL")
                            item.add_value("date", str(day))
                            item.add_value("year", str(year))
                            item.add_value("amount", str(amount))
                            item.add_value("activity", "unknown")
                            item.add_value("upload", upload)
                            item.save()
                            print item
                        else:
                            item = dict()
                            item['country'] = str(country.iso2_code)
                            item['product'] = str(vax_slug)
                            item['group'] = str(vax_group)
                            item['type'] = "SL"
                            item['date'] = str(day)
                            item['year'] = str(year)
                            item['amount'] = str(amount)
                            item['activity'] = str(activity)
                            print item
                    except Exception, e:
                        print 'error creating stock level'
                        print e

                    if not dry_run:
                        cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                        cs_item = domain.new_item(cs_item_name)
                        cs_item.add_value("country", str(country.iso2_code))
                        cs_item.add_value("product", str(vax_slug))
                        cs_item.add_value("type", "CS")
                        cs_item.save()
                        cs, csc = CountryStock.objects.get_or_create(group=vaccine.group, country=country)
                        cs.products.add(vaccine)
                        cs.md5_hash = cs_item_name
                        cs.save()
                else:
                    titles.append(values)
            #print len(titles)
            #print len(stocks)
            print set(products)
            print set(unmatched_products)
            print set(matched_groups)
    return True


def import_all_unicef():
    # 2008
    print import_unicef("UNICEF SD - 2008 Country Forecasting Data.xls")
    print import_unicef("UNICEF SD - 2008 YE Allocations + Country Office Forecasts 2008.xls")
    # 2009
    print import_unicef("UNICEF SD - 2009 Country Forecasting Data.xls")
    print import_unicef("UNICEF SD - 2009 YE Allocations + Country Office Forecasts 2009.xls")
    # 2010
    print import_unicef("UNICEF SD - 2010 Country Forecasting Data.xls")
    print import_unicef("UNICEF SD -  Country Office Forecasts 2010.xls")
    print import_unicef("2010_12 UNICEF SD - All Table Vaccines.xls")
    # 2011
    print import_unicef("UNICEF SD - 2011 Country Forecasting Data - CLEANED COUNTRY NAMES.xls")
    print import_unicef("UNICEF SD - 2011 Country Office Forecasts - CLEANED COUNTRY NAMES.xls")
    print import_unicef("2011_03 UNICEF SD - All Table Vaccines - CLEANED.xls")

def import_unicef(file="", interactive=True, dry_run=False, upload=None):
    print file
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
    # grab any sheets starting with 'forecasting'
    forecasting_sheets = [s for s in sheets if s.startswith("forecasting")]
    sheet = None

    # find the target sheet...
    # which is usually allocations for country forecasts
    # and allocations files, but sometimes Sheet1
    if 'allocations' in sheets:
        sheet = book.sheet_by_name('allocations')
    elif 'Allocations' in sheets:
        sheet = book.sheet_by_name('Allocations')
    elif 'Sheet1' in sheets:
        sheet = book.sheet_by_name('Sheet1')
    else:
        if len(forecasting_sheets) > 0:
            # the desired sheet in country forecasting files 
            # includes the year, so it varies
            sheet = book.sheet_by_name(forecasting_sheets[0])
            # we need to know the year later on, so parse out and save
            year = int(forecasting_sheets[0].split()[1])
        else:
            return "oops. could not find valid sheet"

    column_names = sheet.row_values(0)

    # XXX temp
    products = []
    unmatched_products = []
    matched_groups = []

    # countries to skip
    skips = ['', ' ']
    # products to skip
    vax_skips = ['', ' ']
    for r in range(int(sheet.nrows))[1:]:
        rd = dict(zip(column_names, sheet.row_values(r)))
        try:
            country = None
            if rd['Country'] not in skips:
                if interactive:
                    country = reconcile_country_interactively(rd['Country'])
                else:
                    country = reconcile_country_silently(rd['Country'])
            if country is None:
                if rd['Country'] not in skips:
                    print "cannot reconcile '%s'" % (rd['Country'])
                    print "moving on..."
                    skips.append(rd['Country'])
                continue
        except Exception, e:
            print 'BANG'
            print e
            #continue

        chad = Country.objects.get(iso2_code='TD')
        senegal = Country.objects.get(iso2_code='SN')
        mali = Country.objects.get(iso2_code='ML')

        if country not in [senegal, chad, mali]:
            continue

        vax = rd['Product']

        try:
            if vax not in vax_skips:
                if interactive:
                    vaccine = reconcile_vaccine_interactively(vax, country.iso2_code)
                else:
                    vaccine = reconcile_vaccine_silently(vax, country.iso2_code)
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
            vax_group = vaccine.group.slug
            if vax_slug not in products:
                products.append(vax_slug)
        except Exception, e:
            print e
            print "cannot find vax: '%s'" % (vax)
            continue

        vax_slug = vaccine.slug
        vax_group = vaccine.group.slug
        if vax_slug not in products:
            products.append(vax_slug)

        # see if this is a Routine or Supplementary activity
        if 'Type of Activity' in rd:
            activity = rd['Type of Activity']
        elif 'Activity' in rd:
            activity = rd['Activity']
        else:
            activity = 'Unknown'

        allocation_type = None

        try:
            forecast_doses = int(rd['Doses- Forecast '])
        except ValueError:
            forecast_doses = None
        except KeyError:
            forecast_doses = None

        try:
            po_doses = int(rd['Doses- On PO'])
        except ValueError:
            po_doses = None
        except KeyError:
            po_doses = None

        try:
            co_forecast = int(rd['Doses- CO Forecast '])
        except ValueError:
            co_forecast = None
        except KeyError:
            co_forecast = None
            try:
                co_forecast = int(rd['Doses - CO Forecast'])
            except ValueError:
                co_forecast = None
            except KeyError:
                co_forecast = None

        try:
            co_forecasting = int(rd['Total no. of doses'])
            current_stock = rd['Current Stock Qty']
            if current_stock not in ['', ' ', None]:
                init_quant = int(current_stock)
            else:
                init_quant = 0
        except ValueError:
            co_forecasting = None
        except KeyError:
            co_forecasting = None

        approx_date = None
        if 'YYYY' in rd:
            if rd['YYYY'] not in [None, '', ' ']:
                year = int(rd['YYYY'])
        if 'YYYY-MM' in rd:
            year_month = rd['YYYY-MM']
            if year_month not in [None, '', ' ']:
                yr, month = year_month.split('-')
                approx_date = date(int(yr), int(month), 15)
        if 'YYYY-WW' in rd:
            year_week = rd['YYYY-WW']
            if year_week not in [None, '', ' ']:
                yr, week = year_week.split('-')
                approx_date = first_monday_of_week(yr, week)

        if year is None:
            print 'no year!'
        if year is not None:
            sdb = boto.connect_sdb()
            domain = sdb.create_domain(SDB_DOMAIN_TO_USE)

            try:
                if forecast_doses > 0:
                    amount = forecast_doses
                    if approx_date <= date.today():
                        # original CO forecast (CO)
                        # from allocations table
                        allocation_type = 'CO'
                    else:
                        # future delivery on forecast (FF)
                        # from allocations table
                        allocation_type = 'FF'
                elif po_doses > 0:
                    amount = po_doses
                    if approx_date <= date.today():
                        # unicef deliveries (UN)
                        # from allocations table
                        allocation_type = 'UN'
                    else:
                        # future delivery on PO (FP)
                        # from allocations table
                        allocation_type = 'FP'

                elif co_forecast is not None:
                    # original CO forecast (CO)
                    # from country forecasts file
                    amount = co_forecast
                    allocation_type = 'CO'

                elif co_forecasting is not None:
                    # country forecasts (annual demand and initial stock)
                    # from country forecasting file
                    amount = co_forecasting
                    allocation_type = 'CF'

                else:
                    if allocation_type is None:
                        continue
            except Exception, e:
                print 'BANG determine type'
                print e
                import pdb;pdb.set_trace()

            # TODO save row number
            try:
                if not dry_run:
                    item_name = hashlib.md5()
                    item_name.update(str(country.iso2_code))
                    item_name.update(str(vax_slug))
                    item_name.update(str(vax_group))
                    item_name.update(allocation_type)
                    if allocation_type != 'CF':
                        item_name.update(str(approx_date))
                    item_name.update(str(amount))
                    item_name.update(str(activity))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country.iso2_code))
                    item.add_value("product", str(vax_slug))
                    item.add_value("group", str(vax_group))
                    item.add_value("type", allocation_type)
                    if allocation_type != 'CF':
                        item.add_value("date", str(approx_date))
                    item.add_value("year", str(year))
                    item.add_value("amount", str(amount))
                    item.add_value("activity", str(activity))
                    if allocation_type == 'CF':
                        item.add_value("initial", str(init_quant))
                    item.add_value("upload", upload)
                    item.save()
                    print item
                else:
                    item = dict()
                    item['country'] = str(country.iso2_code)
                    item['product'] = str(vax_slug)
                    item['group'] = str(vax_group)
                    item['type'] = allocation_type
                    if allocation_type != 'CF':
                        item['date'] = str(approx_date)
                    item['year'] = str(year)
                    item['amount'] = str(amount)
                    item['activity'] = str(activity)
                    if allocation_type == 'CF':
                        item['initial'] = str(init_quant)
                    print item
            except Exception, e:
                print 'error creating stock level'
                print e
                if interactive:
                    import ipdb;ipdb.set_trace()
            try:
                if not dry_run:
                    cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                    cs_item = domain.new_item(cs_item_name)
                    cs_item.add_value("country", str(country.iso2_code))
                    cs_item.add_value("product", str(vax_slug))
                    cs_item.add_value("type", "CS")
                    cs_item.save()
                    cs, csc = CountryStock.objects.get_or_create(group=vaccine.group, country=country)
                    cs.products.add(vaccine)
                    cs.md5_hash = cs_item_name
                    cs.save()
            except Exception, e:
                print 'error creating countrystock item'
                print e
                if interactive:
                    import ipdb;ipdb.set_trace()
    print set(products)
    print set(unmatched_products)
    print set(matched_groups)
    return True

def import_template(file=None, interactive=True, dry_run=False, upload=None):
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
    for s in sheets:
        sheet = book.sheet_by_name(s)

        if sheet is not None:
            sdb = boto.connect_sdb()
            domain = sdb.create_domain(SDB_DOMAIN_TO_USE)

            # XXX temp
            products = []
            unmatched_products = []
            matched_groups = []

            skips = ["", " "]
            vax_skips = ["", " "]
            for r in range(int(sheet.nrows)):
                try:
                    country = None
                    term = values[0]
                    if term not in skips:
                        if interactive:
                            country = reconcile_country_interactively(term)
                        else:
                            country = reconcile_country_silently(term)
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

                vax = values[3]
                try:
                    if vax not in vax_skips:
                        if interactive:
                            vaccine = reconcile_vaccine_interactively(vax, country.iso2_code)
                        else:
                            vaccine = reconcile_vaccine_silently(vax, country.iso2_code)
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
                    vax_group = vaccine.group.slug
                    if vax_slug not in products:
                        products.append(vax_slug)
                except Exception, e:
                    print e
                    print "cannot find vax: '%s'" % (vax)
                    continue

                amount = int(values[4])
                obs_date = xldate_to_date(values[5])
                # TODO save row number
                try:
                    if not dry_run:
                        item_name = hashlib.md5()
                        item_name.update(str(country.iso2_code))
                        item_name.update(str(vax_slug))
                        item_name.update(str(vax_group))
                        item_name.update(str(obs_date))
                        item_name.update(str(amount))
                        item_name.update(upload)

                        item = domain.new_item(item_name.hexdigest())
                        item.add_value("country", str(country.iso2_code))
                        item.add_value("product", str(vax_slug))
                        item.add_value("group", str(vax_group))
                        item.add_value("type", 'SL')
                        item.add_value("date", str(obs_date))
                        item.add_value("year", str(year))
                        item.add_value("amount", str(amount))
                        item.add_value("upload", upload)
                        item.save()
                        print item
                    else:
                        item = dict()
                        item['country'] = str(country.iso2_code)
                        item['product'] = str(vax_slug)
                        item['group'] = str(vax_group)
                        item['type'] = 'SL'
                        item['date'] = str(obs_date)
                        item['year'] = str(year)
                        item['amount'] = str(amount)
                        item['upload'] = upload
                        print item
                except Exception, e:
                    print 'error creating stock level'
                    print e
                    if interactive:
                        import ipdb;ipdb.set_trace()
                try:
                    if not dry_run:
                        cs_item_name = hashlib.md5(str(country.iso2_code)+str(vax_slug)).hexdigest()
                        cs_item = domain.new_item(cs_item_name)
                        cs_item.add_value("country", str(country.iso2_code))
                        cs_item.add_value("product", str(vax_slug))
                        cs_item.add_value("type", "CS")
                        cs_item.save()
                        cs, csc = CountryStock.objects.get_or_create(group=vaccine.group, country=country)
                        cs.products.add(vaccine)
                        cs.md5_hash = cs_item_name
                        cs.save()
                except Exception, e:
                    print 'error creating countrystock item'
                    print e
                    if interactive:
                        import ipdb;ipdb.set_trace()
        print set(products)
        print set(unmatched_products)
        print set(matched_groups)
    return True
