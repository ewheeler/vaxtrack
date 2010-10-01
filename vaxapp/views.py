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
from django.template import RequestContext

from .models import *
from . import forms
from vax import import_data

def index(req):
    return render_to_response("index.html",\
        {"countrystocks": CountryStock.objects.all(),\
            "country_form": forms.CountryForm()},\
            context_instance=RequestContext(req))

def chart_country(req, country_pk=None, vaccine_abbr=None):
    # configuration options
    print_to_web = True 
    save_chart = False 
    display_buffers = True
    display_forecast_projection = False
    display_purchased_projection = False
    display_theoretical_forecast = False
    display_adjusted_theoretical_forecast = False

    try:
        country_stock = CountryStock.objects.get(country__pk=country_pk,\
            vaccine__abbr=vaccine_abbr)

        # oldest last
        stocklevels = StockLevel.objects.filter(country_stock=country_stock)\
            .order_by('-date')

        years    = YearLocator()   # every year
        months   = MonthLocator()  # every month
        yearsFmt = DateFormatter('%Y')

        dates = stocklevels.values_list('date', flat=True)
        levels = stocklevels.values_list('amount', flat=True)

        forecasts = country_stock.forecast_set.all().order_by('year')

        if display_buffers:
            three_by_year = dict()
            nine_by_year = dict()

            # create dicts mapping year to buffer levels
            # (according to CO forecast annual demand estimate)
            three = [three_by_year.update({f.year:f.three_month_buffer})\
                for f in forecasts]
            nine = [nine_by_year.update({f.year:f.nine_month_buffer})\
                for f in forecasts]

            # make a list of corresponding buffer levels for every reported stock level
            # TODO can this be done without plotting for each stock level?
            three_month_buffers = [three_by_year[d.year] for d in dates]
            nine_month_buffers = [nine_by_year[d.year] for d in dates]

    except Exception,e:
        print 'ERROR DATA'
        print e

    def _project_future_stock_levels(delivery_type, begin_date, begin_level, end_date=None):
        try:
            all_deliveries = country_stock.delivery_set.all().order_by('date')
            filtered_deliveries = all_deliveries.filter(type=delivery_type)

            def _est_daily_consumption_for_year(year):
                ''' Return daily consumption based on estimated annual demand '''
                forecast = forecasts.get(year=year)
                return int(float(forecast.demand_est)/float(365.0))

            # timedelta representing a change of one day
            one_day = datetime.timedelta(days=1)
            if end_date is None:
                last_day_in_current_year = datetime.date(datetime.datetime.today().year, 12, 31)
                end_date = last_day_in_current_year
            # timedelta representing days we are plotting
            days_to_plot = end_date - begin_date

            # variables to keep track of running totals while we loop
            est_stock_level = begin_level
            est_stock_date = begin_date
            projected_stock_dates = list()
            projected_stock_levels = list()

            for day in range(days_to_plot.days):
                # increment date by one day
                this_date = est_stock_date + one_day
                est_stock_date = this_date
                # check for forecasted deliveries for this date
                deliveries_today = filtered_deliveries.filter(date=this_date)
                if deliveries_today.count() != 0:
                    for delivery in deliveries_today:
                        # add any delivery amounts to the estimated stock level
                        est_stock_level = est_stock_level + delivery.amount

                # add date to list of dates
                projected_stock_dates.append(this_date)
                # subtract estimated daily consumption from stock level
                est_stock_level = est_stock_level - _est_daily_consumption_for_year(est_stock_date.year)
                if est_stock_level < 0:
                    # don't allow negative stock levels!
                    est_stock_level = 0
                # add level to list of levels
                projected_stock_levels.append(est_stock_level)
            return projected_stock_dates, projected_stock_levels
        except Exception,e:
            print 'ERROR PROJECTION'
            print e


    try:
        # documentation sez figsize is in inches (!?)
        fig = figure(figsize=(15,12))

        # add country name and vaccine as chart title
        title = "%s %s" % (country_stock.country.printable_name,\
            country_stock.vaccine.abbr)
        fig.suptitle(title, fontsize=18)

        # add timestamp to lower left corner
        colophon = "Generated by VaxTrack on %s (GMT -5)" %\
            (str(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")))
        fig.text(0,0,colophon, fontsize=8)
        ax = fig.add_subplot(111)

        # plot stock levels
        ax.plot_date(dates, levels, '-', drawstyle='steps', color='blue',\
            label='actual stock')

        if display_buffers:
            # plot 3 and 9 month buffer levels as red lines
            ax.plot_date(dates, three_month_buffers, '-', drawstyle='steps',\
                color='red', label='3 month buffer')
            ax.plot_date(dates, nine_month_buffers, '-', drawstyle='steps',\
                color='red', label='9 month buffer')

        if display_forecast_projection:
            projected_ff_dates, projected_ff_levels = _project_future_stock_levels(\
                "FF", stocklevels[0].date, stocklevels[0].amount)
            ax.plot_date(projected_ff_dates, projected_ff_levels, '--',\
                drawstyle='steps', color='purple',\
                label='projected stock based on forecast')

        if display_purchased_projection:
            projected_fp_dates, projected_fp_levels = _project_future_stock_levels(\
                "FP", stocklevels[0].date, stocklevels[0].amount)
            ax.plot_date(projected_fp_dates, projected_fp_levels, '--',\
            drawstyle='steps', color='blue',\
            label='projected stock based on placed POs')

        # reverse order of stocklevels so first element is the oldest one
        rstocklevels = stocklevels.reverse()
        if display_theoretical_forecast:
            # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
            projected_co_dates, projected_co_levels = _project_future_stock_levels(\
                "CO", rstocklevels[1].date, rstocklevels[1].amount)
            ax.plot_date(projected_co_dates, projected_co_levels, '--',\
            drawstyle='steps', color='green',\
            label='theoretical stock based on forecast')

        if display_adjusted_theoretical_forecast:
            # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
            projected_un_dates, projected_un_levels = _project_future_stock_levels(\
                "UN", rstocklevels[1].date, rstocklevels[1].amount)
            ax.plot_date(projected_un_dates, projected_un_levels, '--',\
            drawstyle='steps', color='orange',\
            label='theoretical stock adjusted with deliveries')

        # format the ticks
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        ax.xaxis.set_minor_locator(months)
        ax.autoscale_view()

        ax.grid(True)
        ax.legend(prop={'size': 'x-small'})

        fig.autofmt_xdate()

        # close figure so next call doesn't add to previous call's image
        # and so memory gets gc'ed
        matplotlib.pyplot.close(fig)

    except Exception, e:
        print 'ERROR FIGURE'
        print e

    if save_chart:
        filename = "%s-%s-%s.png" % (datetime.datetime.today().date().isoformat(),\
            country_pk, vaccine_abbr)
        file_path = "vaxapp/static/charts/" + filename
        fig.savefig(file_path)
        return file_path

    if print_to_web:
        # respond with figure for web display
        canvas = FigureCanvasAgg(fig)
        response = HttpResponse(content_type='image/png')
        canvas.print_png(response)

        return response

def handle_uploaded_file(f, filename='/tmp/wat.csv'):
    destination = open(filename, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()

def upload_country(req):
    if req.method == "POST":
        form = forms.CountryForm(req.POST)

        if form.is_valid():
            cleaned = form.cleaned_data

            uploader = cleaned["uploader"]
            filename = "/tmp/" + uploader + ".csv"

            if "country_csv" in req.FILES:
                try:
                    handle_uploaded_file(req.FILES["country_csv"], filename)
                except Exception, e:
                    print e
                try:
                    import_data.import_csv(filename)
                except Exception, e:
                    print e
    return HttpResponseRedirect('/')
