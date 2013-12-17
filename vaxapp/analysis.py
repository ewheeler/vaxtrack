#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os
import errno
import csv
import datetime
import calendar
import locale
from itertools import chain
from itertools import combinations
import operator

from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from vax.vsdb import *
from vax.vs3 import upload_file
from .tasks import process_file
from .tasks import handle_alert
from .models import *

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def plot_one(sit_year=2011, sit_month=4, sit_day=1):
    begin = datetime.datetime.now()
    for country in ['ML']:
        for v in ['opv']:
            analysis = Analysis(country_pk=country, group_slug=str(v), vaccine_abbr=None, sit_year=sit_year, sit_month=sit_month, sit_day=sit_day)
            print analysis.plot()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

def plot_and_analyze(sit_year=2011, sit_month=12, sit_day=15, country_pks=None, group_slugs=None):
    assert country_pks is not None
    assert group_slugs is not None
    begin = datetime.datetime.now()
    for country in country_pks:
        for slug in group_slugs:
            analysis = Analysis(country_pk=country, group_slug=slug, vaccine_abbr=None, sit_year=sit_year, sit_month=sit_month, sit_day=sit_day)
            print analysis.save_stats()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

def plot(sit_year=2011, sit_month=12, sit_day=15, country='SN', group_slug='bcg'):
    begin = datetime.datetime.now()
    analysis = Analysis(country_pk=country, group_slug=group_slug, vaccine_abbr=None, sit_year=sit_year, sit_month=sit_month, sit_day=sit_day)
    print analysis.save_stats()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

def plot_all(sit_year=2011, sit_month=9, sit_day=15):
    begin = datetime.datetime.now()
    #for country in Country.objects.all().values_list('iso2_code', flat=True):
    for country in ['ML', 'SN', 'TD']:
        #for v in [cs.group.slug for cs in CountryStock.objects.filter(country__iso2_code=country)]:
        for v in ['bcg', 'dtp-hepbhib', 'mea', 'opv', 'tt', 'yf']:
            analysis = Analysis(country_pk=country, group_slug=str(v), vaccine_abbr=None, sit_year=sit_year, sit_month=sit_month, sit_day=sit_day)
            print analysis.plot()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

def plot_all_historical():
    begin = datetime.datetime.now()
    for country in ['ML', 'TD', 'SN']:
        for v in ['bcg', 'dtp-hepbhib', 'mea', 'opv', 'tt', 'yf']:
            for y in [2007,2008,2009,2010,2011]:
                for m in range(13)[1:]:
                    for d in [1,15]:
                        analysis = Analysis(country_pk=country, group_slug=str(v), vaccine_abbr=None, sit_year=y, sit_month=m, sit_day=d)
                        print analysis.plot()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

def plot_historical(country_pks, group_slugs, years):
    begin = datetime.datetime.now()
    for country in country_pks:
        for v in group_slugs:
            for y in years:
                for m in range(13)[1:]:
                    for d in [1,15]:
                        analysis = Analysis(country_pk=country, group_slug=str(v), vaccine_abbr=None, sit_year=y, sit_month=m, sit_day=d)
                        print analysis.plot()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

def analyze_all(sit_year=2011, sit_month=7, sit_day=1):
    begin = datetime.datetime.now()
    for country in ['ML', 'TD', 'SN']:
        #for v in [cs.group.slug for cs in CountryStock.objects.filter(country__iso2_code=country)]:
        for v in ['bcg', 'dtp-hepbhib', 'mea', 'opv', 'tt', 'yf']:
            analysis = Analysis(country_pk=country, group_slug=str(v), vaccine_abbr=None, sit_year=sit_year, sit_month=sit_month, sit_day=sit_day)
            print analysis.save_stats()
    end = datetime.datetime.now()
    delta = end - begin
    print begin
    print end
    print delta

class Analysis(object):
    # helper methods
    @staticmethod
    def values_list(dict_list, key):
        # kindof like django querysets's flat values list
        return [d[key] for d in dict_list]

    @staticmethod
    def filter(dict_list, attr, value):
        # kindof like django queryset's filter
        matches = []
        for dict in dict_list:
            if attr in dict:
                if dict[attr] == value:
                    matches.append(dict)
        return matches

    def get_and_set_vars(self):
        try:
            # fetch all stocklevels up to 'today'
            self.stocklevels = [s for s in get_group_all_stocklevels_asc(self.country_pk, self.group_slug) if s['date'] < self.today]

            self.dates = Analysis.values_list(self.stocklevels, 'date')
            self.levels = Analysis.values_list(self.stocklevels, 'amount')

            self.forecasts = get_group_all_forecasts_asc(self.country_pk, self.group_slug)
            self.fforecasts = get_group_all_fforecasts_asc(self.country_pk, self.group_slug)

            self.annual_demand = {}
            # get list of years we are dealing with
            self.f_years = list(set(Analysis.values_list(self.forecasts, 'year')))
            print self.f_years
            self.ff_years = list(set(Analysis.values_list(self.fforecasts, 'year')))
            print self.ff_years
            self.s_years = list(set(Analysis.values_list(self.stocklevels, 'year')))
            print self.s_years
            for year in self.f_years:
                annual = []
                # get list of forecasts for each year
                fy = Analysis.filter(self.forecasts, 'year', year)
                for f in fy:
                    # add forecasts for this year to list
                    annual.append(f['amount'])
                self.annual_demand.update({year:sum(annual)})
            print self.annual_demand
            return True

        except Exception,e:
            print 'ERROR GET AND SET VARS'
            print e
            if self.interactive:
                import ipdb; ipdb.set_trace()
            return False

    def __init__(self, country_pk=None, group_slug=None, vaccine_abbr=None, lang=None, sit_year=None, sit_month=None, sit_day=None):
        self.country_pk = country_pk
        self.vaccine_abbr = vaccine_abbr
        self.group_slug = group_slug
        self.lang = lang
        self.langs = ['en', 'fr']
        #if self.lang is not None:
        #    translation.activate(self.lang)

        if vaccine_abbr is not None:
            v = Vaccine.lookup_slug(self.vaccine_abbr)
            if v is None:
                print 'couldnt find vaccine'
        #print "GROUP"
        print self.country_pk
        print self.group_slug

        country = Country.objects.get(iso2_code=self.country_pk)
        group = VaccineGroup.objects.get(slug=self.group_slug)
        self.cs, new_cs = CountryStock.objects.get_or_create(country=country, group=group)

        # loosely keep track of what we've done,
        # so we don't call save_stats before plotting
        self.analyzed = False
        self.plotted = False
        self.saved = False

        # configuration options
        self.save_chart = True

        self.dump = True
        self.dump_column_names = False
        self.upload_csv_to_s3 = False

        self.upload_chart_to_s3 = True
        self.generate_all_charts = True
        self.lookahead = datetime.timedelta(90)
        self.cons_rate_diff_threshold = 0.25
        self.anon = True
        self.interactive = False

        self.today = datetime.datetime.today().date()
        if sit_year and sit_month and sit_day:
            self.today = datetime.date(sit_year, sit_month, sit_day)

        self.stocklevels = []
        self.dates = []
        self.levels = []
        self.forecasts = []
        self.fforecasts = []
        self.annual_demand = {}
        self.f_years = []
        self.ff_years = []
        self.s_years = []
        self.has_data = self.get_and_set_vars()


    # calculate projections
    def _calc_stock_levels(self, delivery_type, begin_date, begin_level=None, end_date=None):
        #print 'CALCULATE PROJECTIONS: %s' % delivery_type
        try:
            filtered_deliveries = get_group_all_deliveries_for_type_asc(self.country_pk, self.group_slug, delivery_type)
            #print 'deliveries:'
            #print len(filtered_deliveries)
            #if len(filtered_deliveries) == 0:
            #    return [], []

            def _est_daily_consumption_for_year(year):
                ''' Return daily consumption based on estimated annual demand '''
                if year in self.annual_demand:
                    forecast = self.annual_demand[year]
                    return int(float(forecast)/float(365.0))
                else:
                    if (year - 1) in self.annual_demand:
                        old = self.annual_demand[year-1]
                        return int(float(old)/float(365.0))
                    return 0

            # timedelta representing a change of one day
            one_day = datetime.timedelta(days=1)
            if end_date is None:
                last_day_in_current_year = datetime.date(self.today.year, 12, 31)
                end_date = last_day_in_current_year

            # timedelta representing days we are plotting
            days_to_plot = end_date - begin_date
            #print begin_date
            #print end_date
            #print days_to_plot

            # variables to keep track of running totals while we loop
            annual_begin_levels = {}
            if begin_level is None:
                if delivery_type in ["CO", "UN"]:
                    for f in get_group_all_forecasts_asc(self.country_pk, self.group_slug):
                        if f['initial'] not in [0, '0', '', ' ', None]:
                            annual_begin_levels.update({f['year']:f['initial']})
            if begin_level is not None:
                est_stock_level = begin_level
            else:
                est_stock_level = 0
            est_stock_date = begin_date
            projected_stock_dates = list()
            projected_stock_levels = list()
            year_counter = None

            for day in range(days_to_plot.days):
                # increment date by one day
                this_date = est_stock_date + one_day
                est_stock_date = this_date
                for delivery_type in ["CO", "UN"]:
                    if this_date.year != year_counter:
                        year_counter = this_date.year
                        if this_date.year in annual_begin_levels:
                            if annual_begin_levels[this_date.year] is not None:
                                est_stock_level = annual_begin_levels[this_date.year]
                # check for forecasted deliveries for this date
                deliveries_today = Analysis.filter(filtered_deliveries, 'date', this_date)
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
            #print len(projected_stock_dates)
            #print len(projected_stock_levels)
            return projected_stock_dates, projected_stock_levels
        except Exception,e:
            print 'ERROR PROJECTION'
            print e
            if self.interactive:
                import ipdb; ipdb.set_trace()

    def set_plot_options(self, options_str):
        try:
            # https://twitter.com/#!/raymondh/status/60058896752066560
            self.display_buffers = not not ('B' in options_str)
            self.display_forecast_projection = not not ('F' in options_str)
            self.display_purchased_projection = not not ('P' in options_str)
            self.display_theoretical_forecast = not not ('C' in options_str)
            self.display_adjusted_theoretical_forecast = not not ('U' in options_str)
        except Exception,e:
            print 'ERROR SET PLOT OPTIONS'
            print e
            if self.interactive:
                import ipdb; ipdb.set_trace()

    def plot(self, **kwargs):
        if not self.get_and_set_vars():
            return False
        # string of options (as single characters) in alphabetical order
        # used later for filename
        self.options_str = ''.join(sorted(kwargs.keys()))

        if not self.generate_all_charts:
            # if we are not generating all charts for countrystock,
            # set options based on supplied keyword arguments
            # default to false if options are not specified
            self.calc_buffers = kwargs.get('B', False)
            self.display_buffers = kwargs.get('B', False)
            self.calc_forecast_projection = kwargs.get('F', False)
            self.display_forecast_projection = kwargs.get('F', False)
            self.calc_purchased_projection = kwargs.get('P', False)
            self.display_purchased_projection = kwargs.get('P', False)
            self.calc_theoretical_forecast = kwargs.get('C', False)
            self.display_theoretical_forecast = kwargs.get('C', False)
            self.calc_adjusted_theoretical_forecast = kwargs.get('U', False)
            self.display_adjusted_theoretical_forecast = kwargs.get('U', False)
        else:
            self.options_str = 'BFPCU'
            self.calc_buffers = True
            self.calc_forecast_projection = True
            self.calc_purchased_projection = True
            self.calc_theoretical_forecast = True
            self.calc_adjusted_theoretical_forecast = True
            self.set_plot_options('BFPCU')


        if self.display_buffers:
            try:
                self.three_by_year = dict()
                self.nine_by_year = dict()

                def three_month_buffer(demand_est):
                    return int(float(demand_est) * (float(3.0)/float(12.0)))

                def nine_month_buffer(demand_est):
                    return int(float(demand_est) * (float(9.0)/float(12.0)))

                for year in self.f_years:
                    # create a single key/value pair for each year/sum forecast
                    if year in self.annual_demand:
                        self.three_by_year.update({year:three_month_buffer(self.annual_demand[year])})
                        self.nine_by_year.update({year:nine_month_buffer(self.annual_demand[year])})

                # make a list of corresponding buffer levels for every reported stock level
                first_and_last_days = []
                for i, y in enumerate(sorted(self.three_by_year.keys())):
                    if (i == 0 and (len(self.stocklevels) > 0)):
                        # on the first loop, use the earliest stocklevel
                        # instead of january 1 of that year
                        if self.stocklevels[0]['date'].year in self.three_by_year.keys():
                            first_and_last_days.append(self.stocklevels[0]['date'])
                        else:
                            first_and_last_days.append(datetime.date(y, 1, 1))
                    else:
                        first_and_last_days.append(datetime.date(y, 1, 1))
                    first_and_last_days.append(datetime.date(y, 12, 31))

                self.three_month_buffers = [self.three_by_year[d.year] for d in first_and_last_days if d.year in self.three_by_year]
                self.nine_month_buffers = [self.nine_by_year[d.year] for d in first_and_last_days if d.year in self.nine_by_year]

            except Exception,e:
                print 'ERROR BUFFERS'
                print e
                if self.interactive:
                    import ipdb; ipdb.set_trace()

        try:

            # perform any required calculations before beginning fig
            # construction, so they won't have to be repeated when
            # constructing multiple figs
            projected_ff_dates = []
            projected_ff_levels = []
            if self.calc_forecast_projection and (len(self.stocklevels) > 0):
                projected_ff_dates, projected_ff_levels = self._calc_stock_levels(\
                    "FF", self.stocklevels[-1]['date'], self.stocklevels[-1]['amount'])

            projected_fp_dates = []
            projected_fp_levels = []
            if self.calc_purchased_projection and (len(self.stocklevels) > 0):
                projected_fp_dates, projected_fp_levels = self._calc_stock_levels(\
                    "FP", self.stocklevels[-1]['date'], self.stocklevels[-1]['amount'])

            projected_co_dates = []
            projected_co_levels = []
            if self.calc_theoretical_forecast and (len(self.stocklevels) > 0):
                projected_co_dates, projected_co_levels = self._calc_stock_levels(\
                    "CO", self.stocklevels[0]['date'], None, self.today)

            projected_un_dates = []
            projected_un_levels = []
            if self.calc_adjusted_theoretical_forecast and (len(self.stocklevels) > 0):
                projected_un_dates, projected_un_levels = self._calc_stock_levels(\
                    "UN", self.stocklevels[0]['date'], None, self.today)
        except Exception, e:
            print 'BANG calculations'
            print e

        try:
            if self.dump:

                sl = dict(zip(self.dates, self.levels))
                ff = dict(zip(projected_ff_dates, projected_ff_levels))
                fp = dict(zip(projected_fp_dates, projected_fp_levels))
                co = dict(zip(projected_co_dates, projected_co_levels))
                un = dict(zip(projected_un_dates, projected_un_levels))

                all_years = set(self.f_years + self.ff_years + self.s_years)
                first_date = datetime.date(min(all_years), 1, 1)
                last_date = datetime.date(self.today.year, 12, 31)
                possible_days = last_date - first_date
                one_day = datetime.timedelta(days=1)
                day_pointer = first_date
                time_series = list()
                # TODO always dump one with column names for export and one without for dygraph
                if self.dump_column_names:
                    time_series.append(["date", "actual stock level", "3 month buffer stock level", "9 month overstock level", "future delivery on forecast", "future delivery on purchase", "original country office forecast", "unicef delivery"])
                for day in range(possible_days.days):
                    this_day = day_pointer
                    td = this_day.isoformat()
                    if sl.has_key(this_day):
                        sto = sl[this_day]
                    else:
                        sto = ""
                    if self.three_by_year.has_key(this_day.year):
                        tmo = self.three_by_year[this_day.year]
                    else:
                        tmo = ""
                    if self.nine_by_year.has_key(this_day.year):
                        nmo = self.nine_by_year[this_day.year]
                    else:
                        nmo = ""
                    if ff.has_key(this_day):
                        ffl = str(ff[this_day])
                        if ffl == "0":
                            ffl = ""
                    else:
                        ffl = ""
                    if fp.has_key(this_day):
                        fpl = str(fp[this_day])
                        if fpl == "0":
                            fpl = ""
                    else:
                        fpl = ""
                    if co.has_key(this_day):
                        col = str(co[this_day])
                        if col == "0":
                            col = ""
                    else:
                        col = ""
                    if un.has_key(this_day):
                        unl = str(un[this_day])
                        if unl == "0":
                            unl = ""
                    else:
                        unl = ""
                    # date, stocklevel, 3mo buffer, 9mo overstock, future on forecast, future on po, orig country forecast, unicef delivery
                    time_series.append([td, sto, tmo, nmo, ffl, fpl, col, unl])

                    day_pointer = this_day + one_day

                #file_name = "/tmp/%s_%s_all.csv" % (self.country_pk, self.group_slug)
                country_code = self.country_pk
                file_path = "/home/ubuntu/vax/vaxapp/static/csvs/%s/%s/%s/" % (country_code, self.group_slug, self.today.year)
                file_name = "%s_%s_%s_%s_%s.csv" % (country_code, self.group_slug, self.today.year, self.today.month, self.today.day)
                local_file = file_path + file_name

                anon_country_code = "".join([str(letter_position(l)).zfill(2) for l in self.country_pk])
                anon_file_path = "/home/ubuntu/vax/vaxapp/static/csvs/%s/%s/%s/" % (anon_country_code, self.group_slug, self.today.year)
                anon_file_name = "%s_%s_%s_%s_%s.csv" % (anon_country_code, self.group_slug, self.today.year, self.today.month, self.today.day)
                anon_local_file = anon_file_path + anon_file_name
                try:
                    os.makedirs(file_path)
                except OSError, e:
                    # don't raise if the path already exists,
                    # only if there is another error (permission, etc)
                    if e.errno != errno.EEXIST:
                        raise

                with open(local_file, 'wb') as f:
                    csvwriter = csv.writer(f, delimiter=',')
                    csvwriter.writerows(time_series)

                try:
                    os.makedirs(anon_file_path)
                except OSError, e:
                    # don't raise if the path already exists,
                    # only if there is another error (permission, etc)
                    if e.errno != errno.EEXIST:
                        raise

                with open(anon_local_file, 'wb') as f:
                    csvwriter = csv.writer(f, delimiter=',')
                    csvwriter.writerows(time_series)

                if self.upload_csv_to_s3:
                    # TODO queue uploading with celery so uploading
                    # will not delay generation of next csv
                    try:
                        country_code = self.country_pk
                        if self.anon:
                            country_code = "".join([str(letter_position(l)).zfill(2) for l in self.country_pk])

                        s3_key = "%s_%s_%s_%s_%s.csv" % (country_code, self.group_slug, self.today.year, self.today.month, self.today.day)
                        s3_path = "%s/%s/%s/" % (country_code, self.group_slug, self.today.year)
                        upload_file(filename, 'vaxtrack_csv', s3_path + s3_key, True)
                        print s3_key
                    except Exception, e:
                        print 'ERROR UPLOADING'
                        print e

                return
        except Exception, e:
            print 'BANG dump'
            print e
            if self.interactive:
                import ipdb; ipdb.set_trace()

    def analyze(self):
        if not self.get_and_set_vars():
            return False
        print '~~~~ANALYZING~~~~'
        print self.country_pk
        print self.vaccine_abbr
        print self.group_slug
        print '~~~~~~~~~~~~~~~~~'
        try:
            last_s = {}
            self.consumed_in_year = {}

            # populate dicts with years and 0s
            for y in self.s_years:
                self.consumed_in_year.update({y:0})
                last_s.update({y:0})
            print self.s_years

            for d in get_group_all_stocklevels_asc(self.country_pk, self.group_slug):
                yr = int(d['year'])
                s = int(d['amount'])
                if not yr in self.s_years:
                    continue
                # if this day's stocklevel is less than the last stocklevel...
                if s <= last_s[yr]:
                    # amount consumed this day is difference between
                    # this day's stocklevel and the last one
                    consumed_today = last_s[yr] - s
                    # add this amount to this year's running total
                    consumed_this_year = self.consumed_in_year[yr] + consumed_today
                    # update dict with new sum
                    self.consumed_in_year.update({yr:consumed_this_year})

                # set this day's stocklevel as last one and continue looping
                last_s[yr] = s
            print self.consumed_in_year

            self.actual_cons_rate = {}
            self.days_of_stock_data = {}
            for y in self.s_years:
                # get all stocklevel datapoints from year
                stocklevels_in_year = get_group_type_for_year_asc(self.country_pk, self.group_slug, 'SL', y, 'unknown')
                print len(stocklevels_in_year)
                # find number of days enclosed between first stocklevel entry of year and last
                if len(stocklevels_in_year) > 0:
                    self.days_of_stock_data.update({y:(stocklevels_in_year[-1]['date'] - stocklevels_in_year[0]['date']).days})
                    rate = float(self.consumed_in_year[y])/float(self.days_of_stock_data[y])
                    self.actual_cons_rate.update({y:int(rate)})

            print self.actual_cons_rate

            # "Query 2" Order Lead Time
            # see if there are forecasted deliveries and/or purchased deliveries
            # scheduled for the near future
            print 'Query 2'
            self.forecasted_this_year = get_group_type_for_year_asc(self.country_pk, self.group_slug, "FF", self.today.year)
            self.on_po_this_year = get_group_type_for_year_asc(self.country_pk, self.group_slug, "FP", self.today.year)

            self.upcoming_on_po = [d for d in self.on_po_this_year if ((d['date'] - self.today) <= self.lookahead)]
            self.doses_on_orders = reduce(lambda s,d: s + d['amount'], self.on_po_this_year, 0)
            self.upcoming_forecasted = [d for d in self.forecasted_this_year if ((d['date'] - self.today) <= self.lookahead)]

            if self.today.year not in self.f_years:
                # if there is no forecast for the reference date's year,
                # don't perform any of these queries
                self.analyzed = True
                return

            if len(self.stocklevels) == 0:
                self.analyzed = True
                return
            else:
                self.has_stock_data = True


            # "Query 1" Forecast Accuracy
            # for this year, see how actual consumption rate compares to estimated daily rate
            print 'Query 1'
            est_cons_rate = int(float(self.annual_demand[self.today.year])/float(365))
            print est_cons_rate
            if self.today.year in self.actual_cons_rate:
                rate_difference = float(abs(est_cons_rate - self.actual_cons_rate[self.today.year]))/float(est_cons_rate)
                print rate_difference
                # flag if difference is greater than threshold
                if rate_difference > self.cons_rate_diff_threshold:
                    print '***FLAG***'
                    print 'major difference between forecast and actual consumption rates'
                    handle_alert(countrystock=self.cs,\
                        reference_date=self.today, status='W', risk='F', text='C')


            # "Query 3" Stock Management
            # see how many months worth of supply are in stock
            print 'Query 3'
            latest_stocklevel = self.stocklevels[0]

            if self.today.year in self.annual_demand:
                self.est_daily_cons = int(float(self.annual_demand[self.today.year])/float(365))
                self.days_of_stock = int(float(latest_stocklevel['amount'])/float(self.est_daily_cons))
                print '%s days of stock' % str(self.days_of_stock)

                # check if there is too much stock (more than nine months' worth)
                if self.days_of_stock >= 270:
                    # "Query 4" Stock Management
                    # flag if there are any upcoming deliveries (forecasted or purchased)
                    print 'Query 4'
                    if (len(self.upcoming_forecasted) > 0) or (len(self.upcoming_on_po) > 0):
                        print '***FLAG***'
                        print 'delay or reduce shipment'
                        handle_alert(countrystock=self.cs,\
                            reference_date=self.today, status='U', risk='O', text='D')
                    else:
                        print '---OK---'

            this_years_levels = Analysis.filter(self.stocklevels, 'year', self.today.year)
            if len(this_years_levels) > 0:
                self.first_level_this_year = Analysis.filter(self.stocklevels, 'year', self.today.year)[-1]['amount']
                self.deliveries_this_year = get_group_type_for_year(self.country_pk, self.group_slug, "UN", self.today.year)

                self.doses_delivered_this_year = reduce(lambda s,d: s + d['amount'], self.deliveries_this_year, 0)
                #self.doses_on_orders = reduce(lambda s,d: s + d['amount'], self.upcoming_on_po, 0)

                self.demand_for_period = self.lookahead.days * self.est_daily_cons

                # "Query 5" Stock Management
                # calculate % coverage of annual need
                print 'Query 5'
                self.percent_coverage = float(self.first_level_this_year + self.doses_delivered_this_year)/float(self.annual_demand[self.today.year])
                print '%s percent coverage' % str(self.percent_coverage)

            else:
                self.percent_coverage = 0
                self.demand_for_period = 0

            # check if there is insufficient stock (less than three months' worth)
            if self.days_of_stock <= 90:

                if (self.percent_coverage >= (0.25 + float(self.today.month)/12.0)) and (self.percent_coverage <= (0.5 + float(self.today.month)/12.0)):
                    print '---OK---'

                if self.percent_coverage < (0.25 + float(self.today.month)/12.0):
                    # "Query 7" Stock Management
                    if (len(self.upcoming_on_po) > 0):
                        if self.doses_on_orders < self.demand_for_period:
                            print '***FLAG***'
                            print 'risk of stockout'
                            print 'order immediately -- not enough on upcoming deliveries'
                            handle_alert(countrystock=self.cs,\
                                reference_date=self.today, status='U', risk='S', text='I')
                        else:
                            print '---OK---'

                    elif (len(self.upcoming_forecasted) > 0):
                        print '***FLAG***'
                        print 'risk of stockout'
                        print 'order immediately - purchase forecasted delivery'
                        handle_alert(countrystock=self.cs,\
                            reference_date=self.today, status='U', risk='S', text='F')

                    else:
                        print '***FLAG***'
                        print 'risk of stockout'
                        print 'order immediately - no supply on PO or forecasted for next 3 months'
                        handle_alert(countrystock=self.cs,\
                            reference_date=self.today, status='U', risk='S', text='P')

                if self.percent_coverage > (0.5 + float(self.today.month)/12.0):

                    if (len(self.upcoming_on_po) > 0):
                        if self.doses_on_orders <= self.demand_for_period:
                            print '---OK---'

                        # "Query 6a" Stock Management
                        if self.doses_on_orders > self.demand_for_period:
                            print '***FLAG***'
                            print 'risk of overstocking'
                            print 'delay shipment -- more than enough on upcoming deliveries'
                            handle_alert(countrystock=self.cs,\
                                reference_date=self.today, status='U', risk='O', text='E')

                    elif (len(self.upcoming_forecasted) > 0):
                        self.forecasts_next_month = [d for d in self.upcoming_forecasted if d['date'].month == (self.today.month + 1)]
                        if len(self.forecasts_next_month) > 0:
                            print '***FLAG***'
                            print 'risk of overstocking'
                            print 'delay order - delay purchase of forecasted delivery'
                            handle_alert(countrystock=self.cs,\
                                reference_date=self.today, status='U', risk='O', text='O')
                            alert.analyzed = datetime.datetime.now()
                            alert.save()

                    else:
                        print '---OK---'

            self.analyzed = True
        except Exception, e:
            print 'ERROR ANALYZING'
            print e
            if self.interactive:
                import ipdb; ipdb.set_trace()

    def save_stats(self):
        # ensure that analyze() and plot()
        # have been called. otherwise, many
        # of the variables below will have no value
        if not self.analyzed:
            self.analyze()
        if not self.plotted:
            self.plot()
        try:
            css = CountryStockStats()
            css.countrystock = self.cs
            css.analyzed = datetime.datetime.now()
            css.reference_date = self.today

            if hasattr(self, "has_stock_data"):
                css.has_stock_data = True

            if hasattr(self, "consumed_in_year"):
                css.consumed_in_year = Dicty.create('consumed_in_year', self.consumed_in_year)
            if hasattr(self, "actual_cons_rate"):
                css.actual_cons_rate = Dicty.create('actual_cons_rate', self.actual_cons_rate)
            if hasattr(self, "annual_demand"):
                css.annual_demand = Dicty.create('annual_demand', self.annual_demand)
            if hasattr(self, "three_by_year"):
                css.three_by_year = Dicty.create('three_by_year', self.three_by_year)
            if hasattr(self, "nine_by_year"):
                css.nine_by_year = Dicty.create('nine_by_year', self.nine_by_year)
            if hasattr(self, "days_of_stock_data"):
                css.days_of_stock_data = Dicty.create('days_of_stock_data', self.days_of_stock_data)

            if hasattr(self, "est_daily_cons"):
                css.est_daily_cons = self.est_daily_cons
            if hasattr(self, "days_of_stock"):
                css.days_of_stock = self.days_of_stock

            if hasattr(self, "doses_delivered_this_year"):
                css.doses_delivered_this_year = self.doses_delivered_this_year
            if hasattr(self, "doses_on_orders"):
                css.doses_on_orders = self.doses_on_orders
            if hasattr(self, "demand_for_period"):
                css.demand_for_period = self.demand_for_period
            if hasattr(self, "percent_coverage"):
                css.percent_coverage = self.percent_coverage
            css.save()
            self.saved = True
        except Exception, e:
            print 'ERROR SAVING STATS'
            print e
            if self.interactive:
                import ipdb; ipdb.set_trace()
