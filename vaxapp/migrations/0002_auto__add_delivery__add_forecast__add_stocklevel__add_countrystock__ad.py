# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Delivery'
        db.create_table('vaxapp_delivery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.CountryStock'])),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Delivery'])

        # Adding model 'Forecast'
        db.create_table('vaxapp_forecast', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.CountryStock'])),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('demand_est', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Forecast'])

        # Adding model 'StockLevel'
        db.create_table('vaxapp_stocklevel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country_stock', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.CountryStock'])),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['StockLevel'])

        # Adding model 'CountryStock'
        db.create_table('vaxapp_countrystock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vaccine', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.Vaccine'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.Country'])),
        ))
        db.send_create_signal('vaxapp', ['CountryStock'])

        # Adding field 'Vaccine.abbr'
        db.add_column('vaxapp_vaccine', 'abbr', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Delivery'
        db.delete_table('vaxapp_delivery')

        # Deleting model 'Forecast'
        db.delete_table('vaxapp_forecast')

        # Deleting model 'StockLevel'
        db.delete_table('vaxapp_stocklevel')

        # Deleting model 'CountryStock'
        db.delete_table('vaxapp_countrystock')

        # Deleting field 'Vaccine.abbr'
        db.delete_column('vaxapp_vaccine', 'abbr')


    models = {
        'vaxapp.country': {
            'Meta': {'object_name': 'Country'},
            'iso3_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'iso_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'numerical_code': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Region']", 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.countrystock': {
            'Meta': {'object_name': 'CountryStock'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vaccine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Vaccine']"})
        },
        'vaxapp.delivery': {
            'Meta': {'object_name': 'Delivery'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'country_stock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.CountryStock']"}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.forecast': {
            'Meta': {'object_name': 'Forecast'},
            'country_stock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.CountryStock']"}),
            'demand_est': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'vaxapp.region': {
            'Meta': {'object_name': 'Region'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.stocklevel': {
            'Meta': {'object_name': 'StockLevel'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'country_stock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.CountryStock']"}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'vaxapp.vaccine': {
            'Meta': {'object_name': 'Vaccine'},
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['vaxapp']
