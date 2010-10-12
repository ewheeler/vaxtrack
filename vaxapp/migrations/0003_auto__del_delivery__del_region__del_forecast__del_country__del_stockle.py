# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Delivery'
        db.delete_table('vaxapp_delivery')

        # Deleting model 'Region'
        db.delete_table('vaxapp_region')

        # Deleting model 'Forecast'
        db.delete_table('vaxapp_forecast')

        # Deleting model 'Country'
        db.delete_table('vaxapp_country')

        # Deleting model 'StockLevel'
        db.delete_table('vaxapp_stocklevel')

        # Renaming column for 'CountryStock.country' to match new field type.
        db.rename_column('vaxapp_countrystock', 'country_id', 'country')
        # Changing field 'CountryStock.country'
        db.alter_column('vaxapp_countrystock', 'country', self.gf('django.db.models.fields.CharField')(max_length=4, null=True))

        # Removing index on 'CountryStock', fields ['country']
        db.delete_index('vaxapp_countrystock', ['country_id'])


    def backwards(self, orm):
        
        # Adding index on 'CountryStock', fields ['country']
        db.create_index('vaxapp_countrystock', ['country_id'])

        # Adding model 'Delivery'
        db.create_table('vaxapp_delivery', (
            ('country_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.CountryStock'])),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('vaxapp', ['Delivery'])

        # Adding model 'Region'
        db.create_table('vaxapp_region', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Region'])

        # Adding model 'Forecast'
        db.create_table('vaxapp_forecast', (
            ('country_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.CountryStock'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('demand_est', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Forecast'])

        # Adding model 'Country'
        db.create_table('vaxapp_country', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
            ('numerical_code', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.Region'], null=True, blank=True)),
            ('printable_name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('iso_code', self.gf('django.db.models.fields.CharField')(max_length=2, primary_key=True)),
            ('iso3_code', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Country'])

        # Adding model 'StockLevel'
        db.create_table('vaxapp_stocklevel', (
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('country_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.CountryStock'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('vaxapp', ['StockLevel'])

        # Renaming column for 'CountryStock.country' to match new field type.
        db.rename_column('vaxapp_countrystock', 'country', 'country_id')
        # Changing field 'CountryStock.country'
        db.alter_column('vaxapp_countrystock', 'country_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.Country']))


    models = {
        'vaxapp.countrystock': {
            'Meta': {'object_name': 'CountryStock'},
            'country': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vaccine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Vaccine']"})
        },
        'vaxapp.vaccine': {
            'Meta': {'object_name': 'Vaccine'},
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['vaxapp']
