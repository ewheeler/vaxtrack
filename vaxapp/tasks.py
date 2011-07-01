#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import send_mass_mail
from django.core.exceptions import ObjectDoesNotExist

import boto
from celery.decorators import task

from vaxapp.models import Document
from vaxapp.models import Alert
from vaxapp.analysis import *
import import_xls

"""
$ rabbitmqctl add_user myuser mypassword

$ rabbitmqctl add_vhost myvhost

$ rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
"""

#sudo ./manage.py celeryd -v 2 -B -s celery -E -l INFO

ACL = getattr(settings, "CHART_AWS_ACL", "public-read")


def upload_file_to_s3(doc):
    file_path = doc.local_document.path
    b = boto.connect_s3().get_bucket(settings.DOCUMENT_UPLOAD_BUCKET)
    name = '%s/%s' % (doc.uuid, os.path.basename(file_path))
    k = b.new_key(name)
    k.set_contents_from_filename(file_path)
    k.set_acl(ACL)
    return k

@task
def process_revert_upload(doc, reverter):
    sdb_revert_upload(doc.uuid)
    doc.date_revert_start = datetime.datetime.utcnow()
    doc.reverted_by = reverter
    doc.status = 'P'
    doc.save()
    country_pks = (c.iso2_code for c in doc.imported_countries.all())
    print country_pks
    group_slugs = (g.slug for g in doc.imported_groups.all())
    print group_slugs
    years = doc.imported_years.split(',')
    print years
    last_date = doc.date_data_end
    print last_date
    print plot_and_analyze(sit_year=last_date.year, sit_month=last_date.month, sit_day=last_date.day, country_pks=country_pks, group_slugs=group_slugs)
    print plot_historical(country_pks, group_slugs, years)
    doc.date_revert_end = datetime.datetime.utcnow()
    doc.status = 'R'
    doc.save()
    return True

def notify_upload_complete(doc):
    uploader_email = doc.user.email
    if all([doc.user.first_name, doc.user.last_name]):
        uploader_name = "%s %s" % (doc.user.first_name, doc.user.last_name)
    else:
        uploader_name = doc.user.username
    sender = 'visualvaccines@gmail.com'
    subject = "[VisualVaccines] upload analysis complete"
    body =\
"""
Hello %s,

The analysis of your recently uploaded document is complete.
Please visit http://visualvaccines.com to review any relevant charts,
which now include data from your uploaded document.

Thanks,
VisualVaccines
""" % (uploader_name)

    mail_tuples = []
    mail_tuples.append((subject, body, sender, [uploader_email]))
    mail_tuples.append((subject, body, sender, ['evanmwheeler@gmail.com']))
    send_mass_mail(tuple(mail_tuples), fail_silently=False)

@task
def process_file(doc):
    """Transfer uploaded file to S3 and queue up message to process"""
    key = upload_file_to_s3(doc)
    doc.remote_document = "http://%s.s3.amazonaws.com/%s" % (key.bucket.name, key.name)
    doc.date_stored = datetime.datetime.utcnow()
    doc.status = 'S'
    doc.save()

    doc.status = 'Q'
    doc.date_queued = datetime.datetime.utcnow()
    doc.save()

    if doc.document_format in ['UNSDATV', 'UNSDCOF', 'UNSDACOF', 'UNSDCFD']:
        # TODO XXX dry run for now!
        print 'IMPORT UNICEF'
        doc.date_process_start = datetime.datetime.utcnow()
        doc.status = 'P'
        doc.save()
        if import_xls.import_unicef(doc.local_document.path, interactive=False, dry_run=True, upload=doc.uuid):
            doc.date_process_end = datetime.datetime.utcnow()
            doc.status = 'F'
            doc.save()
            notify_upload_complete(doc)
            return True
    elif doc.document_format in ['WHOCS']:
        # TODO XXX dry run for now!
        print 'IMPORT WHO'
        doc.date_process_start = datetime.datetime.utcnow()
        doc.status = 'P'
        doc.save()
        if import_xls.import_who(doc.local_document.path, interactive=False, dry_run=True, upload=doc.uuid):
            doc.date_process_end = datetime.datetime.utcnow()
            doc.status = 'F'
            doc.save()
            notify_upload_complete(doc)
            return True
    elif doc.document_format in ['UNCOS', 'TMPLT']:
        print 'IMPORT TEMPLATE'
        doc.date_process_start = datetime.datetime.utcnow()
        doc.status = 'P'
        doc.save()
        import_report = import_xls.import_template(doc.local_document.path, interactive=False, dry_run=False, upload=doc.uuid)
        print import_report
        doc.date_process_end = datetime.datetime.utcnow()
        doc.save()
        doc.save_import_report(import_report)
        print 'import complete'
        last_date = doc.date_data_end
        print plot_and_analyze(sit_year=last_date.year, sit_month=last_date.month, sit_day=last_date.day, country_pks=import_report[0], group_slugs=import_report[1])
        print plot_historical(import_report[0], import_report[1], import_report[2])
        doc.status = 'F'
        doc.save()
        notify_upload_complete(doc)
        return True
    else:
        print 'IMPORT UNKNOWN'
        #TODO do something for TKs
        pass
    return True

@task
def handle_alert(countrystock, reference_date, status, risk, text, dry_run=False):
    print 'handling alert...'
    alert, created = Alert.objects.get_or_create(countrystock=countrystock,\
        reference_date=reference_date, status=status, risk=risk, text=text)
    alert.analyzed = datetime.datetime.now()
    alert.save()
    print 'alert created!'
    if 1:
        # only send emails if this is a new alert
        recipients = []
        '''
        # get all staff
        staff = User.objects.filter(is_staff=True)
        # find other users who list this country in their profile
        for u in User.objects.exclude(staff):
            try:
                profile = u.get_profile()
                if profile.country:
                    if profile.country == alert.countrystock.country:
                        recipients.append(u.email)
            except ObjectDoesNotExist:
                continue
        # combine staff and other users
        #recipients = recipients + [s.email for s in staff]
        '''
        recipients = ['evanmwheeler@gmail.com', 'anthonybellon.contact@gmail.com']
        subject = "[VisualVaccines] %s: %s %s" % (alert.countrystock, alert.get_status_display(), alert.get_risk_display())
        body = alert.get_text_display()
        sender = 'visualvaccines@gmail.com'
        if all([subject, body, recipients]):
            mail_tuples = []
            for r in recipients:
                mail_tuples.append((subject, body, sender, [r]))
            print mail_tuples
            if not dry_run:
                send_mass_mail(tuple(mail_tuples), fail_silently=False)
            else:
                for m in mail_tuples:
                    print 'pretend send: ', m
        else:
            print 'failed to construct alert emails'

