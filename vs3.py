#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import os
import json

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

