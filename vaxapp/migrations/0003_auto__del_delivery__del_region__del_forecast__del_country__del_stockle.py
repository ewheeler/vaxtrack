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

        # Adding model 'UserProfile'
        db.create_table('vaxapp_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('vaxapp', ['UserProfile'])

        # Deleting field 'CountryStock.country'
        db.delete_column('vaxapp_countrystock', 'country_id')

        # Adding field 'CountryStock.country_iso_code'
        db.add_column('vaxapp_countrystock', 'country_iso_code', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
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

        # Deleting model 'UserProfile'
        db.delete_table('vaxapp_userprofile')

        # Adding field 'CountryStock.country'
        db.add_column('vaxapp_countrystock', 'country', self.gf('django.db.models.fields.related.ForeignKey')(default='TK', to=orm['vaxapp.Country']), keep_default=False)

        # Deleting field 'CountryStock.country_iso_code'
        db.delete_column('vaxapp_countrystock', 'country_iso_code')


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
        'vaxapp.countrystock': {
            'Meta': {'object_name': 'CountryStock'},
            'country_iso_code': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vaccine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vaxapp.Vaccine']"})
        },
        'vaxapp.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'vaxapp.vaccine': {
            'Meta': {'object_name': 'Vaccine'},
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['vaxapp']
