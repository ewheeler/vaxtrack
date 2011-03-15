#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import xlwt
from vaxapp.models import *

def go():
    book = xlwt.Workbook()
    sheet = book.add_sheet('Sheet1')

    countries = Country.objects.all()

    attrs = ['name', 'name_fr', 'printable_name', 'iso2_code', 'iso3_code', 'numerical_code']
    for col, attr in enumerate(attrs):
        sheet.write(0, col, attr)

    for row, country in enumerate(countries):
        for column, attr in enumerate(attrs):
            sheet.write(row+1, column, getattr(country, attr))

    book.save('country_names_and_codes.xls')

