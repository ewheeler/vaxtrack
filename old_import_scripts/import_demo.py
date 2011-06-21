#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import sys
import os
import codecs
import csv
import datetime
import re

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import setup_environ
from django.template.defaultfilters import slugify

from decimal import Decimal as D

#try:
#    import settings
#    setup_environ(settings)
#except:
#    sys.exit("No settings found")
import hashlib
import boto


from vaxapp.models import *

def import_demo(file=None):
    sdb = boto.connect_sdb()
    domain = sdb.create_domain('demodata')

    # use codecs.open() instead of open() so all characters are utf-8 encoded
    # BEFORE we start dealing with them (just in case)
    # rU option is for universal-newline mode which takes care of \n or \r etc
    csvee = codecs.open(file, "rU", encoding='utf-8', errors='ignore')

    # sniffer attempts to guess the file's dialect e.g., excel, etc
    #dialect = csv.Sniffer().sniff(csvee.read(1024))
    dialect = csv.excel_tab

    # for some reason, sniffer was finding '"'
    #dialect.quotechar = '"'
    csvee.seek(0)

    # DictReader uses first row of csv as key for data in corresponding column
    reader = csv.DictReader(csvee, dialect=dialect, delimiter=",",\
        quoting=csv.QUOTE_ALL, doublequote=True)

    try:
        last_stock = 0
        print 'begin rows'
        row_count = 0
        for country, forecasts in {'ML': {'2007': 860966, '2008': 861581,'2009': 759600,'2010': 754923}, 'TD':{'2007': 694555,'2008': 694555,'2009': 738391,'2010':738283}}.items():
            for year, doses in forecasts.items():
                try:
                    item_name = hashlib.md5()
                    item_name.update(str(country))
                    item_name.update(str('BCG'))
                    item_name.update("CF")
                    item_name.update(str(year))
                    item_name.update(str(doses))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country))
                    item.add_value("supply", str('BCG'))
                    item.add_value("type", "CF")
                    item.add_value("date", str(year))
                    item.add_value("year", str(year))
                    item.add_value("amount", str(doses))
                    item.save()
                    print item
                except Exception, e:
                    print 'error creating forecast'
                    print e

        for row in reader:
            row_count += 1
            if row_count % 400 == 0:
                print row_count

            def has_datum(row, key):
                if row.has_key(key):
                    if row[key] is not None:
                        if row[key] != "":
                            return True
                return False

            def has_data(row, key_list):
                if False in [has_datum(row, key) for key in key_list]:
                    return False
                else:
                    return True

            def only_digits(raw_str):
                cleaned = re.sub("[^0-9]", "", raw_str) 
                if cleaned != "":
                    return cleaned
                else:
                    return None

            def format_date(datestr):
                # expecting MM/DD/YY
                if datestr is not None:
                    if datestr != '':
                        month, day, year = datestr.split('/')
                        real_year = '20' + year
                        try:
                            return datetime(month=int(month),\
                                day=int(day), year=int(real_year)).date()
                        except Exception, e:
                            print 'BANG format date'
                            print e
                            import ipdb;ipdb.set_trace()
                    else:
                        return None
                else:
                    return None

            def create_record(country, type, date_obj, clean_amount):
                try:
                    item_name = hashlib.md5()
                    item_name.update(str(country.iso2_code))
                    item_name.update(str('BCG'))
                    item_name.update(str(type))
                    item_name.update(str(date_obj))
                    item_name.update(str(clean_amount))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country.iso2_code))
                    item.add_value("supply", str('BCG'))
                    item.add_value("type", str(type))
                    item.add_value("date", str(date_obj))
                    item.add_value("year", str(date_obj.year))
                    item.add_value("amount", str(clean_amount))
                    item.save()
                    print item
                except Exception, e:
                    print 'error creating record'
                    print e

            if has_datum(row, 'Country'):
                country = Country.lookup(row['Country'])

                if has_datum(row, 'Vaccine'):
                    vax = Vaccine.lookup_slug(row['Vaccine'])
                    country_stock, c = CountryStock.objects.get_or_create(\
                        vaccine=vax, country=country)


                    if has_data(row, ['Date','BCG WHO stock level']):
                        date_obj = format_date(row['Date'])
                        amt = int(only_digits(row['BCG WHO stock level']))

                        if amt != last_stock:
                            last_stock = amt
                            clean_amount = amt
                            if clean_amount is not None:
                                type = "SL"
                                create_record(country, type, date_obj, clean_amount)

                    if has_datum(row, 'BCG original country forecast'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG original country forecast']))
                        if clean_amount is not None:
                            type='CO'
                            create_record(country, type, date_obj, clean_amount)

                    if has_datum(row, 'BCG Unicef deliveries'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG Unicef deliveries']))
                        if clean_amount is not None:
                            type='UN'
                            create_record(country, type, date_obj, clean_amount)

                    if has_datum(row, 'BCG future delivery on PO'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG future delivery on PO']))
                        if clean_amount is not None:
                            type='FP'
                            create_record(country, type, date_obj, clean_amount)

                    if has_datum(row, 'BCG future delivery on forecast'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG future delivery on forecast']))
                        if clean_amount is not None:
                            type='FF'
                            create_record(country, type, date_obj, clean_amount)


                else:
                    print 'OOPS. MOVING ON'
                    continue
            continue


    except csv.Error, e:
        # TODO handle this error?
        print('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_csv(sys.argv) 
