import re

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


def cif_get_checksum(number):
    s1 = sum([int(digit) for pos, digit in enumerate(number) if int(pos) % 2])
    s2 = sum([sum([int(unit) for unit in str(int(digit) * 2)])
             for pos, digit in enumerate(number) if not int(pos) % 2])
    return (10 - ((s1 + s2) % 10)) % 10


class ESIdentityCardNumberValidator(object):
    """
    Spanish NIF/NIE/CIF (Fiscal Identification Number) code.

    Validates three different formats:

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
    error_messages = {
        'invalid': _('Please enter a valid NIF, NIE, or CIF.'),
        'invalid_only_nif': _('Please enter a valid NIF or NIE.'),
        'invalid_nif': _('Invalid checksum for NIF.'),
        'invalid_nie': _('Invalid checksum for NIE.'),
        'invalid_cif': _('Invalid checksum for CIF.'),
    }

    def __init__(self, only_nif=False, max_length=None, min_length=None, *args, **kwargs):
        self.only_nif = only_nif
        self.nif_control = 'TRWAGMYFPDXBNJZSQVHLCKE'
        self.cif_control = 'JABCDEFGHI'
        self.cif_types = 'ABCDEFGHJKLMNPQS'
        self.nie_types = 'XYZ'

    def __call__(self, value):
        nif_get_checksum = lambda d: self.nif_control[int(d) % 23]
        m = re.match(r'^([%s]?)(\d+)([%s]?)$' % (self.cif_types + self.nie_types, self.nif_control + self.cif_control), value)
        if m is None:
            raise ValidationError(self.error_messages['invalid'])
        letter1, number, letter2 = m.groups()
        if not letter1 and letter2:
            # NIF
            if letter2 == nif_get_checksum(number):
                return
            else:
                raise ValidationError(self.error_messages['invalid_nif'])
        elif letter1 in self.nie_types and letter2:
            # NIE
            l2n = letter1.replace('X', '0').replace('Y', '1').replace('Z', '2')
            number2b_checked = l2n + number
            if letter2 == nif_get_checksum(number2b_checked):
                return
            else:
                raise ValidationError(self.error_messages['invalid_nie'])
        elif not self.only_nif and letter1 in self.cif_types and len(number) in [7, 8]:
            # CIF
            if not letter2:
                number, letter2 = number[:-1], int(number[-1])
            checksum = cif_get_checksum(number)
            if letter2 in (checksum, self.cif_control[checksum]):
                return
            else:
                raise ValidationError(self.error_messages['invalid_cif'])
        else:
            raise ValidationError(self.error_messages['invalid'])
