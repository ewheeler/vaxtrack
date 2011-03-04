#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from django.core import serializers

from .models import *
from .charts import *
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
        alerts = Alert.objects.filter(countrystock=countrystock)
        data = serializers.serialize('json', alerts)
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

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

