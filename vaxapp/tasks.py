#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import send_mass_mail

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
        print import_xls.import_unicef(doc.local_document.path, interactive=False, dry_run=True)
        return True
    elif doc.document_format in ['WHOCS']:
        # TODO XXX dry run for now!
        print 'IMPORT WHO'
        print import_xls.import_who(doc.local_document.path, interactive=False, dry_run=True)
        return True
    elif doc.document_format in ['UNCOS', 'TMPLT']:
        print 'IMPORT TEMPLATE'
        #TODO import script for generic stock template!
        pass
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
        if not dry_run:
            # and this is not a dry run
            pass

