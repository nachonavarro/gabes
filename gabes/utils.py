"""
    This module includes utility functions used throughout the package.
"""

import gabes.settings as settings
import os


def ask_for_inputs(identifiers):
    """
        CLI helper function that queries the user to indicate which
        identifier he supplies and the his choice for each identifier.

        :param list(str) identifiers: the identifiers of the input wires
        :return: the identifiers the user supplies
        :rtype: dict

    """
    print('To start the protocol please indicate with y/n '
          'which wires you supply:')
    chosen_wires = []
    for identifier in identifiers:
        decision = input("Do you supply {}? ".format(identifier))
        while True:
            if decision == 'y':
                chosen_wires.append(identifier)
                break
            elif decision == 'n':
                break
            else:
                decision = input("Sorry, didn't recognize that. \
                                  Indicate with y or n whether \
                                  you supply {}: ".format(identifier))

    inputs = {}
    for identifier in chosen_wires:
        label_choice = input("Choice for {}: ".format(identifier))
        while True:
            if label_choice in '01':
                break
            else:
                label_choice = input("Sorry, you must supply either a 0 \
                                      (indicating false) or a 1 \
                                      (indicating true) for \
                                      wire {}: ".format(identifier))

        inputs[identifier] = label_choice

    return inputs


def get_last_bit(label):
    """
        Gets the last bit from a bytestring.

        :param bytes label: any bytes object
        :return: the last bit
        :rtype: bool

        .. code-block:: python

            >>> import os
            >>> from gabes.utils import get_last_bit
            >>> b1 = os.urandom(10)
            >>> b1
            b'\\xf3\\x9e\\xb0w,|\\xd9\\xa8\\xd73'
            >>> get_last_bit(b1)
            False

    """
    last_byte = label[-1]
    return bool((last_byte >> 7) & 1)


def xor(b1, b2):
    """
        XORs two bytestrings.

        :param bytes b1: first argument
        :param bytes b2: second argument
        :return: the XORed result
        :rtype: bytes

        .. code-block:: python

            >>> import os
            >>> from gabes.utils import get_last_bit
            >>> b1 = os.urandom(10)
            >>> b2 = os.urandom(10)
            >>> b1, b2
            (b'\\xf8\\x00r\\xaf\\x9a\\x06!68\\x83', b'\\x88
            \\xee\\x1c,a\\xd0^\\x8a\\xb4\\xf2')
            >>> xor(b1, b2)
            b'p\\xeen\\x83\\xfb\\xd6\\x7f\\xbc\\x8cq'
            >>> xor(b1, xor(b1, b2)) == b2
            True

    """
    n1 = int.from_bytes(b1, byteorder='big')
    n2 = int.from_bytes(b2, byteorder='big')
    xored = n1 ^ n2
    return int.to_bytes(xored, length=settings.NUM_BYTES, byteorder='big')


def adjust_wire_offset(wire):
    """
        Adjusts the wire's offset so that the two labels have a
        distinct last bit.

        :param wire: the wire in question

    """
    false_label = get_last_bit(wire.false_label.label)
    true_label = get_last_bit(wire.true_label.label)
    while false_label == true_label:
        wire.true_label.label = os.urandom(settings.NUM_BYTES)
        true_label = get_last_bit(wire.true_label.label)
