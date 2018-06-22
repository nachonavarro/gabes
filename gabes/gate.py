"""
This module implements the :class:`Gate` object. The bulk of **gabes**
resides on this module. In it, both garbling and ungarbling (or evaluating)
techniques are implemented.

"""

import os
import pickle
import gabes.settings as settings
import hashlib

from gabes.wire import Wire
from gabes.label import Label
from gabes.utils import get_last_bit, xor, adjust_wire_offset
from gabes.crypto import AESKey, generate_zero_ciphertext
from cryptography.fernet import Fernet, InvalidToken
from Crypto.Random.random import shuffle


class Gate(object):
    """
        The :class:`Gate` object contains three wires: a left wire,
        a right wire, and an output wire, each having a false label
        and a true label. Depending on the settings, different
        optimizations will be used to garble and ungarble.

        :param str gate_type: type of gate (AND, OR, etc)
        :param bool create_left: whether to create the left wire \
        on the gate's initialization
        :param bool create_right: whether to create the right wire \
        on the gate's initialization

    """

    gates = {
        'AND': lambda in1, in2: in1 & in2,
        'XOR': lambda in1, in2: in1 ^ in2,
        'OR': lambda in1, in2: in1 | in2
    }

    def __init__(self, gate_type, create_left=True, create_right=True):
        self.table = []
        self.gate_type = gate_type
        self.left_wire = Wire() if create_left else None
        self.right_wire = Wire() if create_right else None
        self.output_wire = Wire()

    def __str__(self):
        return self.gate_type

    def garble(self):
        """
            Garbles the gate. Delegates to the correct optimization
            depending on the user's choice.
        """
        if settings.CLASSICAL:
            self.classical_garble()
        elif settings.POINT_AND_PERMUTE:
            self.point_and_permute_garble()
        elif settings.FREE_XOR:
            self.free_xor_garble()
        elif settings.FLEXOR:
            self.flexor_garble()
        elif settings.GRR3:
            self.grr3_garble()
        elif settings.HALF_GATES:
            self.half_gates_garble()

    def classical_garble(self):
        """
            The most simple type of garbling. In classical garbled
            circuits, the whole boolean table is obfuscated by
            encrypting the output label using the input labels as keys.
            After this the table is shuffled (or *garbled*) so that
            the evaluator can't know more than one output label. For
            more information see `the paper
            <https://dl.acm.org/citation.cfm?id=1382944>`_.

            Note that a *Fernet* scheme is used since this method
            relies on knowing whether decryption was successful or not,
            as the evaluator needs to try and decrypt the four possible entries
            in the boolean table.
        """
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                key1 = Fernet(left_label.to_base64())
                key2 = Fernet(right_label.to_base64())
                in1, in2 = left_label.represents, right_label.represents
                logic_value = self.evaluate_gate(in1, in2)
                output_label = self.output_wire.get_label(logic_value)
                pickled = pickle.dumps(output_label)
                table_entry = key1.encrypt(key2.encrypt(pickled))
                self.table.append(table_entry)

        shuffle(self.table)

    def point_and_permute_garble(self):
        """
            In this optimization each label has a point-and-permute bit
            associated to it, with the only rule that labels running in the
            same wire must have opposing point-and-permute bits. The garbler
            will insert the encrypted output labels according to the
            point-and-permute bit of the input labels. Therefore, now the
            evaluator does not need to try and decrypt all the four
            ciphers but rather the one indicated by the two point-and-permute
            bits he has. For more information see `the paper
            <https://pdfs.semanticscholar.org/f71d/b4d70d4cc9e931a6\
            3dde7a6db8dad10a61a0.pdf>`_.
        """
        self.table = [None] * 4
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                key1 = AESKey(left_label.to_base64())
                key2 = AESKey(right_label.to_base64())
                in1, in2 = left_label.represents, right_label.represents
                logic_value = self.evaluate_gate(in1, in2)
                output_label = self.output_wire.get_label(logic_value)
                pickled = pickle.dumps(output_label)
                entry = key1.encrypt(key2.encrypt(pickled))
                self.table[2 * left_label.pp_bit + right_label.pp_bit] = entry

    def grr3_garble(self):
        """
            In this optimization the entry corresponding to the two labels that
            have a false point-and-permute bit is not sent over the network.
            Instead, the output label corresponding to this entry is
            set to be equal to the decryption of the zero ciphertext.
            Therefore, there is no need to send the entry because it is
            simply the zero ciphertext. The only thing the evaluator
            needs to do is to conclude that if he receives two false
            point-and-permute bits, the ciphertext will be the all zeros.
            For more information see `the paper
            <http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.2\
            4.6692&rep=rep1&type=pdf>`_.


            Note that now *Fernet* schemes can not be used since there is
            no way to decrypt the zero ciphertext. Instead, AES is used.
            See the Cryptography section for more details.
        """
        self.set_zero_ciphertext()
        self.table = [None] * 3
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                left_pp_bit = left_label.pp_bit
                right_pp_bit = right_label.pp_bit
                if left_pp_bit or right_pp_bit:
                    key1 = AESKey(left_label.to_base64())
                    key2 = AESKey(right_label.to_base64())
                    in1, in2 = left_label.represents, right_label.represents
                    logic_value = self.evaluate_gate(in1, in2)
                    output_label = self.output_wire.get_label(logic_value)
                    pickled = pickle.dumps(output_label)
                    entry = key1.encrypt(key2.encrypt(pickled), to_base64=True)
                    self.table[2 * left_pp_bit + right_pp_bit - 1] = entry

    def free_xor_garble(self):
        """
            In this optimization *XOR* gates are garbled for free, that is,
            the table corresponding to this gate is empty. The way this
            optimization accomplishes this is by setting the true label
            of each wire as an offset *R* of the false label. This offset
            is global to the whole circuit, so by the properties of *XOR*,
            everything works out nicely. For more information see `the paper
            <http://www.cs.toronto.edu/~vlad/papers/XOR_ICALP08.pdf>`_.

            Note that FreeXOR is not compatible with GRR2.
        """
        if self.gate_type == 'XOR':
            A0 = self.left_wire.false_label.label
            B0 = self.right_wire.false_label.label
            R = settings.R
            C0, C1 = xor(A0, B0), xor(xor(A0, B0), R)
            pp_bit = get_last_bit(C0)
            f_label = self.output_wire.false_label
            t_label = self.output_wire.true_label
            f_label.label = C0
            f_label.pp_bit = pp_bit
            t_label.label = C1
            t_label.pp_bit = not pp_bit
        else:
            if settings.GRR3:
                self.grr3_garble()
            else:
                self.point_and_permute_garble()

    def flexor_garble(self):
        """
            In this optimization *XOR* are garbled with a table size
            of 0, 1, or 2 (hence its name flexible XORs). The innovation
            at the time was that this method is compatible with GRR2.
            The way it accomplishes this is by changing the input wires'
            labels to have the same offset as the output wire's labels.
            For more information see `the paper
            <https://pdfs.semanticscholar.org/72ba/7c639e3d7b07\
            5fde8eeca3385923551c6a39.pdf>`_.
        """
        if self.gate_type == 'XOR':
            self.table = [None] * 4
            left, right, out = self.wires()
            adjust_wire_offset(out)
            A0, A1 = left.false_label.label, left.true_label.label
            B0, B1 = right.false_label.label, right.true_label.label
            C0, C1 = out.false_label.label, out.true_label.label
            R1, R2, R3 = xor(A0, A1), xor(B0, B1), xor(C0, C1)
            k1, k2 = AESKey(A0), AESKey(B0)
            A0_ = k1.decrypt(bytes(settings.NUM_BYTES))
            B0_ = k2.decrypt(bytes(settings.NUM_BYTES))
            C0_, C1_ = xor(A0_, B0_), xor(xor(A0_, B0_), R3)
            A1_, B1_ = xor(A0_, R3), xor(B0_, R3)
            self.modify_pp_bits(A0_, B0_, C0_)
            out.false_label.label = C0_
            out.true_label.label = C1_
            k1, k2 = AESKey(A1), AESKey(B1)
            if R1 == R2 == R3:
                self.free_xor_garble()
            elif R1 != R2 != R3:
                self.table[left.true_label.pp_bit] = k1.encrypt(A1_)
                self.table[right.true_label.pp_bit + 2] = k2.encrypt(B1_)
            elif R1 == R3:
                self.table[right.true_label.pp_bit + 2] = k2.encrypt(B1_)
            elif R2 == R3:
                self.table[left.true_label.pp_bit] = k1.encrypt(A1_)
        else:
            if settings.GRR3:
                self.grr3_garble()
            else:
                self.point_and_permute_garble()

    def half_gates_garble(self):
        """
            In this optimization, the most current one to date, the
            authors propose a method to garble *AND* gates with a table
            size of two ciphertexts in a way that is compatible with
            FreeXOR. The way they accomplish this is by breaking up
            an *AND* gate into two *half gates*. For more information
            see `the paper <https://eprint.iacr.org/2014/756.pdf>`_.
        """
        if self.gate_type == 'AND':
            def H(x):
                return hashlib.sha256(x).digest()
            self.table = [None] * 2
            p_a = self.left_wire.false_label.pp_bit
            p_b = self.right_wire.false_label.pp_bit

            # Generator Half Gate
            entry1 = xor(H(self.left_wire.false_label.label),
                         H(self.left_wire.true_label.label))
            if p_b:
                entry1 = xor(entry1, settings.R)
            C0 = H(self.left_wire.false_label.label)
            if p_a:
                C0 = xor(C0, entry1)

            # Evaluator Half Gate
            entry2 = xor(H(self.right_wire.false_label.label),
                         H(self.right_wire.true_label.label))
            entry2 = xor(entry2, self.left_wire.false_label.label)
            C0_ = H(self.right_wire.false_label.label)
            if p_b:
                C0_ = xor(C0_, xor(entry2, self.left_wire.false_label.label))

            self.table = [entry1, entry2]
            self.update_output_wire(xor(C0, C0_), xor(xor(C0, C0_), settings.R))
        else:
            self.free_xor_garble()

    def update_output_wire(self, false_label, true_label):
        """
            Updates the output wire's labels and point-and-permute bits.

            :param false_label: the false label
            :param true_label: the true label
        """
        self.output_wire.false_label.label = false_label
        self.output_wire.true_label.label = true_label
        self.output_wire.false_label.pp_bit = get_last_bit(false_label)
        self.output_wire.true_label.pp_bit = get_last_bit(true_label)

    def set_zero_ciphertext(self):
        """
            Generates the zero ciphertext by taking the two labels
            with false point-and-permute bits and setting the output labels
            accordingly. This function is used for GRR3.
        """
        l, r = self.left_wire, self.right_wire
        pp_left = l.false_label if not l.false_label.pp_bit else l.true_label
        pp_right = r.false_label if not r.false_label.pp_bit else r.true_label
        output_label = generate_zero_ciphertext(pp_left, pp_right)
        in1, in2 = pp_left.represents, pp_right.represents
        logic_value = self.evaluate_gate(in1, in2)
        true_label = self.output_wire.true_label
        false_label = self.output_wire.false_label
        if logic_value:
            true_label.label = output_label
            pp_bit = get_last_bit(output_label)
            true_label.pp_bit = pp_bit
            false_label.pp_bit = not pp_bit
        else:
            false_label.label = output_label
            pp_bit = get_last_bit(output_label)
            false_label.pp_bit = pp_bit
            true_label.pp_bit = not pp_bit

    def modify_pp_bits(self, A0_, B0_, C0_):
        """
            Modifies the point-and-permute bits according to the
            last bit of the label.
        """
        left, right, out = self.wires()
        l_pp_bit, r_pp_bit = get_last_bit(A0_), get_last_bit(B0_)
        out_pp_bit = get_last_bit(C0_)
        left.false_label.pp_bit = l_pp_bit
        left.true_label.pp_bit = not l_pp_bit
        right.false_label.pp_bit = r_pp_bit
        right.true_label.pp_bit = not r_pp_bit
        out.false_label.pp_bit = out_pp_bit
        out.true_label.pp_bit = not out_pp_bit

    def ungarble(self, garblers_label, evaluators_label):
        """
            Ungarbles the gate. Delegates to the correct optimization
            depending on the user's choice.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        g, e = garblers_label, evaluators_label
        if settings.CLASSICAL:
            output_label = self.classical_ungarble(g, e)
        elif settings.POINT_AND_PERMUTE:
            output_label = self.point_and_permute_ungarble(g, e)
        elif settings.FREE_XOR:
            output_label = self.free_xor_ungarble(g, e)
        elif settings.FLEXOR:
            output_label = self.flexor_ungarble(g, e)
        elif settings.GRR3:
            output_label = self.grr3_ungarble(g, e)
        elif settings.HALF_GATES:
            output_label = self.half_gates_ungarble(g, e)

        return output_label

    def classical_ungarble(self, garblers_label, evaluators_label):
        """
            The classical evaluation, in which the evaluator
            tries the four possible table entries until one of them
            decrypts the cipher.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        for table_entry in self.table:
            try:
                key1 = Fernet(garblers_label.to_base64())
                key2 = Fernet(evaluators_label.to_base64())
                output_label = pickle.loads(key2.decrypt(
                                            key1.decrypt(table_entry)))
            except InvalidToken:
                # Wrong table entry, try again
                pass
        return output_label

    def point_and_permute_ungarble(self, garblers_label, evaluators_label):
        """
            Evaluates the gate by indexing the table according to the
            point-and-permute bits given.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        left_pp_bit = garblers_label.pp_bit
        right_pp_bit = evaluators_label.pp_bit
        key1 = AESKey(garblers_label.to_base64())
        key2 = AESKey(evaluators_label.to_base64())
        table_entry = self.table[2 * left_pp_bit + right_pp_bit]
        output_label = pickle.loads(key2.decrypt(key1.decrypt(table_entry)))
        return output_label

    def grr3_ungarble(self, garblers_label, evaluators_label):
        """
            If the point-and-permute bits are false, then imagine
            the ciphertext was the all zero ciphertext. Otherwise,
            proceed as in the point-and-permute optimization.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        left_pp_bit = garblers_label.pp_bit
        right_pp_bit = evaluators_label.pp_bit
        key1 = AESKey(garblers_label.to_base64())
        key2 = AESKey(evaluators_label.to_base64())
        if not left_pp_bit and not right_pp_bit:
            zero_ciphertext = bytes(settings.NUM_BYTES)
            output_label = Label(0)
            output_label.represents = None
            output_label.label = key2.decrypt(key1.decrypt(zero_ciphertext,
                                                           unpad=False),
                                              unpad=False)
            output_label.pp_bit = get_last_bit(output_label.label)
        else:
            table_entry = self.table[2 * left_pp_bit + right_pp_bit - 1]
            output_label = pickle.loads(key2.decrypt(
                                        key1.decrypt(table_entry,
                                                     from_base64=True)))
        return output_label

    def free_xor_ungarble(self, garblers_label, evaluators_label):
        """
            Evaluates *XOR* gates for free by XORing the two
            labels he receives.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        if self.gate_type == 'XOR':
            output_label = Label(0)
            output_label.represents = None
            output_label.label = xor(garblers_label.label,
                                     evaluators_label.label)
            output_label.pp_bit = get_last_bit(output_label.label)
        else:
            g, e = garblers_label, evaluators_label
            if settings.GRR3:
                output_label = self.grr3_ungarble(g, e)
            else:
                output_label = self.point_and_permute_ungarble(g, e)
        return output_label

    def flexor_ungarble(self, garblers_label, evaluators_label):
        """
            Transforms the two input labels to have the same offset
            as the output's true label.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        if self.gate_type == 'XOR':
            garblers_label = self.transform_label(garblers_label,
                                                  garbler=True)
            evaluators_label = self.transform_label(evaluators_label,
                                                    garbler=False)
            output_label = self.free_xor_ungarble(garblers_label,
                                                  evaluators_label)
        else:
            g, e = garblers_label, evaluators_label
            if settings.GRR3:
                output_label = self.grr3_ungarble(g, e)
            else:
                output_label = self.point_and_permute_ungarble(g, e)
        return output_label

    def half_gates_ungarble(self, garblers_label, evaluators_label):
        """
            Evaluates the gate by decrypting each half gate and XORing
            the result.

            :param garblers_label: the chosen label by the garbler
            :param evaluators_label: the chosen label by the evaluator
            :return: the correct output label
            :rtype: :class:`Label`
        """
        if self.gate_type == 'AND':
            s_a, s_b = garblers_label.pp_bit, evaluators_label.pp_bit
            entry1, entry2 = self.table
            gen = hashlib.sha256(garblers_label.label).digest()
            eva = hashlib.sha256(evaluators_label.label).digest()

            C_g = xor(gen, entry1) if s_a else gen
            C_e = xor(eva, xor(entry2, garblers_label.label)) if s_b else eva

            output_label = Label(0)
            output_label.represents = None
            output_label.label = xor(C_g, C_e)
            output_label.pp_bit = get_last_bit(output_label.label)
            return output_label
        else:
            return self.free_xor_ungarble(garblers_label, evaluators_label)

    def transform_label(self, label, garbler=True):
        """
            Transforms the label accordingly.

            :param label: the label to transform
            :param bool garbler: the type of label supplied
        """
        pp_bit = label.pp_bit
        key = AESKey(label.label)
        table_entry = self.table[pp_bit if garbler else pp_bit + 2]
        if not table_entry:
            table_entry = bytes(settings.NUM_BYTES)
        label.label = key.decrypt(table_entry)
        return label

    def evaluate_gate(self, input1, input2):
        """
            Evaluates a gate given two inputs.

            :param bool input1: the first input
            :param bool input2: the second input
            :return: the output of the gate
            :rtype: bool
        """
        g = self.gates[self.gate_type]
        return g(input1, input2)

    def wires(self):
        """
            Returns the three wires related to the gate.

            :return: the three wires
            :rtype: list(:class:`Wire`)
        """
        return (self.left_wire, self.right_wire, self.output_wire)
