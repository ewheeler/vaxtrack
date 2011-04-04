#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import json
import uuid
import datetime
import hashlib
from operator import attrgetter
from operator import itemgetter

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from dameraulevenshtein import dameraulevenshtein as dm

class AltCountry(models.Model):
    country = models.ForeignKey("Country")
    alternate = models.CharField(max_length=160)


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
        verbose_name = _("country")
        verbose_name_plural = _("countries")

    @property
    def en(self):
        return self.name

    @property
    def fr(self):
        return self.name_fr

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
            if match is None:
                # if no matches found, check for alternates
                alternates = AltCountry.objects.filter(alternate__iexact=term)
                if bool(alternates):
                    # if any alternates are found, return the first one
                    match = alternates[0].country
            return match
        except Exception, e:
            print 'BANG'
            print e

    @classmethod
    def closest_to(klass, term):
        try:
            # grr edge cases...
            if 'OPT' in term.upper():
                term = 'palestinian'
            if 'PALESTINE' in term.upper():
                term = 'palestinian'
            if "SERBIA" in term.upper():
                term = 'serbia and montenegro'
            if "LIBYA" in term.upper():
                term = 'libyan arab JAMAHIRIYA'
            if "DRC" in term.upper():
                term = 'congo'
            if "IVORY" in term.upper():
                term = "COTE D'IVOIRE"
            if "VERT" in term.upper():
                term = "cape verde"
            # words to exclude when attempting to match country names
            exclude = set(["democratic", "peoples", "republic", "the", "of", "american", "french", "brazzaville", "islamic", "people's", "territory", "kingdom", "démocratique", "république", "territories", "françaises", "française", "islands", "british", "britannique", "américaines", "britanniques", "western", "occidental", "république-unie", "république", "l'ex-république", "démocratique", "equatorial", "équatoriale", "territoire", "plurinational", "américaines", "conakry", "states", "états", "outlying", "éloignées", "federation", "fédération", "pays", "sultanate"])
            # replace hyphens, exclude any words from exclude set, and pluck the longest remaining word
            big_term = max(set(term.lower().replace('-', ' ').split()).difference(exclude), key=len)
            country_tuples = []
            for obj in klass.objects.all():
                big_en = ""
                big_fr = ""
                if obj.name is not None:
                    # pluck longest word in english name that does not appear in exclude
                    big_en = max(set(word.lower().strip(",") for word in obj.name.replace('-', ' ').split()).difference(exclude), key=len)
                    # calculate edit distance between word from term and word from english name
                    country_tuples.append((dm(big_term, big_en), obj, obj.name))
                if obj.name_fr is not None:
                    # pluck longest word in french name that does not appear in exclude
                    big_fr = max(set(word.lower().strip(",") for word in obj.name_fr.replace('-', ' ').split()).difference(exclude), key=len)
                    if big_fr != big_en:
                        # calculate edit distance between word from term and word from french name
                        country_tuples.append((dm(big_term, big_fr), obj, obj.name_fr))

            # sort tuples by ascending edit distance, pluck the 5 closest matches
            closest = sorted(country_tuples, key=itemgetter(0))[:5]
            # return only the objects
            return set(map(itemgetter(1), closest))
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

    @property
    def en(self):
        return self.abbr_en

    @property
    def fr(self):
        return self.abbr_fr


class AltVaccine(models.Model):
    vaccine = models.ForeignKey("Vaccine")
    country = models.ForeignKey("Country")
    alternate = models.CharField(max_length=160)


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

    class Meta:
        verbose_name = _("vaccine")
        verbose_name_plural = _("vaccines")

    @property
    def abbr(self):
        return self.abbr_en

    @property
    def en(self):
        if self.abbr_en is not None:
            return self.abbr_en

    @property
    def fr(self):
        if self.abbr_fr is not None:
            return self.abbr_fr

    @classmethod
    def lookup_slug(klass, term):
        try:
            match = None
            for obj in klass.objects.all():
                fields = []
                fields.append(obj.slug)
                fields.append(obj.abbr_en)
                fields.append(obj.abbr_en_alt)
                #fields.append(obj.abbr_fr)
                #fields.append(obj.abbr_fr_alt)
                if term.lower().replace('+','-') in [f.lower().replace('+','-') for f in fields if f is not None]:
                    match = obj
                    break
            if match is None:
                '''
                for obj in klass.objects.all():
                    fields = []
                    fields.append(obj.group.abbr_en)
                    #fields.append(obj.group.abbr_fr)
                    if term.lower() in [f.lower() for f in fields if f is not None]:
                        return 'matched a group'
                '''
                # if no matches found, check for alternates
                alternates = AltVaccine.objects.filter(alternate__iexact=term)
                if bool(alternates):
                    # if any alternates are found, return the first one
                    match = alternates[0].vaccine
            return match
        except Exception, e:
            print 'BANG'
            print e

    @classmethod
    def country_aware_lookup(klass, term, country_pk):
        try:
            match = None
            for obj in klass.objects.all():
                fields = []
                fields.append(obj.slug)
                fields.append(obj.abbr_en)
                fields.append(obj.abbr_en_alt)
                #fields.append(obj.abbr_fr)
                #fields.append(obj.abbr_fr_alt)
                if term.lower().replace('+','-') in [f.lower().replace('+','-') for f in fields if f is not None]:
                    match = obj
                    break
            if match is None:
                '''
                for obj in klass.objects.all():
                    fields = []
                    fields.append(obj.group.abbr_en)
                    #fields.append(obj.group.abbr_fr)
                    if term.lower() in [f.lower() for f in fields if f is not None]:
                        return 'matched a group'
                '''
                # if no matches found, check for alternates
                alternates = AltVaccine.objects.filter(alternate__iexact=term, country=country_pk)
                if bool(alternates):
                    # if any alternates are found, return the first one
                    match = alternates[0].vaccine
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

    @classmethod
    def closest_to(klass, term):
        try:
            # words to exclude when attempting to match country names
            exclude = set(["vaccine"])
            big_term = term.lower()
            vax_tuples = []
            for obj in klass.objects.all():
                big_en = ""
                big_fr = ""
                if obj.abbr_en is not None:
                    big_en = obj.abbr_en.lower()
                    # calculate edit distance between word from term and word from english name
                    vax_tuples.append((dm(big_term, big_en), obj, obj.abbr_en))
                if obj.abbr_fr is not None:
                    big_fr = obj.abbr_fr.lower()
                    if big_fr != big_en:
                        # calculate edit distance between word from term and word from french name
                        vax_tuples.append((dm(big_term, big_fr), obj, obj.abbr_fr))

            # sort tuples by ascending edit distance, pluck the 5 closest matches
            closest = sorted(vax_tuples, key=itemgetter(0))[:10]
            # return only the objects
            return set(map(itemgetter(1), closest))
        except Exception, e:
            print 'BANG'
            print e

    @classmethod
    def country_aware_closest_to(klass, term, country_pk):
        try:
            big_term = term.lower()
            countrystocks = CountryStock.objects.filter(country=country_pk)
            # fetch all vaccines that this country has stocks of
            cs_vaccines = map(attrgetter('vaccine'), countrystocks)

            vax_tuples = []
            for obj in klass.objects.all():
                big_en = ""
                big_fr = ""
                if obj.abbr_en is not None:
                    big_en = obj.abbr_en.lower()
                    # calculate edit distance between word from term and word from english name
                    vax_tuples.append((dm(big_term, big_en), obj, obj.abbr_en))
                if obj.abbr_fr is not None:
                    big_fr = obj.abbr_fr.lower()
                    if big_fr != big_en:
                        # calculate edit distance between word from term and word from french name
                        vax_tuples.append((dm(big_term, big_fr), obj, obj.abbr_fr))

            # sort tuples by ascending edit distance, pluck closest matches
            closest = sorted(vax_tuples, key=itemgetter(0))[:10]
            # return only the objects
            only_objs = set(map(itemgetter(1), closest))

            # see if any closest matches are vaccines this country stocks
            if only_objs.isdisjoint(set(cs_vaccines)):
                # if not, return top matches
                return only_objs[:10], None
            else:
                # if so, return the intersection
                return only_objs.difference(set(cs_vaccines)), only_objs.intersection(set(cs_vaccines))

        except Exception, e:
            print 'BANG'
            print e


class CountryStock(models.Model):
    vaccine = models.ForeignKey(Vaccine)
    country = models.ForeignKey(Country)
    md5_hash = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return "%s: %s" % (self.country.printable_name, self.vaccine)

    class Meta:
        permissions = (
            ("can_upload", "Can upload"),
        )

    @property
    def latest_stats(self):
        css = self.countrystockstats_set.all().order_by('-analyzed')
        if css.count() > 0:
            return css[0]
        else:
            return None

    @property
    def get_md5(self):
        return self.md5_hash

    def set_md5(self):
        self.md5_hash = hashlib.md5(self.country.iso2_code + self.vaccine.slug).hexdigest()
        self.save()

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
    three_by_year = models.ForeignKey(Dicty, blank=True, null=True, related_name='three_by_year')
    nine_by_year = models.ForeignKey(Dicty, blank=True, null=True, related_name='nine_by_year')
    days_of_stock_data = models.ForeignKey(Dicty, blank=True, null=True, related_name='days_of_stock_data')

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
        if self.consumed_in_year is not None:
            return self.consumed_in_year.as_dict

    @property
    def get_actual_cons_rate(self):
        if self.actual_cons_rate is not None:
            return self.actual_cons_rate.as_dict

    @property
    def get_annual_demand(self):
        if self.annual_demand is not None:
            return self.annual_demand.as_dict

    @property
    def get_three_by_year(self):
        if self.three_by_year is not None:
            return self.three_by_year.as_dict

    @property
    def get_nine_by_year(self):
        if self.nine_by_year is not None:
            return self.nine_by_year.as_dict

    @property
    def get_days_of_stock_data(self):
        if self.days_of_stock_data is not None:
            return self.days_of_stock_data.as_dict

class Alert(models.Model):
    ALERT_STATUS = (
        ('U', _('urgent')),
        ('R', _('resolved')),
        ('W', _('warning')),
    )
    RISK_TYPE = (
        ('O', _('risk of overstock')),
        ('S', _('risk of stockout')),
        ('F', _('further analysis needed')),
        ('U', _('unknown')),
    )
    ADVICE = (
        ('D', _('delay or reduce shipment')),
        ('I', _('order immediately, insufficient doses on upcoming deliveries')),
        ('F', _('order immediately, purchase forecasted delivery')),
        ('P', _('order immediately, no doses on PO or forecasted in next 3 months')),
        ('E', _('delay shipment, excessive doses on upcoming deliveries')),
        ('O', _('delay order, delay purchase of forecasted delivery')),
        ('C', _('major difference between forecast and actual consumption rates')),
        ('U', _('unknown or error')),
    )

    countrystock = models.ForeignKey(CountryStock)
    analyzed = models.DateTimeField(blank=True, null=True)
    reference_date = models.DateField(blank=True, null=True)

    text = models.CharField(max_length=2, default='U', choices=ADVICE, blank=True, null=True)
    status = models.CharField(max_length=2, default='U', choices=ALERT_STATUS, blank=True, null=True)
    risk = models.CharField(max_length=2, default='U', choices=RISK_TYPE, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s - %s" % (self.countrystock.country.iso2_code,\
            self.countrystock.vaccine, self.get_text_display())

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
