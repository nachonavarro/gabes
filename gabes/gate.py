from wire import Wire
from cryptography.fernet import Fernet
from Crypto.Random.random import shuffle

class Gate(object):
    """The :class:`Gate` object contains four labels representing
    *True* and *False* for the two input wires and two labels for
    the output wire.
    """

    gates = {
        'AND': lambda in1, in2: in1 & in2,
        'XOR': lambda in1, in2: in1 ^ in2
    }

    def __init__(self, gate_type, create_labels=True):
        self.table = []
        self.gate_type = gate_type
        if create_labels:
            self.left_wire   = Wire()
            self.right_wire  = Wire()
            self.output_wire = Wire()

    def __str__(self):
        return self.gate_type

    def garble_gate(self):
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                key1, key2   = Fernet(left_label.label), Fernet(right_label.label)
                in1, in2     = left_label.represents, right_label.represents
                logic_value  = self.evaluate_gate(in1, in2)
                output_label = self.output_wire.get_label(logic_value)
                table_entry  = key1.encrypt(key2.encrypt(output_label.label))
                self.table.append(table_entry)

        shuffle(self.table)

    def evaluate_gate(self, input1, input2):
        g = self.gates[self.gate_type]
        return g(input1, input2)