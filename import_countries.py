#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import json
from vaxapp.models import Country

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
    # convert unicode to strings
    world = [_parseJSON(w) for w in world]
    for w in world:
        # create Country objects
        Country.objects.create(**w)
