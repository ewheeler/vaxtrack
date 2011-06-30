#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import authority
from authority import permissions
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from .models import Country

class CountryPermission(permissions.BasePermission):
    label = 'country_permission'
    checks = ('has_country_affiliation',)

    def has_country_affiliation(self, user, country):
        # allow staff and superusers to see all countries
        if user.is_staff() or user.is_superuser():
            return True
        try:
            profile = user.get_profile()
            if profile.country:
                # if the user declared affiliation with a country
                # during registration, allow them to view it
                if(profile.country == country):
                    return True
        except ObjectDoesNotExist:
            pass
        return False

authority.register(Country, CountryPermission)
