#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import hashlib

from vaxapp.models import *
import boto

def goboto():
    sdb = boto.connect_sdb()

    countries = Country.objects.all()
    domain = sdb.create_domain('countrystockdata')
    
    for country in countries:

        countrystocks = country.countrystock_set.all()
        for countrystock in countrystocks:
            stock_levels = countrystock.stocklevel_set.all()
            forecasts = countrystock.forecast_set.all()
            deliveries = countrystock.delivery_set.all()

            for stock_level in stock_levels:
                try:
                    item_name = hashlib.md5()
                    item_name.update(str(country.iso_code))
                    item_name.update(str(countrystock.vaccine.abbr))
                    item_name.update("SL")
                    item_name.update(str(stock_level.date))
                    item_name.update(str(stock_level.amount))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country.iso_code))
                    item.add_value("supply", str(countrystock.vaccine.abbr))
                    item.add_value("type", "SL")
                    item.add_value("date", str(stock_level.date))
                    item.add_value("year", str(stock_level.date.year))
                    item.add_value("amount", str(stock_level.amount))
                    item.save()
                    print item
                except Exception, e:
                    print 'error creating stock level'
                    print e

            for forecast in forecasts:
                try:
                    item_name = hashlib.md5()
                    item_name.update(str(country.iso_code))
                    item_name.update(str(countrystock.vaccine.abbr))
                    item_name.update("CF")
                    item_name.update(str(forecast.year))
                    item_name.update(str(forecast.demand_est))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country.iso_code))
                    item.add_value("supply", str(countrystock.vaccine.abbr))
                    item.add_value("type", "CF")
                    item.add_value("date", str(forecast.year))
                    item.add_value("year", str(forecast.year))
                    item.add_value("amount", str(forecast.demand_est))
                    item.save()
                    print item
                except Exception, e:
                    print 'error creating forecast'
                    print e

            for delivery in deliveries:
                try:
                    item_name = hashlib.md5()
                    item_name.update(str(country.iso_code))
                    item_name.update(str(countrystock.vaccine.abbr))
                    item_name.update(str(delivery.type))
                    item_name.update(str(delivery.date))
                    item_name.update(str(delivery.amount))

                    item = domain.new_item(item_name.hexdigest())
                    item.add_value("country", str(country.iso_code))
                    item.add_value("supply", str(countrystock.vaccine.abbr))
                    item.add_value("type", str(delivery.type))
                    item.add_value("date", str(delivery.date))
                    item.add_value("year", str(delivery.date.year))
                    item.add_value("amount", str(delivery.amount))
                    item.save()
                    print item
                except Exception, e:
                    print 'error creating delivery'
                    print e
