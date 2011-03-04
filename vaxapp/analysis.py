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

from django.db.models import Sum

from vax import import_data
from vax.vsdb import *
from vax.vs3 import upload_file
from .tasks import process_file
from .models import *

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
        analysis = Analysis(country_pk=country_pk, vaccine_abbr=vaccine_abbr, lang=lang, **params)
        analysis.plot()
        analysis.analyze()

def generate_six_charts_country_sdb(country_pk=None, lang=None):
    #for v in ['opv-50', 'measles', 'tt-10', 'dtp-hepbhib-1', 'yf-1', 'bcg-10']:
    for v in ['tt-10', 'dtp-hepbhib-1']:
        print generate_all_charts_country_sdb(country_pk=country_pk, vaccine_abbr=v, lang=lang)

def generate_demo_charts():
    for country in ['ML', 'TD']:
        for vax in ['BCG']:
            print generate_all_charts_country_sdb(country_pk=country, vaccine_abbr=vax, lang='en')

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


    def __init__(self, country_pk=None, vaccine_abbr=None, lang=None, **kwargs):
        # string of options (as single characters) in alphabetical order
        # used later for filename
        self.options_str = ''.join(sorted(kwargs.keys()))

        self.country_pk = country_pk
        self.vaccine_abbr = vaccine_abbr
        self.lang = lang

        # configuration options
        self.save_chart = True
        self.upload_chart_to_s3 = False
        self.lookahead = datetime.timedelta(90)

        # TODO XXX back to the present!
        #self.today = datetime.datetime.today().date()
        self.today = datetime.date(2010, 2, 15)

        # default to false if options are not specified
        self.display_buffers = kwargs.get('B', False)
        self.display_forecast_projection = kwargs.get('F', False)
        self.display_purchased_projection = kwargs.get('P', False)
        self.display_theoretical_forecast = kwargs.get('C', False)
        self.display_adjusted_theoretical_forecast = kwargs.get('U', False)


        try:
            self.stocklevels = all_stocklevels_desc(self.country_pk, self.vaccine_abbr)

            self.dates = Analysis.values_list(self.stocklevels, 'date')
            self.levels = Analysis.values_list(self.stocklevels, 'amount')

            self.forecasts = all_forecasts_asc(self.country_pk, self.vaccine_abbr)

            self.annual_demand = {}
            # get list of years we are dealing with
            self.f_years = list(set(Analysis.values_list(self.forecasts, 'year')))
            for year in self.f_years:
                annual = []
                # get list of forecasts for each year
                fy = Analysis.filter(self.forecasts, 'year', year)
                for f in fy:
                    # add forecasts for this year to list
                    annual.append(f['amount'])
                self.annual_demand.update({year:sum(annual)})

        except Exception,e:
            print 'ERROR INIT'
            print e
            import ipdb; ipdb.set_trace()


    # calculate projections
    def _calc_stock_levels(self, delivery_type, begin_date, begin_level, end_date=None):
        try:
            filtered_deliveries = all_deliveries_for_type_asc(self.country_pk, self.vaccine_abbr, delivery_type)

            def _est_daily_consumption_for_year(year):
                ''' Return daily consumption based on estimated annual demand '''
                forecast = self.annual_demand[year]
                return int(float(forecast)/float(365.0))

            # timedelta representing a change of one day
            one_day = datetime.timedelta(days=1)
            if end_date is None:
                last_day_in_current_year = datetime.date(self.today.year, 12, 31)
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
            return projected_stock_dates, projected_stock_levels
        except Exception,e:
            print 'ERROR PROJECTION'
            print e
            import ipdb; ipdb.set_trace()

    def plot(self):
        if self.display_buffers:
            try:
                three_by_year = dict()
                nine_by_year = dict()

                def three_month_buffer(demand_est):
                    return int(float(demand_est) * (float(3.0)/float(12.0)))

                def nine_month_buffer(demand_est):
                    return int(float(demand_est) * (float(9.0)/float(12.0)))

                for year in self.f_years:
                    # create a single key/value pair for each year/sum forecast
                    three_by_year.update({year:three_month_buffer(self.annual_demand[year])})
                    nine_by_year.update({year:nine_month_buffer(self.annual_demand[year])})

                # make a list of corresponding buffer levels for every reported stock level
                first_and_last_days = []
                for i, y in enumerate(sorted(three_by_year.keys())):
                    if i == 0:
                        # on the first loop, use the earliest stocklevel
                        # instead of january 1 of that year
                        first_and_last_days.append(self.stocklevels[-1]['date'])
                    else:
                        first_and_last_days.append(datetime.date(y, 1, 1))
                    first_and_last_days.append(datetime.date(y, 12, 31))

                self.three_month_buffers = [three_by_year[d.year] for d in first_and_last_days]
                self.nine_month_buffers = [nine_by_year[d.year] for d in first_and_last_days]

            except Exception,e:
                print 'ERROR BUFFERS'
                print e
                import ipdb; ipdb.set_trace()

        try:
            # documentation sez figsize is in inches (!?)
            fig = figure(figsize=(15,12))

            # add country name and vaccine as chart title
            title = "%s %s" % (self.country_pk, self.vaccine_abbr)
            fig.suptitle(title, fontsize=18)

            # add timestamp to lower left corner
            colophon = "Generated by VaxTrack on %s (GMT -5)" %\
                (str(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")))
            fig.text(0,0,colophon, fontsize=8)
            ax = fig.add_subplot(111)

            # plot stock levels
            ax.plot_date(self.dates, self.levels, '-', drawstyle='steps', color='blue',\
                label='actual stock')

            if self.display_buffers:
                # plot 3 and 9 month buffer levels as red lines
                ax.plot_date(first_and_last_days, self.three_month_buffers, '-', drawstyle='steps',\
                    color='red', label='3 month buffer')
                ax.plot_date(first_and_last_days, self.nine_month_buffers, '-', drawstyle='steps',\
                    color='red', label='9 month buffer')

            if self.display_forecast_projection:
                projected_ff_dates, projected_ff_levels = self._calc_stock_levels(\
                    "FF", self.stocklevels[0]['date'], self.stocklevels[0]['amount'])
                ax.plot_date(projected_ff_dates, projected_ff_levels, '--',\
                    drawstyle='steps', color='purple',\
                    label='projected stock based on forecast')

            if self.display_purchased_projection:
                projected_fp_dates, projected_fp_levels = self._calc_stock_levels(\
                    "FP", self.stocklevels[0]['date'], self.stocklevels[0]['amount'])
                ax.plot_date(projected_fp_dates, projected_fp_levels, '--',\
                drawstyle='steps', color='blue',\
                label='projected stock based on placed POs')

            if self.display_theoretical_forecast:
                # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
                projected_co_dates, projected_co_levels = self._calc_stock_levels(\
                    "CO", self.stocklevels[-2]['date'], self.stocklevels[-2]['amount'])
                ax.plot_date(projected_co_dates, projected_co_levels, '--',\
                drawstyle='steps', color='green',\
                label='theoretical stock based on forecast')

            if self.display_adjusted_theoretical_forecast:
                # TODO use the first stocklevel -- using second because the first data point for chad is really low (incorrect)
                projected_un_dates, projected_un_levels = self._calc_stock_levels(\
                    "UN", self.stocklevels[-2]['date'], self.stocklevels[-2]['amount'])
                ax.plot_date(projected_un_dates, projected_un_levels, '--',\
                drawstyle='steps', color='orange',\
                label='theoretical stock adjusted with deliveries')

            years    = YearLocator()   # every year
            months   = MonthLocator()  # every month
            yearsFmt = DateFormatter('%Y')

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

        if self.save_chart:
            try:
                filename = "%s-%s-%s.png" % (self.country_pk, self.vaccine_abbr, self.options_str)
                file_path = "/tmp/" + filename
                fig.savefig(file_path)
            except Exception, e:
                print 'ERROR SAVING'
                print e
                import ipdb; ipdb.set_trace()

        if self.upload_chart_to_s3:
            try:
                # TODO make these configurable? same with sdb domain?
                #s3_key = "%s-%s-%s-%s.png" % (lang, country_pk, vaccine_abbr, options_str)
                #s3_path = "%s/%s/%s/" % (lang, country_pk, vaccine_abbr)
                #upload_file(file_path, 'vaxtrack_charts', s3_path + s3_key, True)
                demo_key = "%s-%s-%s.png" % (self.country_pk, self.vaccine_abbr, self.options_str)
                upload_file(file_path, 'vaxtrack_charts', demo_key, True)
                return file_path
            except Exception, e:
                print 'ERROR UPLOADING'
                print e
                import ipdb; ipdb.set_trace()

    def analyze(self):
        try:
            last_s = {}
            self.consumed_in_year = {}

            # populate dicts with years and 0s
            for y in self.f_years:
                self.consumed_in_year.update({y:0})
                last_s.update({y:0})

            for d in all_stocklevels_asc(self.country_pk, self.vaccine_abbr):
                yr = int(d['year'])
                s = int(d['amount'])
                if not yr in self.f_years:
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

            self.actual_cons_rate = {}
            for y in self.f_years:
                rate = float(self.consumed_in_year[y])/float(365)
                self.actual_cons_rate.update({y:int(rate)})

            # see if there are forecasted deliveries and/or purchased deliveries
            # scheduled for the near future
            self.forecasted_this_year = type_for_year_asc(self.country_pk, self.vaccine_abbr, "FF", self.today.year)
            self.on_po_this_year = type_for_year_asc(self.country_pk, self.vaccine_abbr, "FP", self.today.year)

            self.upcoming_on_po = [d for d in self.on_po_this_year if ((d['date'] - self.today) <= self.lookahead)]
            self.upcoming_forecasted = [d for d in self.forecasted_this_year if ((d['date'] - self.today) <= self.lookahead)]

            # see how many months worth of supply are in stock
            latest_stocklevel = self.stocklevels[0]

            self.est_daily_cons = int(float(self.annual_demand[self.today.year])/float(365))
            self.days_of_stock = int(float(latest_stocklevel['amount'])/float(self.est_daily_cons))
            print '%s days of stock' % str(self.days_of_stock)

            # check if there is too much stock (more than nine months' worth)
            if self.days_of_stock >= 270:
                # flag if there are any upcoming deliveries (forecasted or purchased)
                if (len(self.upcoming_forecasted) > 0) or (len(self.upcoming_on_po) > 0):
                    print '***FLAG***'
                    print 'delay or reduce shipment'
                else:
                    print '---OK---'

            self.first_level_this_year = Analysis.filter(self.stocklevels, 'year', self.today.year)[-1]['amount']
            self.deliveries_this_year = type_for_year(self.country_pk, self.vaccine_abbr, "UN", self.today.year)

            self.doses_delivered_this_year = reduce(lambda s,d: s + d['amount'], self.deliveries_this_year, 0)
            self.doses_on_orders = reduce(lambda s,d: s + d['amount'], self.upcoming_on_po, 0)

            self.demand_for_period = self.lookahead.days * self.est_daily_cons

            # calculate % coverage of annual need
            self.percent_coverage = float(self.first_level_this_year + self.doses_delivered_this_year)/float(self.annual_demand[self.today.year])
            print '%s percent coverage' % str(self.percent_coverage)

            # check if there is insufficient stock (less than three months' worth)
            if self.days_of_stock <= 90:

                if (self.percent_coverage >= (0.25 + float(self.today.month)/12.0)) and (self.percent_coverage <= (0.5 + float(self.today.month)/12.0)):
                    print '---OK---'

                if self.percent_coverage < (0.25 + float(self.today.month)/12.0):
                    if (len(self.upcoming_on_po) > 0):
                        if self.doses_on_orders < self.demand_for_period:
                            print '***FLAG***'
                            print 'risk of stockout'
                            print 'order immediately -- not enough on upcoming deliveries'
                        else:
                            print '---OK---'

                    elif (len(self.upcoming_forecasted) > 0):
                        print '***FLAG***'
                        print 'risk of stockout'
                        print 'order immediately - purchase forecasted delivery'

                    else:
                        print '***FLAG***'
                        print 'risk of stockout'
                        print 'order immediately - no supply on PO or forecasted for next 3 months'

                if self.percent_coverage > (0.5 + float(self.today.month)/12.0):

                    if (len(self.upcoming_on_po) > 0):
                        if self.doses_on_orders <= self.demand_for_period:
                            print '---OK---'

                        if self.doses_on_orders > self.demand_for_period:
                            print '***FLAG***'
                            print 'risk of overstocking'
                            print 'delay shipment -- more than enough on upcoming deliveries'

                    elif (len(self.upcoming_forecasted) > 0):
                        self.forecasts_next_month = [d for d in self.upcoming_forecasted if d['date'].month == (self.today.month + 1)]
                        if len(self.forecasts_next_month) > 0:
                            print '***FLAG***'
                            print 'risk of overstocking'
                            print 'delay order - delay purchase of forecasted delivery'

                    else:
                        print '---OK---'

        except Exception, e:
            print 'ERROR ANALYZING'
            print e
            import ipdb; ipdb.set_trace()

    def save_stats(self):
        v = Vaccine.lookup_slug(self.vaccine_abbr)
        if v is None:
            return 'couldnt find vaccine'
        cs = CountryStock.objects.get(country=self.country_pk, vaccine=v)
        if cs is None:
            return 'couldnt find countrystock'
        css = CountryStockStats()
        css.countrystock = cs
        css.analyzed = datetime.datetime.now()
        css.reference_date = self.today

        css.consumed_in_year = repr(self.consumed_in_year)
        css.actual_cons_rate = repr(self.actual_cons_rate)
        css.annual_demand = repr(self.annual_demand)
        css.three_month_buffers = repr(self.three_month_buffers)
        css.nine_month_buffers = repr(self.nine_month_buffers)

        css.est_daily_cons = self.est_daily_cons
        css.days_of_stock = self.days_of_stock

        css.doses_delivered_this_year = self.doses_delivered_this_year
        css.doses_on_orders = self.doses_on_orders
        css.demand_for_period = self.demand_for_period
        css.percent_coverage = self.percent_coverage
        css.save()
