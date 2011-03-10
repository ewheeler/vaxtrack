#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

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
    mali = Country.objects.get(iso2_code='ML')
    chad = Country.objects.get(iso2_code='TD')
    countries = [mali, chad]
    vaccines = Vaccine.objects.filter(abbr_en='BCG')
    return render_to_response("index.html",\
        {"countrystocks": countrystocks,\
            "countries": countries,\
            "vaccines": vaccines,\
            "tab": "dashboard"},\
            context_instance=RequestContext(req))

def alerts(req, country_pk, vaccine_abbr):
    if req.is_ajax():
        countrystock = CountryStock.objects.filter(country=country_pk, vaccine__abbr_fr_alt=vaccine_abbr)
        print countrystock
        alerts = Alert.objects.filter(countrystock=countrystock)
        print alerts
        if len(alerts) == 0:
            return HttpResponse([], 'application/javascript')
        alerts_text = {}
        for alert in alerts:
            print alert.get_text_display()
            alerts_text.update({'text':alert.get_text_display(), 'status':alert.status})
        print alerts_text
        #data = serializers.serialize('json', alerts)
        return HttpResponse(simplejson.dumps([alerts_text]), 'application/javascript')

def stats(req, country_pk, vaccine_abbr):
    if req.is_ajax():
        countrystock = CountryStock.objects.filter(country=country_pk, vaccine__abbr_fr_alt=vaccine_abbr)
        if countrystock.count() > 0:
            css = countrystock[0].latest_stats
            if css is None:
                return HttpResponse([], 'application/javascript')
            stats = {}
            # TODO this is insane
            # instead of the fields, i'd like the properties that return
            # a dict of the related obj rather than pks of related obj
            props_to_get = ['consumed_in_year', 'actual_cons_rate', 'annual_demand', 'three_by_year', 'nine_by_year']
            years = []
            for prop in props_to_get:
                #stats[prop] = getattr(css, 'get_' + prop)
                prop_dict = getattr(css, 'get_' + prop)
                prop_list = []
                if prop_dict is not None:
                    for year in sorted(prop_dict.iterkeys()):
                        years.append(str(year))
                        prop_list.append(prop_dict[year])
                    stats[prop] = prop_list
            stats['years'] = sorted(list(set(years)))

            attrs_to_get = ['est_daily_cons','days_of_stock','doses_delivered_this_year','doses_on_orders','demand_for_period']
            for attr in attrs_to_get:
                stats[attr] = getattr(css, attr)

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

            #data = serializers.serialize('json', stats)
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
            {"country_form": form,
            "tab": "upload"},\
            context_instance=RequestContext(req))

def get_chart_dev(req, country_pk=None, vaccine_abbr=None, chart_opts=""):
    vaccine_abbr = vaccine_abbr.replace("_", "-")
    path = "%s/%s/%s/" % ('en', country_pk, vaccine_abbr)
    filename = "en-%s-%s-%s.png" % (country_pk, vaccine_abbr, chart_opts)
    chart_url = "https://s3.amazonaws.com/vaxtrack_charts/%s%s" % (path, filename)
    print chart_url
    return HttpResponseRedirect(chart_url)

def get_chart(req, country_pk=None, vaccine_abbr=None, chart_opts=""):
    vaccine_abbr = 'BCG'
    filename = "%s-%s-%s.png" % (country_pk, vaccine_abbr, chart_opts)
    chart_url = "https://s3.amazonaws.com/vaxtrack_charts/%s" % (filename)
    print chart_url
    return HttpResponseRedirect(chart_url)

