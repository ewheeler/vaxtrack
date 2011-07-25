#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import itertools
import string

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.core import serializers
from django.utils import simplejson

from .models import *
from .analysis import *
from vax.vaxapp.tasks import *
from . import forms

def index_dev(req, country_pk=None):
    if country_pk is not None:
        countrystocks = CountryStock.objects.filter(country=country_pk)
    else:
        countrystocks = False
    #countrystocks = [c for c in CountryStock.objects.all() if c.has_stock_data]
    countrystocks = [c for c in CountryStock.objects.all() if c.group.slug in ['bcg', 'dtp-hepbhib', 'mea', 'opv', 'tt', 'yf']]
    #countrystocks = [c for c in CountryStock.objects.filter(country__iso2_code='SN') if c.group.slug in ['bcg', 'dtp-hepbhib', 'mea', 'opv', 'tt', 'yf']]
    countries = list(set([c.country for c in countrystocks]))
    groups = list(set([g.group for g in countrystocks]))
    return render_to_response("dev.html",\
        {"countrystocks": countrystocks,\
            "countries": countries,\
            "groups": groups,\
            "tab": "dashboard"},\
            context_instance=RequestContext(req))

def index(req, country_pk=None):
    if country_pk is not None:
        countrystocks = CountryStock.objects.filter(country=country_pk)
    else:
        countrystocks = False
    countrystocks = [c for c in CountryStock.objects.all() if c.group.slug in ['bcg', 'dtp-hepbhib', 'mea', 'opv', 'tt', 'yf']]

    countries = list(set([c.country for c in countrystocks]))
    groups = list(set([g.group for g in countrystocks]))
    return render_to_response("index.html",\
        {"countrystocks": countrystocks,\
            "countries": countries,\
            "groups": groups,\
            "tab": "dashboard"},\
            context_instance=RequestContext(req))

def get_data(req, country_pk, group_slug, sit_year, sit_month, sit_day):
    print "DATA"
    if req.is_ajax():
        data_url_path = "https://s3.amazonaws.com/vaxtrack_csv/" + country_pk + "/" + group_slug + "/" + sit_year + "/" + sit_month + "/"
        data_url_file = country_pk + "_" + group_slug + "_" + sit_year + "_" + sit_month + "_" + sit_day + ".csv"
        data_url = data_url_path + data_url_file
        print data_url
        return HttpResponseRedirect(data_url)

def sit_as_of(req, country_pk, group_slug):
    if req.is_ajax():
        try:
            country_code = country_pk
            if str(country_pk).isdigit():
                country_code = string.uppercase[int(country_pk[:2]) -1] + string.uppercase[int(country_pk[2:]) -1]
            countrystock = CountryStock.objects.filter(country=country_code, group__slug=group_slug)
            if countrystock:
                sit_as_of = Document.get_current_sit_as_of(countrystock[0])
                if sit_as_of:
                    sit_day = sit_as_of.day
                    if sit_day < 10:
                        sit_day = 1;
                    else:
                        sit_day = 15
                    sit_as_of_dict = [{'year': sit_as_of.year, 'month': sit_as_of.month, 'day': sit_day}]
                    return HttpResponse(simplejson.dumps(sit_as_of_dict), 'application/javascript')
            today = datetime.datetime.now()
            return HttpResponse(simplejson.dumps([{'year':today.year, 'month': today.month, 'day': today.day}]), 'application/javascript')
        except Exception, e:
            print 'BANG SIT AS OF'
            print e
            return HttpResponse([], 'application/javascript')

def alerts(req, country_pk, group_slug):
    if req.is_ajax():
        try:
            country_code = country_pk
            if str(country_pk).isdigit():
                country_code = string.uppercase[int(country_pk[:2]) -1] + string.uppercase[int(country_pk[2:]) -1]
            countrystock = CountryStock.objects.filter(country=country_code, group__slug=group_slug)
            alerts = Alert.objects.filter(countrystock=countrystock)
            if len(alerts) == 0:
                return HttpResponse([], 'application/javascript')
            alerts_text = [{'text':alert.get_text_display(), 'status':alert.status, 'reference_date':alert.reference_date.isoformat(), 'analyzed':alert.analyzed.date().isoformat()} for alert in alerts]
            return HttpResponse(simplejson.dumps(alerts_text), 'application/javascript')
        except Exception, e:
            print 'BANG ALERTS'
            print e
            return HttpResponse([], 'application/javascript')

def add_sep(num, sep=','):
    if num is None:
        return None
    s = str(int(num))
    out = ''
    while len(s) > 3:
        out = sep + s[-3:] + out
        s = s[:-3]
    return s + out

def stats(req, country_pk, group_slug):
    if req.is_ajax():
        try:
            country_code = country_pk
            if str(country_pk).isdigit():
                country_code = string.uppercase[int(country_pk[:2]) -1] + string.uppercase[int(country_pk[2:]) -1]
            countrystock = CountryStock.objects.filter(country=country_code, group__slug=group_slug)
            if countrystock.count() > 0:
                css = countrystock[0].latest_stats
                # XXX why isnt this working?
                #if not css.has_stock_data:
                #    return HttpResponse([], 'application/javascript')
                # TODO this is insane
                # instead of the fields, i'd like the properties that return
                # a dict of the related obj rather than pks of related obj
                props_to_get = ['consumed_in_year', 'actual_cons_rate', 'annual_demand', 'three_by_year', 'nine_by_year', 'days_of_stock_data']

                # get a set of years that there may be historical data for
                # by getting the years from a stocklevel stat and a forecats stat
                # this way, if there is no forecast/unicef data for a particular year
                # or no stocklevel data for a particular year, the other data
                # will be shown in the correct column.
                # TODO its probably better in the long run to build the
                # hist tables in a way that does not depend on the orders
                # of several lists in order for the correct data to appear
                # in the correct column...
                years = sorted(list(set(css.get_consumed_in_year.keys() + css.get_annual_demand.keys())))

                stats = {}
                for prop in props_to_get:
                    prop_dict = getattr(css, 'get_' + prop)
                    prop_list = []
                    if prop_dict is not None:
                        for year in years:
                            if year in prop_dict:
                                prop_list.append(prop_dict[year])
                            else:
                                prop_list.append("")
                        stats[prop] = prop_list
                stats['years'] = years

                attrs_to_get = ['est_daily_cons','days_of_stock','doses_delivered_this_year','doses_on_orders','demand_for_period']
                # instead of a for loop, using this strategy: http://news.ycombinator.com/item?id=2320298
                # basically, this avoids having the for loop translated into
                # bytecode by the interpreter and runs in straight c instead
                #
                # also add_sep to these -- my lame js version for the hist
                # table will add commas to these dates
                any(itertools.imap(lambda attr: stats.update({attr: add_sep(getattr(css, attr))}), attrs_to_get))

                if css.percent_coverage is not None:
                    stats['percent_coverage'] = str(int(css.percent_coverage*100.0)) + '%'

                # need isoformat because dates/datetimes aren't serializable
                date_attrs = ['analyzed', 'reference_date']
                for date_attr in date_attrs:
                    # analyzed is a datetime, so use the isoformat of its date
                    temp = getattr(css, date_attr)
                    if temp is not None:
                        if isinstance(temp, datetime.datetime):
                            stats[date_attr] = getattr(css, date_attr).date().strftime("%d/%m/%Y")
                            continue
                        # otherwise, assume we have a datetime.date...
                        stats[date_attr] = getattr(css, date_attr).strftime("%d/%m/%Y")

                if len(stats):
                    if None in stats.values():
                        stats.update((k, v) for k, v in stats.iteritems() if v is not None)
                    data = simplejson.dumps([stats])
                else:
                    data = simplejson.dumps([])

                return HttpResponse(data, 'application/javascript')
            else:
                data = simplejson.dumps([])
                return HttpResponse(data, 'application/javascript')
        except Exception, e:
            print 'BANG STATS'
            print e
            data = simplejson.dumps([])
            return HttpResponse(data, 'application/javascript')

def register(req):
    if req.method == "POST":
        form = forms.RegisterForm(req.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/login')

    return render_to_response("register.html",\
        {"register_form": forms.RegisterForm()},\
        context_instance=RequestContext(req))

def get_upload_progress(request):
  from django.utils import simplejson
  cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], request.GET['X-Progress-ID'])
  data = cache.get(cache_key)
  return HttpResponse(simplejson.dumps(data))

@permission_required('vaxapp.can_upload')
def upload(req, up_id=None):
    if req.method == 'POST':
        form = forms.DocumentForm(req.POST, req.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = req.user
            doc.date_uploaded = datetime.datetime.utcnow()
            doc.local_document = req.FILES['local_document']
            doc.save()
            process_file.delay(doc)
            return HttpResponseRedirect('/upload/' + doc.uuid)
    else:
        if up_id:
            doc = get_object_or_404(Document, uuid=up_id)
            return render_to_response("upload_detail.html",\
                    {"doc":doc}, context_instance=RequestContext(req))
        form = forms.DocumentForm()
    return render_to_response("upload.html",\
            {"document_form": form,
            "tab": "upload"},\
            context_instance=RequestContext(req))

@permission_required('vaxapp.delete_document')
def uploads(req, user=None):
    return render_to_response("uploads.html",\
            {"docs": Document.objects.all().order_by('-date_uploaded')},\
            context_instance=RequestContext(req))

@permission_required('vaxapp.delete_document')
def revert_upload(req):
    if req.method == 'POST':
        up_id = req.POST['uuid']
        print up_id
        doc = get_object_or_404(Document, uuid=up_id)
        print doc
        process_revert_upload.delay(doc, req.user)
        return HttpResponseRedirect("/uploads/")

@permission_required('vaxapp.can_upload')
def entry(req):
    if req.method == 'POST':
        entry_forms = [forms.EntryForm(request.POST, prefix=str(x)) for x in range(0,10)]
        #if all((f.is_valid() for f in entry_forms)):
        for entry_form in entry_forms:
            if entry_form.is_valid():
                f = entry_form.save(commit=False)
                f.user = req.user
                f.date_entered = datetime.datetime.utcnow()
                f.save()
                #process_file.delay(doc)
                return HttpResponseRedirect('/')
    else:
        form = forms.EntryForm()
        entry_forms = [forms.EntryForm(prefix=str(x)) for x in range(0,10)]
    return render_to_response("entry.html",\
            {"entry_forms": entry_forms,\
            "tab": "entry"},\
            context_instance=RequestContext(req))
