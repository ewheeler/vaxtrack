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
    display_forecast_projection = True
    display_purchased_projection = True
    display_theoretical_forecast = True

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

        def project_future_stock_levels(delivery_type, begin_date, begin_level, end_date=None):
            deliveries = country_stock.delivery_set.all().order_by('date')
            future_deliveries = deliveries.filter(type=delivery_type)

            current_year = datetime.datetime.today().year
            # get this year's forecast
            current_forecast = forecasts.get(year=current_year)
            # estimate daily consumption based on estimated annual demand
            # TODO use appropriate year's estimate, not just current year!
            est_daily_consumption = int(float(current_forecast.demand_est)/float(365.0))

            # timedelta representing a change of one day
            one_day = datetime.timedelta(days=1)
            # TODO use end_date parameter if given
            last_day_in_current_year = datetime.date(current_year, 12, 31)
            # timedelta representing remaining days in this year
            # following the most recent stock level
            remaining_days_in_current_year = last_day_in_current_year - begin_date

            # variables to keep track of running totals while we loop
            est_stock_level = begin_level
            est_stock_date = begin_date
            projected_stock_dates = list()
            projected_stock_levels = list()

            for day in range(remaining_days_in_current_year.days):
                # increment date by one day
                this_date = est_stock_date + one_day
                est_stock_date = this_date
                # check for forecasted deliveries for this date
                deliveries_today = future_deliveries.filter(date=this_date)
                if deliveries_today.count() != 0:
                    for delivery in deliveries_today:
                        # add any delivery amounts to the estimated stock level
                        est_stock_level = est_stock_level + delivery.amount

                # add date to list of dates
                projected_stock_dates.append(this_date)
                # subtract estimated daily consumption from stock level
                est_stock_level = est_stock_level - est_daily_consumption
                if est_stock_level < 0:
                    # don't allow negative stock levels!
                    est_stock_level = 0
                # add level to list of levels
                projected_stock_levels.append(est_stock_level)
            return projected_stock_dates, projected_stock_levels


        fig = figure(figsize=(9,6))
        ax = fig.add_subplot(111)

        # plot stock levels
        ax.plot_date(dates, levels, '-', drawstyle='steps', color='blue')

        if display_buffers:
            # plot 3 and 9 month buffer levels as red lines
            ax.plot_date(dates, three_month_buffers, '-', drawstyle='steps', color='red')
            ax.plot_date(dates, nine_month_buffers, '-', drawstyle='steps', color='red')

        if display_forecast_projection:
            projected_ff_dates, projected_ff_levels = project_future_stock_levels("FF", stocklevels[0].date, stocklevels[0].amount)
            ax.plot_date(projected_ff_dates, projected_ff_levels, '--', drawstyle='steps', color='orange')

        if display_purchased_projection:
            projected_fp_dates, projected_fp_levels = project_future_stock_levels("FP", stocklevels[0].date, stocklevels[0].amount)
            ax.plot_date(projected_fp_dates, projected_fp_levels, '--', drawstyle='steps', color='blue')

        if display_theoretical_forecast:
            #TODO dynamic begin_date parameter
            projected_co_dates, projected_co_levels = project_future_stock_levels("CO", datetime.date(2007,8,31), 0)
            ax.plot_date(projected_co_dates, projected_co_levels, '--', drawstyle='steps', color='green')

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
