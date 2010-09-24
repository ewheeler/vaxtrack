#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime

from pylab import figure, axes, pie, title
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.db.models import Sum

from models import *

def index(req):
    return render_to_response("index.html")

def chart_country(req, country_pk=None):
    f = figure(figsize=(6,6))
    ax = axes([0.1, 0.1, 0.8, 0.8])
    labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
    fracs = [15,30,45, 10]
    explode=(0, 0.05, 0, 0)
    pie(fracs, explode=explode, labels=labels, autopct='%1.1f%%')
    title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})

    canvas = FigureCanvasAgg(f)    
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    matplotlib.pyplot.close(f)

    save_charts = False
    if save_charts:
        filename = "%s-%s.png" % (datetime.datetime.today().date().isoformat(), country_pk)
        file_path = "vaxapp/static/charts/" + filename
        f.savefig(file_path)

    return response
