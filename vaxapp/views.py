#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import itertools

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from django.core import serializers
from django.utils import simplejson

from .models import *
from .analysis import *
from . import forms

def index_dev(req, country_pk=None):
    if country_pk is not None:
        countrystocks = CountryStock.objects.filter(country=country_pk)
    else:
        countrystocks = False
    countries = list(set([c.country for c in CountryStock.objects.all().exclude(country__iso2_code='TD').exclude(country__iso2_code='ML')]))
    # TODO preserve order? 
    vaccines = list(set([v.vaccine for v in CountryStock.objects.all().exclude(vaccine__abbr_en='BCG')]))
    return render_to_response("dev.html",\
        {"countrystocks": countrystocks,\
            "countries": countries,\
            "vaccines": vaccines,\
            "tab": "dashboard"},\
            context_instance=RequestContext(req))

def index(req, country_pk=None):
    if country_pk is not None:
        countrystocks = CountryStock.objects.filter(country=country_pk)
    else:
        countrystocks = False
    countrystocks = CountryStock.objects.filter(country="ML")
    countries = list(set([c.country for c in countrystocks ]))
    groups = list(set([g.group for g in countrystocks]))
    return render_to_response("index.html",\
        {"countrystocks": countrystocks,\
            "countries": countries,\
            "groups": groups,\
            "tab": "dashboard"},\
            context_instance=RequestContext(req))

def alerts(req, country_pk, vaccine_abbr):
    if req.is_ajax():
        countrystock = CountryStock.objects.filter(country=country_pk, group=group_slug)
        alerts = Alert.objects.filter(countrystock=countrystock)
        if len(alerts) == 0:
            return HttpResponse([], 'application/javascript')
        #alerts_text = []
        #any(itertools.imap(lambda alert: alerts_text.append({'text':alert.get_text_display(), 'status':alert.status}), alerts))
        alerts_text = [{'text':alert.get_text_display(), 'status':alert.status} for alert in alerts]
        return HttpResponse(simplejson.dumps(alerts_text), 'application/javascript')

def stats(req, country_pk, vaccine_abbr):
    if req.is_ajax():
        countrystock = CountryStock.objects.filter(country=country_pk, vaccine__abbr_fr_alt=vaccine_abbr)
        if countrystock.count() > 0:
            css = countrystock[0].latest_stats
            if css is None:
                return HttpResponse([], 'application/javascript')
            # TODO this is insane
            # instead of the fields, i'd like the properties that return
            # a dict of the related obj rather than pks of related obj
            props_to_get = ['consumed_in_year', 'actual_cons_rate', 'annual_demand', 'three_by_year', 'nine_by_year', 'days_of_stock_data']
            years = []

            #t1 = os.times()
            stats = {}
            for prop in props_to_get:
                prop_dict = getattr(css, 'get_' + prop)
                prop_list = []
                if prop_dict is not None:
                    for year in sorted(prop_dict.iterkeys()):
                        years.append(str(year))
                        prop_list.append(prop_dict[year])
                    stats[prop] = prop_list
            stats['years'] = sorted(list(set(years)))
            #t2 = os.times()
            ## print result
            #utime = t2[0] - t1[0] # user time
            #stime = t2[1] - t1[1] # system time
            #print "utime=%s, stime=%s" % (utime, stime)
            #print stats

            # in this case, the for loop is comparable in speed
            # and much much more legible. caveat: os.times() is not best measure
            # could be faster if theres a way to get rid of the list comps
            #
            #test = {}
            #t1 =  os.times()
            #props = dict(((prop, getattr(css, 'get_' + prop)) for prop in props_to_get))
            #test.update({'years': sorted(props['annual_demand'].keys())})
            #any(itertools.imap(lambda prop: test.update({prop: [props[prop][y] for y in test['years']]}), props_to_get))
            #t2 = os.times()
            ## print result
            #utime = t2[0] - t1[0] # user time
            #stime = t2[1] - t1[1] # system time
            #print "utime=%s, stime=%s" % (utime, stime)
            #print test

            attrs_to_get = ['est_daily_cons','days_of_stock','doses_delivered_this_year','doses_on_orders','demand_for_period']
            # instead of a for loop, using this strategy: http://news.ycombinator.com/item?id=2320298
            # basically, this avoids having the for loop translated into
            # bytecode by the interpreter and runs in straight c instead
            any(itertools.imap(lambda attr: stats.update({attr: getattr(css, attr)}), attrs_to_get))

            stats['percent_coverage'] = str(int(css.percent_coverage*100.0)) + '%'

            # need isoformat because dates/datetimes aren't serializable
            date_attrs = ['analyzed', 'reference_date']
            for date_attr in date_attrs:
                # analyzed is a datetime, so use the isoformat of its date
                temp = getattr(css, date_attr)
                if isinstance(temp, datetime.datetime):
                    stats[date_attr] = getattr(css, date_attr).date().isoformat()
                    continue
                # otherwise, assume we have a datetime.date...
                stats[date_attr] = getattr(css, date_attr).isoformat()

            data = simplejson.dumps([stats])
            return HttpResponse(data, 'application/javascript')
        else:
            data = simplejson.dumps([{}])
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

@permission_required('vaxapp.can_upload')
def upload(req):
    if req.method == 'POST':
        form = forms.DocumentForm(req.POST, req.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = req.user
            doc.date_uploaded = datetime.datetime.utcnow()
            doc.save()
            process_file.delay(doc)
            return HttpResponseRedirect('/')
    else:
        form = forms.DocumentForm()
    return render_to_response("upload.html",\
            {"document_form": form,
            "tab": "upload"},\
            context_instance=RequestContext(req))

def get_chart(req, country_pk=None, group_slug=None, chart_opts=""):
    group_slug = group_slug.replace("_", "-").lower()
    path = "%s/%s/%s/" % ('en', country_pk, group_slug)
    filename = "en-%s-%s-%s.png" % (country_pk, group_slug, chart_opts)
    chart_url = "https://s3.amazonaws.com/vaxtrack_charts/%s%s" % (path, filename)
    return HttpResponseRedirect(chart_url)

'''
def get_chart(req, country_pk=None, group_slug=None, chart_opts=""):
    filename = "%s-%s-%s.png" % (country_pk, group_slug, chart_opts)
    chart_url = "https://s3.amazonaws.com/vaxtrack_charts/%s" % (filename)
    return HttpResponseRedirect(chart_url)
'''
