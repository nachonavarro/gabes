import gabes.settings as settings
import random

from gabes.utils import xor, get_last_bit
from gabes.label import Label

class Wire(object):
    """The :class:`Wire` object holds two labels representing
    *True* and *False*.
    """
    def __init__(self, identifier=None):
        self.identifier  = identifier
        if settings.CLASSICAL:
            self.false_label = Label(False)
            self.true_label  = Label(True)
        else:
            b = random.choice([True, False])
            self.false_label = Label(False, pp_bit=b)
            self.true_label  = Label(True, pp_bit=not b)
        if settings.FREE_XOR or settings.HALF_GATES:
            self.true_label.label = xor(self.false_label.label, settings.R)

    def __str__(self):
        if self.identifier:
            return "Wire {}".format(self.identifier)
        else:
            return "Unidentified Wire"

    def labels(self):
        for label in (self.false_label, self.true_label):
            yield label

    def get_label(self, representing):
        return self.true_label if representing else self.false_label