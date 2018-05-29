import settings
import pickle
from wire import Wire
from cryptography.fernet import Fernet, InvalidToken
from Crypto.Random.random import shuffle

class Gate(object):
    """The :class:`Gate` object contains four labels representing
    *True* and *False* for the two input wires and two labels for
    the output wire.
    """

    gates = {
        'AND': lambda in1, in2: in1 & in2,
        'XOR': lambda in1, in2: in1 ^ in2,
        'OR':  lambda in1, in2: in1 | in2
    }

    def __init__(self, gate_type, create_left_wire=True, create_right_wire=True):
        self.table = []
        self.gate_type = gate_type
        self.left_wire   = Wire() if create_left_wire else None
        self.right_wire  = Wire() if create_right_wire else None
        self.output_wire = Wire()

    def __str__(self):
        return self.gate_type

    def garble(self):
        if settings.CLASSICAL:
            self.classical_garble()
        elif settings.POINT_AND_PERMUTE:
            self.point_and_permute_garble()

    def classical_garble(self):
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                key1, key2   = Fernet(left_label.to_base64()), Fernet(right_label.to_base64())
                in1, in2     = left_label.represents, right_label.represents
                logic_value  = self.evaluate_gate(in1, in2)
                output_label = self.output_wire.get_label(logic_value)
                table_entry  = key1.encrypt(key2.encrypt(pickle.dumps(output_label)))
                self.table.append(table_entry)

        shuffle(self.table)

    def point_and_permute_garble(self):
        self.table = [None] * 4
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                key1, key2   = Fernet(left_label.to_base64()), Fernet(right_label.to_base64())
                in1, in2     = left_label.represents, right_label.represents
                logic_value  = self.evaluate_gate(in1, in2)
                output_label = self.output_wire.get_label(logic_value)
                table_entry  = key1.encrypt(key2.encrypt(pickle.dumps(output_label)))
                left_pp_bit  = left_label.pp_bit
                right_pp_bit = right_label.pp_bit
                self.table[2 * left_pp_bit + right_pp_bit] = table_entry

    def ungarble(self, garblers_label, evaluators_label):
        if settings.CLASSICAL:
            output_label = self.classical_ungarble(garblers_label, evaluators_label)
        elif settings.POINT_AND_PERMUTE:
            output_label = self.point_and_permute_ungarble(garblers_label, evaluators_label)
        return output_label

    def classical_ungarble(self, garblers_label, evaluators_label):
        for table_entry in self.table:
            try:
                key1, key2 = Fernet(garblers_label.to_base64()), Fernet(evaluators_label.to_base64())
                output_label = pickle.loads(key2.decrypt(key1.decrypt(table_entry)))
            except InvalidToken:
                # Wrong table entry, try again
                pass
        return output_label

    def point_and_permute_ungarble(self, garblers_label, evaluators_label):
        left_pp_bit  = garblers_label.pp_bit
        right_pp_bit = evaluators_label.pp_bit
        key1, key2 = Fernet(garblers_label.to_base64()), Fernet(evaluators_label.to_base64())
        table_entry = self.table[2 * left_pp_bit + right_pp_bit]
        output_label = pickle.loads(key2.decrypt(key1.decrypt(table_entry)))
        return output_label

    def evaluate_gate(self, input1, input2):
        g = self.gates[self.gate_type]
        return g(input1, input2)