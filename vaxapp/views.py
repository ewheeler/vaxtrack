#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime
from itertools import chain
from itertools import combinations

# allow this to run on a headless server
# (otherwise pylab will use TkAgg backend)
import matplotlib
matplotlib.use('Agg')
import pylab

from pylab import figure, axes, pie, title
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import matplotlib.pyplot

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.db.models import Sum
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required

from .models import *
from . import forms
from vax import import_data
from vax.vsdb import *
from vax.vs3 import upload_file
from .tasks import process_file

def index(req, country_pk=None):
    if country_pk is not None:
        countrystocks = CountryStock.objects.filter(country=country_pk)
    else:
        countrystocks = False
    countries = [c.country for c in CountryStock.objects.all()]
    # TODO preserve order? 
    vaccines = list(set([v.vaccine for v in CountryStock.objects.all()]))
    return render_to_response("index.html",\
        {"countrystocks": countrystocks,\
            "countries": countries,\
            "vaccines": vaccines,\
            "tab": "dashboard"},\
            context_instance=RequestContext(req))

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

def get_chart(req, country_pk=None, vaccine_abbr=None, chart_opts=""):
    chart_url = "https://s3.amazonaws.com/vaxtrack_charts/%s-%s-%s.png" % (country_pk, vaccine_abbr, chart_opts)
    return HttpResponseRedirect(chart_url)

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def generate_all_charts_country_sdb(country_pk=None, vaccine_abbr=None, lang=None):
    ''' Calls all_charts_country_sdb with all permutations of `options`
        string where each character represents one option. '''
    # 5 options = 2^5 = 32 charts
    options = "BFPCU"
    for p in powerset(options):
        params = {}
        dicts = [params.update({c:True}) for c in p]
        print all_charts_country_sdb(country_pk=country_pk, vaccine_abbr=vaccine_abbr, lang=lang, **params)

def all_charts_country_sdb(country_pk=None, vaccine_abbr=None, lang=None, **kwargs):
    # string of options (as single characters) in alphabetical order
    # used later for filename
    options_str = ''.join(sorted(kwargs.keys()))

    # configuration options
    save_chart = True

    # default to false if options are not specified
    # TODO handle gracefully if all are false
    display_buffers = kwargs.get('B', False)
    display_forecast_projection = kwargs.get('F', False)
    display_purchased_projection = kwargs.get('P', False)
    display_theoretical_forecast = kwargs.get('C', False)
    display_adjusted_theoretical_forecast = kwargs.get('U', False)

    def values_list(dict_list, key):
        return [d[key] for d in dict_list]

    def filter(dict_list, attr, value):
        matches = []
        for dict in dict_list:
            if attr in dict:
                if dict[attr] == value:
                    matches.append(dict)
        return matches

    try:
        stocklevels = all_stocklevels_desc(country_pk, vaccine_abbr)

        years    = YearLocator()   # every year
        months   = MonthLocator()  # every month
        yearsFmt = DateFormatter('%Y')

        dates = values_list(stocklevels, 'date')
        levels = values_list(stocklevels, 'amount')

        forecasts = all_forecasts_asc(country_pk, vaccine_abbr)

        if display_buffers:
            three_by_year = dict()
            nine_by_year = dict()

            def three_month_buffer(demand_est):
                return int(float(demand_est) * (float(3.0)/float(12.0)))

            def nine_month_buffer(demand_est):
                return int(float(demand_est) * (float(9.0)/float(12.0)))

            # create dicts mapping year to buffer levels
            # (according to CO forecast annual demand estimate)
            three = [three_by_year.update({f['year']:three_month_buffer(f['amount'])})\
                for f in forecasts]
            nine = [nine_by_year.update({f['year']:nine_month_buffer(f['amount'])})\
                for f in forecasts]

            # make a list of corresponding buffer levels for every reported stock level
            # TODO can this be done without plotting for each stock level?
            three_month_buffers = [three_by_year[d.year] for d in dates]
            nine_month_buffers = [nine_by_year[d.year] for d in dates]

    except Exception,e:
        print 'ERROR DATA'
        print e
        import ipdb; ipdb.set_trace()

    def _project_future_stock_levels(delivery_type, begin_date, begin_level, end_date=None):
        try:
            filtered_deliveries = all_deliveries_for_type_asc(country_pk, vaccine_abbr, delivery_type)

            def _est_daily_consumption_for_year(year):
                ''' Return daily consumption based on estimated annual demand '''
                forecast = forecast_for_year(country_pk, vaccine_abbr, year)[0]
                return int(float(forecast['amount'])/float(365.0))

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
                deliveries_today = filter(filtered_deliveries, 'date', this_date)
                if len(deliveries_today) != 0:
                    for delivery in deliveries_today:
                        # add any delivery amounts to the estimated stock level
                        est_stock_level = est_stock_level + delivery['amount']

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
            import ipdb; ipdb.set_trace()


    try:
        # documentation sez figsize is in inches (!?)
        fig = figure(figsize=(15,12))

        # add country name and vaccine as chart title
        title = "%s %s" % (country_pk, vaccine_abbr)
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
                "FF", stocklevels[0]['date'], stocklevels[0]['amount'])
            ax.plot_date(projected_ff_dates, projected_ff_levels, '--',\
                drawstyle='steps', color='purple',\
                label='projected stock based on forecast')

        if display_purchased_projection:
            projected_fp_dates, projected_fp_levels = _project_future_stock_levels(\
                "FP", stocklevels[0]['date'], stocklevels[0]['amount'])
            ax.plot_date(projected_fp_dates, projected_fp_levels, '--',\
            drawstyle='steps', color='blue',\
            label='projected stock based on placed POs')

        if display_theoretical_forecast:
            # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
            projected_co_dates, projected_co_levels = _project_future_stock_levels(\
                "CO", stocklevels[-2]['date'], stocklevels[-2]['amount'])
            ax.plot_date(projected_co_dates, projected_co_levels, '--',\
            drawstyle='steps', color='green',\
            label='theoretical stock based on forecast')

        if display_adjusted_theoretical_forecast:
            # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
            projected_un_dates, projected_un_levels = _project_future_stock_levels(\
                "UN", stocklevels[-2]['date'], stocklevels[-2]['amount'])
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
        import ipdb; ipdb.set_trace()

    if save_chart:
        try:
            filename = "%s-%s-%s.png" % (country_pk, vaccine_abbr, options_str)
            file_path = "/tmp/" + filename
            fig.savefig(file_path)
        except Exception, e:
            print 'ERROR SAVING'
            print e
            import ipdb; ipdb.set_trace()
        try:
            s3_key = "%s-%s-%s.png" % (country_pk, vaccine_abbr, options_str)
            s3_path = "%s/%s/%s/" % (lang, country_pk, vaccine_abbr)
            upload_file(file_path, 'vaxtrack_charts', s3_path + s3_key, True)
            return file_path
        except Exception, e:
            print 'ERROR UPLOADING'
            print e
            import ipdb; ipdb.set_trace()

    return 'wat'
