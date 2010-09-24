#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    region = models.ForeignKey('Region', blank=True, null=True)

    printable_name = models.CharField(max_length=80)
    iso_code = models.CharField(max_length=2, primary_key=True)
    iso3_code = models.CharField(max_length=3, blank=True, null=True)
    numerical_code = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.printable_name

    class Meta:
        verbose_name_plural = "countries"

class Region(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    
class Vaccine(models.Model):
    name = models.CharField(max_length=160, blank=True, null=True)
    abbr = models.CharField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return self.abbr

class CountryStock(models.Model):
    vaccine = models.ForeignKey(Vaccine)
    country = models.ForeignKey(Country)

    def __unicode__(self):
        return "%s: %s" % (self.country, self.vaccine)

class StockLevel(models.Model):
    country_stock = models.ForeignKey(CountryStock)
    amount = models.PositiveIntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return "%s %s %s" % (self.country_stock, self.date, self.amount)

class Forecast(models.Model):
    country_stock = models.ForeignKey(CountryStock)
    year = models.PositiveIntegerField(blank=True, null=True)
    demand_est = models.PositiveIntegerField(blank=True, null=True)

    @property
    def three_month_buffer(self):
        if self.demand_est is not None:
            return int(float(self.demand_est) * (float(3.0)/float(12.0)))

    @property
    def nine_month_buffer(self):
        if self.demand_est is not None:
            return int(float(self.demand_est) * (float(9.0)/float(12.0)))

    def __unicode__(self):
        return "%s %s" % (self.country_stock, self.year)

class Delivery(models.Model):
    DELIVERY_TYPE_CHOICES = (
        ('CO', 'original CO'),
        ('UN', 'UNICEF delivery'),
        ('FP', 'future on PO'),
        ('FF', 'future on forecast'),
    )
    country_stock = models.ForeignKey(CountryStock)
    amount = models.PositiveIntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    type = models.CharField(max_length=4, choices=DELIVERY_TYPE_CHOICES, blank=True, null=True)

    def __unicode__(self):
        return "%s %s %s" % (self.country_stock, self.amount, self.get_type_display())

    class Meta:
        verbose_name_plural = "deliveries"
