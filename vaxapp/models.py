#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import json
from operator import attrgetter

from django.db import models
from django.contrib.auth.models import User

class Country(object):
    ''' Provides a model-like interface and simple API 
        for country information, which is loaded from a JSON file. '''

    world = json.load(open('vaxapp/world.json'))

    def __init__(self, d):
        self.iso_code = d['iso2_code']
        self.pk = d['iso2_code']
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
        ''' Returns a list of all Country names. '''
        return [c.name for c in klass.all()]

    @classmethod
    def as_tuples(klass):
        ''' Returns a list of 2-tuples for choices field. '''
        return [(c.iso_code,c.name) for c in klass.all()]

    @classmethod
    def as_tuples_for_admin(klass):
        ''' Returns a list of 2-tuples for choices field. '''
        return [(c.iso_code, c.iso_code + " (" + c.name + ")") for c in klass.all()]


class Vaccine(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    abbr = models.CharField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return self.abbr


class CountryStock(models.Model):
    vaccine = models.ForeignKey(Vaccine)
    country_iso_code = models.CharField(max_length=4, blank=True, null=True,
        choices=Country.as_tuples_for_admin())

    @property
    def country(self):
        return Country.get(self.country_iso_code)

    def __unicode__(self):
        return "%s: %s" % (self.country.printable_name, self.vaccine)


class UserProfile(models.Model):
    user = models.ForeignKey(User)
    country = models.CharField(max_length=4, blank=True, null=True)
