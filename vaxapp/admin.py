#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from .models import *

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'date_uploaded', 'date_process_end', 'document_format', 'get_imported_countries', 'get_imported_groups')
    readonly_fields = ('exception', 'remote_document', 'date_revert_start',\
            'date_revert_end', 'reverted_by', 'imported_countries', 'imported_groups',\
            'imported_years', 'date_data_begin', 'date_data_end', 'date_uploaded',\
            'date_process_start', 'date_process_end')

class CountryStockAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'country', 'group')


admin.site.register(Vaccine)
admin.site.register(VaccineGroup)
admin.site.register(Country)
admin.site.register(AltCountry)
admin.site.register(CountryStock, CountryStockAdmin)
admin.site.register(Alert)
admin.site.register(Document, DocumentAdmin)
