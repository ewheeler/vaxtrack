#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import json
from vaxapp.models import Country

def go():
    # load json file
    world = json.load(open('vaxapp/world.json'))
    for w in world:
        # create Country objects
        try:
            Country.objects.create(**w)
        except Exception, e:
            print e
            print w
