# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'CountryStockStats.days_of_stock_data'
        db.add_column('vaxapp_countrystockstats', 'days_of_stock_data', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='days_of_stock_data', null=True, to=orm['vaxapp.Dicty']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'CountryStockStats.days_of_stock_data'
        db.delete_column('vaxapp_countrystockstats', 'days_of_stock_data_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'vaxapp.alert': {
            'Meta': {'object_name': 'Alert'},
            'analyzed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'countrystock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.CountryStock']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reference_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'risk': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '2', 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.country': {
            'Meta': {'object_name': 'Country'},
            'iso2_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'numerical_code': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        'vaxapp.countrystock': {
            'Meta': {'object_name': 'CountryStock'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5_hash': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'vaccine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Vaccine']"})
        },
        'vaxapp.countrystockstats': {
            'Meta': {'object_name': 'CountryStockStats'},
            'actual_cons_rate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'actual_cons_rate'", 'null': 'True', 'to': "orm['vaxapp.Dicty']"}),
            'analyzed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'annual_demand': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'annual_demand'", 'null': 'True', 'to': "orm['vaxapp.Dicty']"}),
            'consumed_in_year': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'consumed_in_year'", 'null': 'True', 'to': "orm['vaxapp.Dicty']"}),
            'countrystock': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.CountryStock']"}),
            'days_of_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'days_of_stock_data': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'days_of_stock_data'", 'null': 'True', 'to': "orm['vaxapp.Dicty']"}),
            'demand_for_period': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'doses_delivered_this_year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'doses_on_orders': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'est_daily_cons': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nine_by_year': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'nine_by_year'", 'null': 'True', 'to': "orm['vaxapp.Dicty']"}),
            'percent_coverage': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'reference_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'three_by_year': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'three_by_year'", 'null': 'True', 'to': "orm['vaxapp.Dicty']"})
        },
        'vaxapp.dicty': {
            'Meta': {'object_name': 'Dicty'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160'})
        },
        'vaxapp.document': {
            'Meta': {'object_name': 'Document'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'date_exception': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_process_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_process_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_queued': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_stored': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_uploaded': ('django.db.models.fields.DateTimeField', [], {}),
            'exception': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_document': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'remote_document': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        'vaxapp.keyval': {
            'Meta': {'object_name': 'KeyVal'},
            'dicty': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Dicty']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'val': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Country']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'vaxapp.vaccine': {
            'Meta': {'object_name': 'Vaccine'},
            'abbr_en': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'abbr_en_alt': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'abbr_fr': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'abbr_fr_alt': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.VaccineGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.vaccinegroup': {
            'Meta': {'object_name': 'VaccineGroup'},
            'abbr_en': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'abbr_fr': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['vaxapp']
