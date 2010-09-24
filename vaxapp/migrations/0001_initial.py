# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Country'
        db.create_table('vaxapp_country', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vaxapp.Region'], null=True, blank=True)),
            ('printable_name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('iso_code', self.gf('django.db.models.fields.CharField')(max_length=2, primary_key=True)),
            ('iso3_code', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('numerical_code', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Country'])

        # Adding model 'Region'
        db.create_table('vaxapp_region', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Region'])

        # Adding model 'Vaccine'
        db.create_table('vaxapp_vaccine', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
        ))
        db.send_create_signal('vaxapp', ['Vaccine'])


    def backwards(self, orm):
        
        # Deleting model 'Country'
        db.delete_table('vaxapp_country')

        # Deleting model 'Region'
        db.delete_table('vaxapp_region')

        # Deleting model 'Vaccine'
        db.delete_table('vaxapp_vaccine')


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
        'vaxapp.region': {
            'Meta': {'object_name': 'Region'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        },
        'vaxapp.vaccine': {
            'Meta': {'object_name': 'Vaccine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['vaxapp']
