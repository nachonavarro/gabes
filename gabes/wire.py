"""
This module implements the :class:`Wire` object. Each gate will have
a left wire (in the case of input gates, this will be probably be supplied
by the garbler), a right wire (evaluator), and an output wire. Each
wire holds the two possible for labels that run through it.
"""

import random
import gabes.settings as settings

from gabes.utils import xor
from gabes.label import Label


class Wire(object):
    """
        The :class:`Wire` object holds two labels representing
        *True* and *False*. In classical garbled circuits,
        there is no need for a point-and-permute bit. In all the other
        cases, a pp_bit is associated to each label. The two labels
        in the same wire must have opposing pp_bits.

        If the optimization chosen is FreeXOR or Half Gates then
        the true label is the false label xored with the global
        parameter `R` defined in :class:`gabes.circuit.Circuit`

        :param str identifier: (optional) wire's unique identifier

        .. code-block:: python

               >>> from gabes.wire import Wire
               >>> w = Wire(identifier='A')
               >>> str(w)
               'Wire A'
               >>> w.false_label
               b'dnE2Gsvhx84HgwrLRm8L9aFtI_aBYxzEDaOBRK2qkP0='
               >>> w.true_label
               b'eBRWiJzYL65gU8nBFvXRZ8NK4_Cf9GlrYtNGZNEZOSs='
               >>> w.get_label(True) == w.true_label.represents
               True
    """
    def __init__(self, identifier=None):
        self.identifier = identifier
        if settings.CLASSICAL:
            self.false_label = Label(False)
            self.true_label = Label(True)
        else:
            b = random.choice([True, False])
            self.false_label = Label(False, pp_bit=b)
            self.true_label = Label(True, pp_bit=not b)
        if settings.FREE_XOR or settings.HALF_GATES:
            self.true_label.label = xor(self.false_label.label, settings.R)

    def __str__(self):
        if self.identifier:
            return "Wire {}".format(self.identifier)
        else:
            return "Unidentified Wire"

    def labels(self):
        """
            A getter method to get the two labels (*False* and *True*)
            going through the wire.

            :return: a tuple of labels
            :rtype: Generator[:class:`Wire`]

        """
        for label in (self.false_label, self.true_label):
            yield label

    def get_label(self, representing):
        """
            Gets the label according to which truth value it represents.

            :param bool representing: *True* for the true label and *False* \
            for the false label
            :return: the corresponding label
            :rtype: :class:`Label`
        """
        return self.true_label if representing else self.false_label
