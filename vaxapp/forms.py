#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import os
import datetime
import operator

from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from .models import Country
from .models import Document
from .models import UserProfile
from .models import VaccineGroup
from .models import Vaccine

class DocumentValidationError(forms.ValidationError):
    def __init__(self):
        msg = _(u'Only .csv and .xls files are valid uploads.')
        super(DocumentValidationError, self).__init__(msg)


class DocumentField(forms.FileField):
    """A validating document upload field"""

    def clean(self, data, initial=None):
        f = super(DocumentField, self).clean(data, initial)
        ext = os.path.splitext(f.name)[1][1:].lower()
        extensions = ['csv', 'xls']
        content_types = ['text/csv', 'application/vnd.ms-excel']
        if ext in extensions and f.content_type in content_types:
            return f
        raise DocumentValidationError()

class DocumentForm(forms.ModelForm):
    local_document = DocumentField()

    class Meta:
        model = Document
        fields = ('name', 'local_document')

class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label=_("First name"),
        max_length=30)

    last_name = forms.CharField(
        label=_("Last name"),
        max_length=30)

    username = forms.CharField(
        label=_("Username"),
        max_length=30)

    password1 = forms.CharField(
        label=_("password"),
        widget=forms.PasswordInput())

    password2 = forms.CharField(
        label=_("re-enter password"),
        widget=forms.PasswordInput())

    email = forms.EmailField(
        label=_("Your email address"))

    country = forms.ChoiceField(
        label=_("Your country"),
        choices=Country.as_tuples())

    group = forms.ChoiceField(
        label=_("Your group or organization"),
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

class EntryForm(forms.Form):
    lang = translation.get_language()

    get_country_choices = operator.methodcaller("as_tuples_" + lang)
    country = forms.ChoiceField(
        label=_("Your country"),
        choices=get_country_choices(Country))

    affiliation = forms.ChoiceField(
        label=_("Your group or organization"),
        choices = [(g.pk, unicode(g)) for g in Group.objects.all()])

    group = forms.ChoiceField(
        label=_("Product group"),
        choices = [(g.pk, getattr(g, lang)) for g in VaccineGroup.objects.all()])

    product = forms.ChoiceField(
        label=_("Product"),
        choices = [(v.pk, getattr(v, lang)) for v in Vaccine.objects.all()])

    # SelectDateWidget's default is the next ten years.
    # Instead, provide +/- 5 years
    years = range(datetime.datetime.today().year - 5, datetime.datetime.today().year + 5)
    date = forms.DateField(label=_("Date of delivery or stock level observation"), widget=SelectDateWidget(years=years))

    amount_type = forms.ChoiceField(
        label=_("Amount type"),
        choices = [
            ('SL', _('Actual stock level')),
            ('UN', _('UNICEF delivery')),
            ('FF', _('UNICEF order (on forecast)')),
            ('FP', _('UNICEF order (on purchase)')),
            ('SI', _('Initial stock level from country office forecast')),
        ])

    amount = forms.IntegerField(label=_("Amount of product in doses"))

    def save(self):
        data = self.cleaned_data
        group = VaccineGroup.objects.get(pk=data['group'])
        data_date = data['date']
        amount_type = data['amount_type']
        affiliation = Group.objects.get(pk=data['affiliation'])
        country = Country.objects.get(iso2_code=data['country'])
        #product
        amount = data['amount']
