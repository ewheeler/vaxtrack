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

from vaxapp.models import *

def import_fr(file='fr_names.semi'):

    dialect = csv.excel_tab

    # for some reason, sniffer was finding '"'
    #dialect.quotechar = '"'
    #csvee.seek(0)

    def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                                dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            yield [unicode(cell, 'utf-8') for cell in row]

    def utf_8_encoder(unicode_csv_data):
        for line in unicode_csv_data:
            yield line.decode('latin').encode('utf-8')

    reader = unicode_csv_reader(open(file), dialect=dialect, delimiter=";",\
        quoting=csv.QUOTE_ALL, doublequote=True)

    try:
        print 'begin rows'
        row_count = 0


        for row in reader:
            row_count += 1

            try:
                country = Country.objects.get(iso2_code=row[1])
                country.name_fr = unicode(row[0])
                country.save()
            except ObjectDoesNotExist:
                print "'%s' not found" % (row[1])
            continue


    except csv.Error, e:
        # TODO handle this error?
        print('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_fr(sys.argv) 
