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


from vaxapp.models import *

def import_csv(args):

    # use codecs.open() instead of open() so all characters are utf-8 encoded
    # BEFORE we start dealing with them (just in case)
    # rU option is for universal-newline mode which takes care of \n or \r etc
    csvee = codecs.open("chad.csv", "rU", encoding='utf-8', errors='ignore')

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

        mali, m = Country.objects.get_or_create(name="MALI", printable_name="Mali",\
            iso2_code="ML", iso3_code="MLI", numerical_code=466)

        chad, c = Country.objects.get_or_create(name="CHAD", printable_name="Chad",\
            iso2_code="TD", iso3_code="TCD", numerical_code=148)

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
                        return datetime.date(month=int(month),\
                            day=int(day), year=int(real_year))
                    else:
                        return None
                else:
                    return None

            ''' Country
                Vaccine
                YEAR
                Date
                BCG WHO stock level
                BCG Buffer stock
                BCG MALI 3-month buffer stock
                BCG MALI 9-month stock limit
                BCG forecasted stock levels (forecast)
                BCG forecasted stock levels (placed POs)
                BCG original country forecast
                BCG theoretical stock level based on CO forecast
                BCG theoretical stock level based on deliveries
                BCG Unicef deliveries
                BCG future delivery on PO
                BCG future delivery on forecast
                Stock-VPO
                Stock-DTC
                Stock-VAR
                Stock-VAT
                Stock-VAA
                Stock-DTC-HepB
            '''
            if has_datum(row, 'Country'):
                country = Country.objects.get(name__iexact=row['Country'])

                if has_datum(row, 'Vaccine'):
                    vax, v = Vaccine.objects.get_or_create(abbr=row['Vaccine'])
                    country_stock, c = CountryStock.objects.get_or_create(\
                        vaccine=vax, country=country)

                    if has_data(row, ['Date','BCG WHO stock level']):
                        date_obj = format_date(row['Date'])
                        amt = int(only_digits(row['BCG WHO stock level']))

                        if amt != last_stock:
                            last_stock = amt
                            stock_level = StockLevel.objects.create(\
                                country_stock=country_stock, amount=amt,\
                                date=date_obj)

                    if has_datum(row, 'BCG original country forecast'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG original country forecast']))
                        if clean_amount is not None:
                            original_co = Delivery.objects.create(\
                                country_stock=country_stock,date=date_obj,\
                                amount=clean_amount, type='CO')

                    if has_datum(row, 'BCG Unicef deliveries'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG Unicef deliveries']))
                        if clean_amount is not None:
                            unicef = Delivery.objects.create(\
                                country_stock=country_stock,date=date_obj,\
                                amount=clean_amount,type='UN')

                    if has_datum(row, 'BCG future delivery on PO'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG future delivery on PO']))
                        if clean_amount is not None:
                            on_po = Delivery.objects.create(\
                                country_stock=country_stock,date=date_obj,\
                                amount=clean_amount, type='FP')

                    if has_datum(row, 'BCG future delivery on forecast'):
                        date_obj = format_date(row['Date'])
                        clean_amount = int(only_digits(row['BCG future delivery on forecast']))
                        if clean_amount is not None:
                            on_forecast = Delivery.objects.create(\
                                country_stock=country_stock,date=date_obj,\
                                amount=clean_amount, type='FF')

                else:
                    print 'OOPS. MOVING ON'
                    continue
            continue


    except csv.Error, e:
        # TODO handle this error?
        print('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_csv(sys.argv) 
