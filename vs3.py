#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import boto

def upload_file(local_file, bucket, key, public=False):
    b = boto.connect_s3().get_bucket(bucket)
    k = b.new_key(key)
    k.set_contents_from_filename(local_file)
    if public:
        k.set_acl('public-read')

