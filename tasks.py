#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from celery.task.schedules import crontab

from celery.decorators import periodic_task
from celery.decorators import task

@task
def add(x, y):
    return x + y

@task
def queue_new_data():
    pass

@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def test():
    print "firing test task"

#sudo ./manage.py celeryd -v 2 -B -s celery -E -l INFO
