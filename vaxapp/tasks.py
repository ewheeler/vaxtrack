#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
from datetime import datetime
from datetime import timedelta

from django.conf import settings

import boto
from celery.decorators import task

from vaxapp.models import Document

#sudo ./manage.py celeryd -v 2 -B -s celery -E -l INFO

ACL = getattr(settings, "CHART_AWS_ACL", "public-read")


def upload_file_to_s3(doc):
    file_path = doc.local_document.path
    b = boto.connect_s3().get_bucket(settings.CSV_UPLOAD_BUCKET)
    name = '%s/%s' % (doc.uuid, os.path.basename(file_path))
    k = b.new_key(name)
    k.set_contents_from_filename(file_path)
    k.set_acl(ACL)
    return k


@task
def process_file(doc):
    """Transfer uploaded file to S3 and queue up message to process PDF."""
    key = upload_file_to_s3(doc)
    doc.remote_document = "http://%s.s3.amazonaws.com/%s" % (key.bucket.name, key.name)
    doc.date_stored = datetime.utcnow()
    doc.status = 'S'
    doc.save()

    doc.status = 'Q'
    doc.date_queued = datetime.utcnow()
    doc.save()

    return True

