#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import json
import uuid
from datetime import datetime
from operator import attrgetter

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

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

    class Meta:
        permissions = (
            ("can_upload", "Can upload"),
        )


class UserProfile(models.Model):
    user = models.ForeignKey(User)
    country = models.CharField(max_length=4, blank=True, null=True)

DOCUMENT_STATES = (
    ('U', _('Uploaded')),
    ('S', _('Stored Remotely')),
    ('Q', _('Queued')),
    ('P', _('Processing')),
    ('F', _('Finished')),
    ('E', _('Processing Error')))


DEFAULT_PATH = os.path.join(settings.MEDIA_ROOT, "uploads")
UPLOAD_PATH = getattr(settings, "CSV_UPLOAD_PATH", DEFAULT_PATH)


class Document(models.Model):
    """
    A simple model which stores data about an uploaded document.
    """
    user = models.ForeignKey(User, verbose_name=_('user'))
    name = models.CharField(_("Title"), max_length=100)
    uuid = models.CharField(_('Unique Identifier'), max_length=36)
    local_document = models.FileField(_("Local Document"), null=True, blank=True, upload_to=UPLOAD_PATH)
    remote_document = models.URLField(_("Remote Document"), null=True, blank=True)
    status = models.CharField(_("Remote Processing Status"), default='U', max_length=1, choices=DOCUMENT_STATES)
    exception = models.TextField(_("Processing Exception"), null=True, blank=True)

    date_uploaded = models.DateTimeField(_("Date Uploaded"))
    date_stored = models.DateTimeField(_("Date Stored Remotely"), null=True, blank=True)
    date_queued = models.DateTimeField(_("Date Queued"), null=True, blank=True)
    date_process_start = models.DateTimeField(_("Date Process Started"), null=True, blank=True)
    date_process_end = models.DateTimeField(_("Date Process Completed"), null=True, blank=True)
    date_exception = models.DateTimeField(_("Date of Exception"), null=True, blank=True)

    date_created = models.DateTimeField(_("Date Created"), default=datetime.utcnow)

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')

    def __unicode__(self):
        return unicode(_("%s's uploaded document." % self.user))

    def save(self, **kwargs):
        if self.id is None:
            self.uuid = str(uuid.uuid4())
        super(Document, self).save(**kwargs)

    @staticmethod
    def process_response(data):
        c = boto.connect_s3()
        key = c.get_bucket(data['bucket']).get_key(data['key'])
        if key is not None:
            response_data = json.loads(key.get_contents_as_string())
            doc = Document.objects.get(uuid=response_data['uuid'])
            status = response_data['status']
            now = response_data.get("now", None)
            if now is not None:
                now = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
            if status == 'E':
                doc.status = "E"
                doc.exception = response_data.get('exception', None)
                doc.date_exception = now
            if status == 'F':
                if doc.status != 'E':
                    doc.status = 'F'
                doc.date_process_end = now
            if status == 'P':
                if doc.status not in ('E', 'F'):
                    doc.status = 'P'
                doc.date_process_start = now
            doc.save()
            return True
        return False
