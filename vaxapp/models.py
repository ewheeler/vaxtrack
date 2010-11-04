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

class Country(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)

    printable_name = models.CharField(max_length=80)
    iso2_code = models.CharField(max_length=2, primary_key=True)
    iso3_code = models.CharField(max_length=3, blank=True, null=True)
    numerical_code = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.printable_name

    class Meta:
        verbose_name_plural = "countries"

    @classmethod
    def all_names(klass):
        ''' Returns a list of all Country names. '''
        return [c.name for c in klass.objects.all()]

    @classmethod
    def as_tuples(klass):
        ''' Returns a list of 2-tuples for choices field. '''
        return [(c.iso3_code,c.name) for c in klass.objects.all()]

    @classmethod
    def as_tuples_for_admin(klass):
        ''' Returns a list of 2-tuples for choices field. '''
        return [(c.iso3_code, c.iso3_code + " (" + c.name + ")") for c in klass.objects.all()]


class VaccineGroup(models.Model):
    abbr_en = models.CharField(max_length=160, blank=True, null=True)
    abbr_fr = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.abbr_en


class Vaccine(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    slug = models.CharField(max_length=160, blank=True, null=True)
    group = models.ForeignKey(VaccineGroup)

    abbr_en = models.CharField(max_length=30, blank=True, null=True)
    abbr_fr = models.CharField(max_length=30, blank=True, null=True)
    abbr_fr_alt = models.CharField(max_length=30, blank=True, null=True)

    def __unicode__(self):
        return self.slug

    @property
    def abbr(self):
        return self.abbr_en


class CountryStock(models.Model):
    vaccine = models.ForeignKey(Vaccine)
    country = models.ForeignKey(Country)

    def __unicode__(self):
        return "%s: %s" % (self.country.printable_name, self.vaccine)

    class Meta:
        permissions = (
            ("can_upload", "Can upload"),
        )


class UserProfile(models.Model):
    user = models.ForeignKey(User)
    country = models.ForeignKey(Country, blank=True, null=True)

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
