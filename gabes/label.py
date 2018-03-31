import os
import base64


class Label(object):
    """The :class:`Label` object, which contains the label
    that will represent either the boolean *False* or *True* for a particular gate.
    """
    def __init__(self, represents, gate=None, size=32):
        self.gate  = gate
        self.label = self.generate_label(size)
        self.represents = represents

    def __repr__(self):
        return str(self.label)

    def __str__(self):
        return str(self.label)

    @staticmethod
    def generate_label(size):
        return base64.urlsafe_b64encode(os.urandom(size))
