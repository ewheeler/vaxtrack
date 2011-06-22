#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import json
import datetime
import datetime
from uuid import uuid4

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import send_mass_mail

import boto

from celery.decorators import periodic_task
from celery.decorators import task
from celery.task import PeriodicTask

from vaxapp.models import Document
from vaxapp.models import Alert
import import_xls

"""
$ rabbitmqctl add_user myuser mypassword

$ rabbitmqctl add_vhost myvhost

$ rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
"""

#sudo ./manage.py celeryd -v 2 -B -s celery -E -l INFO

REQUEST_QUEUE = getattr(settings, "CHART_REQUEST_QUEUE", "chart_requests")
RESPONSE_QUEUE = getattr(settings, "CHART_RESPONSE_QUEUE", "chart_responses")
ACL = getattr(settings, "CHART_AWS_ACL", "public-read")
AMI_ID = getattr(settings, "CHART_AMI_ID", "ami-1641b47f")
KEYPAIR = getattr(settings, "CHART_KEYPAIR_NAME", None)
MAX_INSTANCES = getattr(settings, 'CHART_MAX_NODES', 20)
SECURITY_GROUPS = getattr(settings, 'CHART_SECURITY_GROUPS', None)


def queue_json_message(doc, doc_key):
    key_name = doc_key.name.replace(os.path.basename(doc_key.name), "message-%s.json" % str(uuid4()))
    key = doc_key.bucket.new_key(key_name)
    message_data = json.dumps({'bucket': doc_key.bucket.name, 'key': doc_key.name, 'uuid': doc.uuid})
    key.set_contents_from_string(message_data)
    msg_body = {'bucket': key.bucket.name, 'key': key.name}
    queue = boto.connect_sqs().create_queue(REQUEST_QUEUE)
    msg = queue.new_message(body=json.dumps(msg_body))
    queue.write(msg)


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

    queue_json_message(doc, key)
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

