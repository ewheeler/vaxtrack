#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime

from pylab import figure, axes, pie, title
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import matplotlib.pyplot

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.db.models import Sum

from models import *

def index(req):
    return render_to_response("index.html",\
        {"countrystocks": CountryStock.objects.all()})

def chart_country(req, country_pk=None, vaccine_abbr=None):
    country_stock = CountryStock.objects.get(country__pk=country_pk,\
        vaccine__abbr=vaccine_abbr)

    stocklevels = StockLevel.objects.filter(country_stock=country_stock).order_by('-date')

    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')

    dates = stocklevels.values_list('date', flat=True)
    levels = stocklevels.values_list('amount', flat=True)

    fig = figure()
    ax = fig.add_subplot(111)
    ax.plot_date(dates, levels, '-')

    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.autoscale_view()

    ax.grid(True)

    fig.autofmt_xdate()

    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    matplotlib.pyplot.close(fig)

    save_charts = False
    if save_charts:
        filename = "%s-%s.png" % (datetime.datetime.today().date().isoformat(), country_pk)
        file_path = "vaxapp/static/charts/" + filename
        fig.savefig(file_path)

    return response
