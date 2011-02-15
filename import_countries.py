#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import json
from vaxapp.models import Country

# cribbed from http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-unicode-ones-from-json-in-python/1641528#1641528
def _parseJSON(obj):
        newobj = {}

        for key, value in obj.iteritems():
                key = str(key)

                if isinstance(value, dict):
                        newobj[key] = _parseJSON(value)
                elif isinstance(value, list):
                        if key not in newobj:
                                newobj[key] = []
                                for i in value:
                                        newobj[key].append(_parseJSON(i))
                elif isinstance(value, unicode):
                        val = str(value)
                        if val.isdigit():
                                val = int(val)
                        else:
                                try:
                                        val = float(val)
                                except ValueError:
                                        val = str(val)
                        newobj[key] = val

        return newobj

def go():
    # load json file
    world = json.load(open('vaxapp/world.json'))
    # next line necessary on my mac at home, but not ubuntu machine at work...
    world = [_parseJSON(w) for w in world]
    for w in world:
        # create Country objects
        try:
            Country.objects.create(**w)
        except Exception, e:
            print e
            print w
