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

def import_vax(file='vaccines.csv'):

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
        print 'begin rows'
        row_count = 0


        for row in reader:
            row_count += 1

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

            vg = None
            if has_data(row, ['group__abbr_en', 'group__abbr_fr']):
                vg, vgb= VaccineGroup.objects.get_or_create(abbr_en=row['group__abbr_en'], abbr_fr=row['group__abbr_fr'])

            if not vgb:
                if has_datum(row, 'group__abbr_en'):
                    vg, vgen= VaccineGroup.objects.get_or_create(abbr_en=row['group__abbr_en'], abbr_fr=row['group__abbr_fr'])
            if vg is not None:
                try:
                    # remove group info, if it exists
                    en = row.pop('group__abbr_en')
                    fr = row.pop('group__abbr_fr')
                except Exception, e:
                    pass

                v = Vaccine(**row)
                v.slug = slugify(row['abbr_en'])
                v.group = vg
                v.save()


            else:
                print 'OOPS. MOVING ON'
                continue
            continue


    except csv.Error, e:
        # TODO handle this error?
        print('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_csv(sys.argv) 
