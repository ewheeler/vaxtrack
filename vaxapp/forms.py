#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from .models import Country
from .models import UserProfile


class CountryForm(forms.Form):
    uploader = forms.CharField(
        label="Your name",
        max_length=160)

    country_csv = forms.FileField(
        label="Country stock data CSV file",
        required=False,
        help_text="Upload a <em>csv file</em> " +
                  "containing country stock data.")

class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label="First name",
        max_length=30)

    last_name = forms.CharField(
        label="Last name",
        max_length=30)

    username = forms.CharField(
        label="Username",
        max_length=30)

    password1 = forms.CharField(
        label="password",
        widget=forms.PasswordInput())

    password2 = forms.CharField(
        label="re-enter password",
        widget=forms.PasswordInput())

    email = forms.EmailField(
        label="Your email address")

    country = forms.ChoiceField(
        label="Your country",
        choices=Country.as_tuples())

    group = forms.ChoiceField(
        label="Your group or organization",
        choices = [(g.pk, unicode(g)) for g in Group.objects.all()])

    def save(self):
        data = self.cleaned_data
        # create_user only accepts three parameters...
        user = User.objects.create_user(data['username'],
            data['email'], data['password1'])

        # so add the remaining attributes
        user.first_name=data['first_name']
        user.last_name=data['last_name']

        # and add group
        user.groups.add(data['group'])
        # TODO only allow UNICEF SD and WHO HQ
        # members to access admin site
        user.is_staff = True
        user.save()

        # create UserProfile with additional attributes
        user_profile = UserProfile.objects.create(user=user,
            country = data['country'])
        user_profile.save()
