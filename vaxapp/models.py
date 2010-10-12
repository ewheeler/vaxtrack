#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import json
from operator import attrgetter

from django.db import models

class Country(object):
    ''' Provides a model-like interface and simple API 
        for country information, which is loaded from a JSON file. '''

    world = json.load(open('vaxapp/world.json'))

    def __init__(self, d):
        self.iso_code = d['iso2_code']
        self.iso3_code = d['iso3_code']
        self.printable_name = d['printable_name']
        self.name = d['name']
        self.numerical_code = d['numerical_code']

    def __unicode__(self):
        return self.printable_name

    @classmethod
    def filter(klass, attr, value):
        # XXX creates new (or duplicate) Country
        # objects upon each call. i don't think thats
        # a problem because they should not be modified
        # and will get garbage-collected eventually.
        # perhaps there is a better way...
        matches = []
        for d in klass.world:
            if attr in d:
                if d[attr] == value:
                    matches.append(Country(d))
        return matches

    @classmethod
    def get(klass, query):
        ''' Returns a single Country (or False) matching iso_code query. '''
        dicts = klass.filter('iso2_code', query)
        if len(dicts) == 1:
            return dicts[0]
        else:
            return False

    @classmethod
    def all(klass):
        ''' Returns a list of all Country objects in alphabetical order. '''
        return sorted([Country(d) for d in klass.world], key=attrgetter('name'))

    @classmethod
    def all_names(klass):
        ''' Returns a list of all Country names in alphabetical order. '''
        return [c.name for c in klass.all()]


'''
class Country(models.Model):
    # TODO use flat json file for countries?
    name = models.CharField(max_length=160, blank=True, null=True)

    printable_name = models.CharField(max_length=80)
    iso_code = models.CharField(max_length=2, primary_key=True)
    iso3_code = models.CharField(max_length=3, blank=True, null=True)
    numerical_code = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.printable_name

    class Meta:
        verbose_name_plural = "countries"
'''

class Vaccine(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    abbr = models.CharField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return self.abbr

class CountryStock(models.Model):
    vaccine = models.ForeignKey(Vaccine)
    #country = models.ForeignKey(Country)
    country = models.CharField(max_length=4, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.country, self.vaccine)
