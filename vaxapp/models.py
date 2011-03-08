#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import json
import uuid
import datetime
from operator import attrgetter

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

class Country(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    name_fr = models.CharField(max_length=160, blank=True, null=True)

    printable_name = models.CharField(max_length=80)
    iso2_code = models.CharField(max_length=2, primary_key=True)
    iso3_code = models.CharField(max_length=3, blank=True, null=True)
    numerical_code = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.printable_name

    class Meta:
        verbose_name_plural = "countries"

    @classmethod
    def lookup(klass, term):
        try:
            match = None
            for obj in klass.objects.all():
                fields = []
                fields.append(obj.name)
                fields.append(obj.name_fr)
                fields.append(obj.iso2_code)
                fields.append(obj.iso3_code)
                fields.append(obj.numerical_code)
                if term.upper() in [f for f in fields if f is not None]:
                    match = obj
                    break
            return match
        except Exception, e:
            print 'BANG'
            print e

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

    @classmethod
    def dump_dict_for_bs(klass):
        d = {}
        for c in klass.objects.all():
            d.update({c.name:c.iso3_code})
        return d


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
    abbr_en_alt = models.CharField(max_length=30, blank=True, null=True)
    abbr_fr = models.CharField(max_length=30, blank=True, null=True)
    abbr_fr_alt = models.CharField(max_length=30, blank=True, null=True)

    def __unicode__(self):
        alternates = [a for a in [self.abbr_en, self.abbr_en_alt, self.abbr_fr,\
            self.abbr_fr_alt] if a not in ['', None]]
        if len(alternates) > 0:
            return "%s (%s)" % (self.slug, ",".join(alternates))
        else:
            return self.slug

    @property
    def abbr(self):
        return self.abbr_en

    @classmethod
    def lookup_slug(klass, term):
        try:
            match = None
            for obj in klass.objects.all():
                fields = []
                fields.append(obj.slug)
                fields.append(obj.abbr_en)
                fields.append(obj.abbr_en_alt)
                fields.append(obj.abbr_fr)
                fields.append(obj.abbr_fr_alt)
                if term.lower() in [f.lower() for f in fields if f is not None]:
                    match = obj
                    break
            if match is None:
                for obj in klass.objects.all():
                    fields = []
                    fields.append(obj.group.abbr_en)
                    fields.append(obj.group.abbr_fr)
                    if term.lower() in [f.lower() for f in fields if f is not None]:
                        return 'matched a group'
            return match
        except Exception, e:
            print 'BANG'
            print e

    @classmethod
    def dump_dict_for_bs(klass):
        d = {}
        for obj in klass.objects.all():
            val = obj.slug
            if val not in ['', ' ', None]:
                fields = []
                fields.append(obj.slug)
                fields.append(obj.abbr_en)
                fields.append(obj.abbr_en_alt)
                fields.append(obj.abbr_fr)
                fields.append(obj.abbr_fr_alt)
                clean_fields = []
                for f in fields:
                    if f not in ['', ' ', None]:
                        d.update({f.lower(): val})
        print len(d.keys())
        return d

class CountryStock(models.Model):
    vaccine = models.ForeignKey(Vaccine)
    country = models.ForeignKey(Country)

    def __unicode__(self):
        return "%s: %s" % (self.country.printable_name, self.vaccine)

    class Meta:
        permissions = (
            ("can_upload", "Can upload"),
        )

class Dicty(models.Model):
    ''' not pretty, but more useful than stashing dicts
    as TextFields with repr/eval...
    These should only be accessed from CountryStockStats,
    as names are NOT unique.'''
    name = models.CharField(max_length=160)

    @classmethod
    def create(klass, name, d):
        # TODO better handling of other types?
        assert(isinstance(d, dict))
        dicty = klass(name=name)
        dicty.save()
        for k,v in d.iteritems():
            kv = KeyVal(dicty=dicty, key=k, val=v)
            kv.save()
        return dicty

    @property
    def as_dict(self):
        return dict(((kv.key, kv.val) for kv in self.keyval_set.all()))

class KeyVal(models.Model):
    dicty = models.ForeignKey(Dicty)
    key = models.CharField(max_length=160)
    val = models.CharField(max_length=160, blank=True, null=True)

class CountryStockStats(models.Model):
    countrystock = models.ForeignKey(CountryStock)
    analyzed = models.DateTimeField(blank=True, null=True)
    reference_date = models.DateField(blank=True, null=True)

    consumed_in_year = models.ForeignKey(Dicty, blank=True, null=True, related_name='consumed_in_year')
    actual_cons_rate = models.ForeignKey(Dicty, blank=True, null=True, related_name='actual_cons_rate')
    annual_demand = models.ForeignKey(Dicty, blank=True, null=True, related_name='annual_demand')
    # TODO these are incorrectly named! should be three_by_year
    # and nine_by_year to reflect the corresponding variable that is stashed here
    three_month_buffers = models.ForeignKey(Dicty, blank=True, null=True, related_name='three_month_buffers')
    nine_month_buffers = models.ForeignKey(Dicty, blank=True, null=True, related_name='nine_month_buffers')

    # other values
    est_daily_cons = models.IntegerField(blank=True, null=True)
    days_of_stock = models.IntegerField(blank=True, null=True)

    doses_delivered_this_year = models.IntegerField(blank=True, null=True)
    doses_on_orders = models.IntegerField(blank=True, null=True)
    demand_for_period = models.IntegerField(blank=True, null=True)
    percent_coverage = models.FloatField(blank=True, null=True)

    # helper properties to return Dicty attributes as dicts
    @property
    def get_consumed_in_year(self):
        return self.consumed_in_year.as_dict

    @property
    def get_actual_cons_rate(self):
        return self.actual_cons_rate.as_dict

    @property
    def get_annual_demand(self):
        return self.annual_demand.as_dict

    @property
    def get_three_month_buffers(self):
        # TODO see above
        return self.three_month_buffers.as_dict

    @property
    def get_nine_month_buffers(self):
        # TODO see above
        return self.nine_month_buffers.as_dict

class Alert(models.Model):
    ALERT_STATUS = (
        ('U', 'urgent'),
        ('R', 'resolved'),
        ('W', 'warning'),
    )
    countrystock = models.ForeignKey(CountryStock)
    text = models.CharField(max_length=160, blank=True, null=True)
    status = models.CharField(max_length=2, default='U', choices=ALERT_STATUS, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s - %s" % (self.countrystock.country.iso2_code, self.countrystock.vaccine, self.text)

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

    date_created = models.DateTimeField(_("Date Created"), default=datetime.datetime.utcnow)

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
                now = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
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
