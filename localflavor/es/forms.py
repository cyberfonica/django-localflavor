# -*- coding: utf-8 -*-
"""
Spanish-specific Form helpers
"""

from __future__ import absolute_import, unicode_literals

import re

from django.core.validators import EMPTY_VALUES
from django.forms import ValidationError
from django.forms.fields import RegexField, Select, CharField
from django.utils.translation import ugettext_lazy as _

from .es_provinces import PROVINCE_CHOICES
from .es_regions import REGION_CHOICES
from .validators import ESIdentityCardNumberValidator


class ESPostalCodeField(RegexField):
    """
    A form field that validates its input as a spanish postal code.

    Spanish postal code is a five digits string, with two first digits
    between 01 and 52, assigned to provinces code.
    """
    default_error_messages = {
        'invalid': _('Enter a valid postal code in the range and format 01XXX - 52XXX.'),
    }

    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ESPostalCodeField, self).__init__(
            r'^(0[1-9]|[1-4][0-9]|5[0-2])\d{3}$',
            max_length, min_length, *args, **kwargs)


class ESPhoneNumberField(RegexField):
    """
    A form field that validates its input as a Spanish phone number.
    Information numbers are ommited.

    Spanish phone numbers are nine digit numbers, where first digit is 6 (for
    cell phones), 8 (for special phones), or 9 (for landlines and special
    phones)

    TODO: accept and strip characters like dot, hyphen... in phone number
    """
    default_error_messages = {
        'invalid': _('Enter a valid phone number in one of the formats 6XXXXXXXX, 8XXXXXXXX or 9XXXXXXXX.'),
    }

    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ESPhoneNumberField, self).__init__(r'^(6|7|8|9)\d{8}$',
                                                 max_length, min_length, *args, **kwargs)


class ESIdentityCardNumberField(CharField):
    """
    Spanish NIF/NIE/CIF (Fiscal Identification Number) code.

    Validates three diferent formats:

        NIF (individuals): 12345678A
        CIF (companies): A12345678
        NIE (foreigners): X12345678A

    according to a couple of simple checksum algorithms.

    Value can include a space or hyphen separator between number and letters.
    Number length is not checked for NIF (or NIE), old values start with a 1,
    and future values can contain digits greater than 8. The CIF control digit
    can be a number or a letter depending on company type. Algorithm is not
    public, and different authors have different opinions on which ones allows
    letters, so both validations are assumed true for all types.
    """
    default_error_messages = {
        'invalid': _('Please enter a valid NIF, NIE, or CIF.'),
        'invalid_only_nif': _('Please enter a valid NIF or NIE.'),
        'invalid_nif': _('Invalid checksum for NIF.'),
        'invalid_nie': _('Invalid checksum for NIE.'),
        'invalid_cif': _('Invalid checksum for CIF.'),
    }

    # validators = [ESIdentityCardNumberValidator()]
    # default_validators =
    def __init__(self, only_nif=False, max_length=None, min_length=None, *args, **kwargs):
        self.only_nif = only_nif
        self.nif_control = 'TRWAGMYFPDXBNJZSQVHLCKE'
        self.cif_control = 'JABCDEFGHI'
        self.cif_types = 'ABCDEFGHJKLMNPQS'
        self.nie_types = 'XYZ'
        super(ESIdentityCardNumberField, self).__init__(
            max_length, min_length, validators=[ESIdentityCardNumberValidator()], *args, **kwargs)

    def clean(self, value):
        if value not in EMPTY_VALUES:
            value = value.upper().replace(' ', '').replace('-', '')
        return super(ESIdentityCardNumberField, self).clean(value)


class ESCCCField(RegexField):
    """
    A form field that validates its input as a Spanish bank account or CCC
    (Codigo Cuenta Cliente).

        Spanish CCC is in format EEEE-OOOO-CC-AAAAAAAAAA where:

            E = entity
            O = office
            C = checksum
            A = account

        It's also valid to use a space as delimiter, or to use no delimiter.

        First checksum digit validates entity and office, and last one
        validates account. Validation is done multiplying every digit of 10
        digit value (with leading 0 if necessary) by number in its position in
        string 1, 2, 4, 8, 5, 10, 9, 7, 3, 6. Sum resulting numbers and extract
        it from 11.  Result is checksum except when 10 then is 1, or when 11
        then is 0.

        TODO: allow IBAN validation too
    """
    default_error_messages = {
        'invalid': _('Please enter a valid bank account number in format XXXX-XXXX-XX-XXXXXXXXXX.'),
        'checksum': _('Invalid checksum for bank account number.'),
    }

    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ESCCCField, self).__init__(r'^\d{4}[ -]?\d{4}[ -]?\d{2}[ -]?\d{10}$',
                                         max_length, min_length, *args, **kwargs)

    def clean(self, value):
        super(ESCCCField, self).clean(value)
        if value in EMPTY_VALUES:
            return ''
        control_str = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6]
        m = re.match(r'^(\d{4})[ -]?(\d{4})[ -]?(\d{2})[ -]?(\d{10})$', value)
        entity, office, checksum, account = m.groups()
        get_checksum = lambda d: str(11 - sum([int(digit) * int(control) for digit, control in zip(d, control_str)]) % 11).replace('10', '1').replace('11', '0')
        if get_checksum('00' + entity + office) + get_checksum(account) == checksum:
            return value
        else:
            raise ValidationError(self.error_messages['checksum'])


class ESRegionSelect(Select):
    """
    A Select widget that uses a list of spanish regions as its choices.
    """
    def __init__(self, attrs=None):
        super(ESRegionSelect, self).__init__(attrs, choices=REGION_CHOICES)


class ESProvinceSelect(Select):
    """
    A Select widget that uses a list of spanish provinces as its choices.
    """
    def __init__(self, attrs=None):
        super(ESProvinceSelect, self).__init__(attrs, choices=PROVINCE_CHOICES)
