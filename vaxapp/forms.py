#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import forms


class CountryForm(forms.Form):
    uploader = forms.CharField(
        label="Your name",
        max_length=160)

    country_csv = forms.FileField(
        label="Country stock data CSV file",
        required=False,
        help_text="Upload a <em>csv file</em> " +
                  "containing country stock data.")
