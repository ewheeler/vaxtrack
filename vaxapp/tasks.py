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
        # TODO XXX dry run for now!
        print 'IMPORT TEMPLATE'
        doc.date_process_start = datetime.datetime.utcnow()
        doc.status = 'P'
        doc.save()
        if import_xls.import_template(doc.local_document.path, interactive=False, dry_run=True, upload=doc.uuid):
            doc.date_process_end = datetime.datetime.utcnow()
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
def handle_alert(countrystock, ref_date, status, risk, text, dry_run=False):
    alert, created = Alert.objects.get_or_create(countrystock=countrystock,\
        reference_date=ref_date, status=status, risk=risk, text=text)
    alert.analyzed = datetime.datetime.now()
    alert.save()
    if created:
        # only send emails if this is a new alert
        recipients = []
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
        recipients = recipients + [s.email for s in staff]
        subject = "[VisualVaccines] %s: %s %s" % (alert.countrystock, alert.status, alert.risk)
        body = alert.text
        sender = 'visualvaccines@gmail.com'
        if all([subject, body, recipients]):
            mail_tuples = []
            for r in recipeints:
                mail_tuples.append((subject, body, sender, [r]))
            if not dry_run:
                send_mass_mail(tuple(mail_tuples), fail_silently=False)
            else:
                for m in mail_tuples:
                    print 'pretend send: ', m
        else:
            print 'failed to construct alert emails'

