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
from django.core import serializers

from .models import *
from . import forms
from vax import import_data
from vax.vsdb import *
from vax.vs3 import upload_file
from .tasks import process_file

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

def update_dev():
    for iso in ['SN', 'NE']:
        generate_six_charts_country_sdb(iso, 'en')

def generate_all_charts_country_sdb(country_pk=None, vaccine_abbr=None, lang=None, options="BFPCU"):
    ''' Calls all_charts_country_sdb with all permutations of `options`
        string where each character represents one option. '''
    # 5 options = 2^5 = 32 charts
    for p in powerset(options):
        params = {}
        dicts = [params.update({c:True}) for c in p]
        print all_charts_country_sdb(country_pk=country_pk, vaccine_abbr=vaccine_abbr, lang=lang, **params)

def generate_six_charts_country_sdb(country_pk=None, lang=None):
    #for v in ['opv-50', 'measles', 'tt-10', 'dtp-hepbhib-1', 'yf-1', 'bcg-10']:
    for v in ['tt-10', 'dtp-hepbhib-1']:
        print generate_all_charts_country_sdb(country_pk=country_pk, vaccine_abbr=v, lang=lang)

def generate_demo_charts():
    for country in ['ML', 'TD']:
        for vax in ['BCG']:
            print generate_all_charts_country_sdb(country_pk=country, vaccine_abbr=vax, lang='en')

def all_charts_country_sdb(country_pk=None, vaccine_abbr=None, lang=None, **kwargs):
    # string of options (as single characters) in alphabetical order
    # used later for filename
    options_str = ''.join(sorted(kwargs.keys()))

    # configuration options
    save_chart = False
    analyze = True

    # default to false if options are not specified
    display_buffers = kwargs.get('B', False)
    display_forecast_projection = kwargs.get('F', False)
    display_purchased_projection = kwargs.get('P', False)
    display_theoretical_forecast = kwargs.get('C', False)
    display_adjusted_theoretical_forecast = kwargs.get('U', False)

    def values_list(dict_list, key):
        # kindof like django querysets's flat values list
        return [d[key] for d in dict_list]

    def filter(dict_list, attr, value):
        # kindof like django queryset's filter
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

        annual_demand = {}
        # get list of years we are dealing with
        f_years = list(set(values_list(forecasts, 'year')))
        for year in f_years:
            annual = []
            # get list of forecasts for each year
            fy = filter(forecasts, 'year', year)
            for f in fy:
                # add forecasts for this year to list
                annual.append(f['amount'])
            annual_demand.update({year:sum(annual)})

        if display_buffers:
            three_by_year = dict()
            nine_by_year = dict()

            def three_month_buffer(demand_est):
                return int(float(demand_est) * (float(3.0)/float(12.0)))

            def nine_month_buffer(demand_est):
                return int(float(demand_est) * (float(9.0)/float(12.0)))

            for year in f_years:
                # create a single key/value pair for each year/sum forecast
                three_by_year.update({year:three_month_buffer(annual_demand[year])})
                nine_by_year.update({year:nine_month_buffer(annual_demand[year])})

            # make a list of corresponding buffer levels for every reported stock level
            first_and_last_days = []
            for y in sorted(three_by_year.keys()):
                first_and_last_days.append(datetime.date(y, 1, 1))
                first_and_last_days.append(datetime.date(y, 12, 31))

            three_month_buffers = [three_by_year[d.year] for d in first_and_last_days]
            nine_month_buffers = [nine_by_year[d.year] for d in first_and_last_days]


    except Exception,e:
        print 'ERROR DATA'
        print e
        import ipdb; ipdb.set_trace()

    def _calc_stock_levels(delivery_type, begin_date, begin_level, end_date=None):
        try:
            filtered_deliveries = all_deliveries_for_type_asc(country_pk, vaccine_abbr, delivery_type)

            def _est_daily_consumption_for_year(year):
                ''' Return daily consumption based on estimated annual demand '''
                forecast = annual_demand[year]
                return int(float(forecast)/float(365.0))

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
            ax.plot_date(first_and_last_days, three_month_buffers, '-', drawstyle='steps',\
                color='red', label='3 month buffer')
            ax.plot_date(first_and_last_days, nine_month_buffers, '-', drawstyle='steps',\
                color='red', label='9 month buffer')

        if display_forecast_projection:
            projected_ff_dates, projected_ff_levels = _calc_stock_levels(\
                "FF", stocklevels[0]['date'], stocklevels[0]['amount'])
            ax.plot_date(projected_ff_dates, projected_ff_levels, '--',\
                drawstyle='steps', color='purple',\
                label='projected stock based on forecast')

        if display_purchased_projection:
            projected_fp_dates, projected_fp_levels = _calc_stock_levels(\
                "FP", stocklevels[0]['date'], stocklevels[0]['amount'])
            ax.plot_date(projected_fp_dates, projected_fp_levels, '--',\
            drawstyle='steps', color='blue',\
            label='projected stock based on placed POs')

        if display_theoretical_forecast:
            # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
            projected_co_dates, projected_co_levels = _calc_stock_levels(\
                "CO", stocklevels[-2]['date'], stocklevels[-2]['amount'])
            ax.plot_date(projected_co_dates, projected_co_levels, '--',\
            drawstyle='steps', color='green',\
            label='theoretical stock based on forecast')

        if display_adjusted_theoretical_forecast:
            # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
            projected_un_dates, projected_un_levels = _calc_stock_levels(\
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
            # TODO make these configurable? same with sdb domain?
            #s3_key = "%s-%s-%s-%s.png" % (lang, country_pk, vaccine_abbr, options_str)
            #s3_path = "%s/%s/%s/" % (lang, country_pk, vaccine_abbr)
            #upload_file(file_path, 'vaxtrack_charts', s3_path + s3_key, True)
            demo_key = "%s-%s-%s.png" % (country_pk, vaccine_abbr, options_str)
            upload_file(file_path, 'vaxtrack_charts', demo_key, True)
            return file_path
        except Exception, e:
            print 'ERROR UPLOADING'
            print e
            import ipdb; ipdb.set_trace()

    if analyze:
        last_s = {}
        consumed_in_year = {}

        for y in f_years:
            consumed_in_year.update({y:0})
            last_s.update({y:0})

        for d in all_stocklevels_asc(country_pk, vaccine_abbr):
            yr = int(d['year'])
            s = int(d['amount'])
            if not yr in f_years:
                continue
            if s <= last_s[yr]:
                consumed_today = last_s[yr] - s
                consumed_this_year = consumed_in_year[yr] + consumed_today
                consumed_in_year.update({yr:consumed_this_year})

            last_s[yr] = s

        actual_cons_rate = {}
        for y in f_years:
            rate = float(consumed_in_year[y])/float(365)
            actual_cons_rate.update({y:int(rate)})
        print actual_cons_rate
    import ipdb;ipdb.set_trace()
    return 'wat'
