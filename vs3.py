#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import simplejson

from datetime import datetime, timedelta
from uuid import uuid4

from django.conf import settings

from celery.decorators import task
from celery.task import PeriodicTask

from vaxapp.models import *
import boto

# constants and methods for use by temporary instances

request_queue = boto.connect_sqs().create_queue('chart_request_queue')
response_queue = boto.connect_sqs().create_queue('chart_response_queue')
count = 0

def read_json_pointer_message():
    m = request_queue.read(3600) # Give the job an hour to run, plenty of time to avoid double-runs
    if m is not None:
        pointer = json.loads(m.get_body())
        k = boto.connect_s3().get_bucket(pointer['bucket']).get_key(pointer['key'])
        data = json.loads(k.get_contents_as_string())
        data['pointer'] = m
        return data

def delete_json_pointer_message(data):
    request_queue.delete_message(data['pointer'])

def write_json_pointer_message(data, bucket, key_name, base_key):
    b = boto.connect_s3().get_bucket(bucket)
    k = b.new_key(base_key.replace(os.path.basename(base_key), key_name))
    k.set_contents_from_string(json.dumps(data))
    response_message = {'bucket': b.name, 'key': k.name}
    message = response_queue.new_message(body=json.dumps(response_message))
    response_queue.write(message)

def download(bucket, key, local_file):
    b = boto.connect_s3().get_bucket(bucket)
    k = b.get_key(key)
    k.get_contents_to_filename(local_file)

def upload_file(local_file, bucket, key, public=False):
    b = boto.connect_s3().get_bucket(bucket)
    k = b.new_key(key)
    k.set_contents_from_filename(local_file)
    if public:
        k.set_acl('public-read')

# constants and methods for use by persistant instance
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
    message_data = simplejson.dumps({'bucket': doc_key.bucket.name, 'key': doc_key.name, 'uuid': doc.uuid})
    key.set_contents_from_string(message_data)
    msg_body = {'bucket': key.bucket.name, 'key': key.name}
    queue = boto.connect_sqs(settings.CHART_AWS_KEY, settings.CHART_AWS_SECRET).create_queue(REQUEST_QUEUE)
    msg = queue.new_message(body=simplejson.dumps(msg_body))
    queue.write(msg)


def upload_file_to_s3(doc):
    file_path = doc.local_document.path
    b = boto.connect_s3(settings.CHART_AWS_KEY, settings.CHART_AWS_SECRET).get_bucket(settings.CHART_UPLOAD_BUCKET)
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

    queue_json_message(doc, key)
    doc.status = 'Q'
    doc.date_queued = datetime.utcnow()
    doc.save()

    return True


class CheckResponseQueueTask(PeriodicTask):
    """
    Checks response queue for messages returned from running processes in the
    cloud.  The messages are read and corresponding `pdf.models.Document`
    records are updated.
    """
    run_every = timedelta(seconds=30)

    def _dequeue_json_message(self):
        sqs = boto.connect_sqs(settings.CHART_AWS_KEY, settings.CHART_AWS_SECRET)
        queue = sqs.create_queue(RESPONSE_QUEUE)
        msg = queue.read()
        if msg is not None:
            data = simplejson.loads(msg.get_body())
            bucket = data.get('bucket', None)
            key = data.get("key", None)
            queue.delete_message(msg)
            if bucket is not None and key is not None:
                return data

    def run(self, **kwargs):
        logger = self.get_logger(**kwargs)
        logger.info("Running periodic task!")
        data = self._dequeue_json_message()
        if data is not None:
            Document.process_response(data)
            return True
        return False


class CheckQueueLevelsTask(PeriodicTask):
    """
    Checks the number of messages in the queue and compares it with the number
    of instances running, only booting nodes if the number of queued messages
    exceed the number of nodes running.
    """
    run_every = timedelta(seconds=60)

    def run(self, **kwargs):
        ec2 = boto.connect_ec2(settings.CHART_AWS_KEY, settings.CHART_AWS_SECRET)
        sqs = boto.connect_sqs(settings.CHART_AWS_KEY, settings.CHART_AWS_SECRET)

        queue = sqs.create_queue(REQUEST_QUEUE)
        num = queue.count()
        launched = 0
        icount = 0

        reservations = ec2.get_all_instances()
        for reservation in reservations:
            for instance in reservation.instances:
                if instance.state == "running" and instance.image_id == AMI_ID:
                    icount += 1
        to_boot = min(num - icount, MAX_INSTANCES)

        if to_boot > 0:
            startup = BOOTSTRAP_SCRIPT % {
                'KEY': settings.CHART_AWS_KEY,
                'SECRET': settings.CHART_AWS_SECRET,
                'RESPONSE_QUEUE': RESPONSE_QUEUE,
                'REQUEST_QUEUE': REQUEST_QUEUE}
            r = ec2.run_instances(
                image_id=AMI_ID,
                min_count=to_boot,
                max_count=to_boot,
                key_name=KEYPAIR,
                security_groups=SECURITY_GROUPS,
                user_data=startup)
            launched = len(r.instances)
        return launched
