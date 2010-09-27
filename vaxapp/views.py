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
    # configuration options
    save_charts = False
    display_buffers = True

    country_stock = CountryStock.objects.get(country__pk=country_pk,\
        vaccine__abbr=vaccine_abbr)

    stocklevels = StockLevel.objects.filter(country_stock=country_stock).order_by('-date')

    years    = YearLocator()   # every year
    months   = MonthLocator()  # every month
    yearsFmt = DateFormatter('%Y')

    dates = stocklevels.values_list('date', flat=True)
    levels = stocklevels.values_list('amount', flat=True)

    try:
        forecasts = country_stock.forecast_set.all().order_by('year')

        if display_buffers:
            three_by_year = dict()
            nine_by_year = dict()

            # create dicts mapping year to buffer levels
            # (according to CO forecast annual demand estimate)
            three = [three_by_year.update({f.year:f.three_month_buffer}) for f in forecasts ]
            nine = [nine_by_year.update({f.year:f.nine_month_buffer}) for f in forecasts ]

            # make a list of corresponding buffer levels for every reported stock level
            # TODO can this be done without plotting for each stock level?
            three_month_buffers = [three_by_year[d.year] for d in dates]
            nine_month_buffers = [nine_by_year[d.year] for d in dates]

        deliveries = country_stock.delivery_set.all().order_by('date')
        future_forecast = deliveries.filter(type='FF')
        future_forecast_dates = future_forecast.values_list('date', flat=True)
        future_forecast_amounts = future_forecast.values_list('amount', flat=True)

    except Exception, e:
        print 'ERROR DATA'
        print e

    try:
        fig = figure(figsize=(9,6))
        ax = fig.add_subplot(111)

        # plot stock levels
        ax.plot_date(dates, levels, '-', drawstyle='steps')

        if display_buffers:
            # plot 3 and 9 month buffer levels as red lines
            ax.plot_date(dates, three_month_buffers, '-', drawstyle='steps', color='red')
            ax.plot_date(dates, nine_month_buffers, '-', drawstyle='steps', color='red')

        ax.plot_date(future_forecast_dates, future_forecast_amounts, '-', drawstyle='steps', color='green')

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

    except Exception, e:
        print 'ERROR FIGURE'
        print e

    if save_charts:
        filename = "%s-%s-%s.png" % (datetime.datetime.today().date().isoformat(),\
            country_pk, vaccine_abbr)
        file_path = "vaxapp/static/charts/" + filename
        fig.savefig(file_path)

    return response
