import pickle
import gabes.settings as settings
import gabes.fields as fields
import hashlib

from gabes.wire import Wire
from gabes.label import Label
from gabes.utils import get_last_bit, xor, adjust_wire_offset, get_first_distinct
from gabes.crypto import AESKey, generate_zero_ciphertext
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
        elif settings.FREE_XOR:
            self.free_xor_garble()
        elif settings.FLEXOR:
            self.flexor_garble()
        elif settings.GRR3:
            self.grr3_garble()
        elif settings.GRR2:
            self.grr2_garble()
        elif settings.HALF_GATES:
            self.half_gates_garble()

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
                key1, key2   = AESKey(left_label.to_base64()), AESKey(right_label.to_base64())
                in1, in2     = left_label.represents, right_label.represents
                logic_value  = self.evaluate_gate(in1, in2)
                output_label = self.output_wire.get_label(logic_value)
                table_entry  = key1.encrypt(key2.encrypt(pickle.dumps(output_label)))
                left_pp_bit  = left_label.pp_bit
                right_pp_bit = right_label.pp_bit
                self.table[2 * left_pp_bit + right_pp_bit] = table_entry

    def grr3_garble(self):
        self.set_zero_ciphertext()
        self.table = [None] * 3
        for left_label in self.left_wire.labels():
            for right_label in self.right_wire.labels():
                left_pp_bit  = left_label.pp_bit
                right_pp_bit = right_label.pp_bit
                if left_pp_bit or right_pp_bit:
                    key1, key2   = AESKey(left_label.to_base64()), AESKey(right_label.to_base64())
                    in1, in2     = left_label.represents, right_label.represents
                    logic_value  = self.evaluate_gate(in1, in2)
                    output_label = self.output_wire.get_label(logic_value)
                    table_entry  = key1.encrypt(key2.encrypt(pickle.dumps(output_label)), to_base64=True)
                    self.table[2 * left_pp_bit + right_pp_bit - 1] = table_entry

    def free_xor_garble(self):
        if self.gate_type == 'XOR':
            A0, B0, R = self.left_wire.false_label.label, self.right_wire.false_label.label, settings.R
            C0, C1 = xor(A0, B0), xor(xor(A0, B0), R)
            pp_bit = get_last_bit(C0)
            f_label, t_label = self.output_wire.false_label, self.output_wire.true_label
            f_label.label  = C0
            f_label.pp_bit = pp_bit
            t_label.label  = C1
            t_label.pp_bit = not pp_bit
        else:
            if settings.GRR3:
                self.grr3_garble()
            else:
                self.point_and_permute_garble()

    def flexor_garble(self):
        if self.gate_type == 'XOR':
            self.table = [None] * 4
            left, right, out = self.wires()
            adjust_wire_offset(out)
            A0, B0, C0 = left.false_label.label, right.false_label.label, out.false_label.label
            A1, B1, C1 = left.true_label.label, right.true_label.label, out.true_label.label
            R1, R2, R3 = xor(A0, A1), xor(B0, B1), xor(C0, C1)
            k1, k2 = AESKey(A0), AESKey(B0)
            A0_ = k1.decrypt(bytes(settings.NUM_BYTES))
            B0_ = k2.decrypt(bytes(settings.NUM_BYTES))
            C0_, C1_ = xor(A0_, B0_), xor(xor(A0_, B0_), R3)
            A1_, B1_ = xor(A0_, R3), xor(B0_, R3)
            self.modify_pp_bits(A0_, B0_, C0_)
            out.false_label.label = C0_
            out.true_label.label  = C1_
            k1, k2 = AESKey(A1), AESKey(B1)
            if R1 == R2 == R3:
                self.free_xor_garble(with_GRR3=with_GRR3)
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
            elif settings.GRR2:
                self.grr2_garble()
            else:
                self.point_and_permute_garble()

    def grr2_garble(self):
        Ks = self.find_Ks()
        P0, Q0, P5, P6 = self.interpolate_polynomials(Ks)
        false_label, true_label = P0, Q0
        if get_last_bit(false_label) == get_last_bit(true_label):
            # PP bits are the same, try again with different labels.
            b = self.left_wire.false_label.pp_bit
            self.left_wire.false_label = Label(0, pp_bit=b)
            self.left_wire.true_label  = Label(1, pp_bit=not b)
            self.grr2_garble()
            return
        self.update_output_wire(false_label, true_label)
        self.table.extend([P5, P6])

    def half_gates_garble(self):
        self.table = [None] * 2
        H = lambda x: hashlib.sha256(x).digest()
        r = self.right_wire.false_label.pp_bit
        entry1 = xor(H(self.right_wire.false_label.label), self.output_wire.false_label.label)
        entry2 = xor(H(self.right_wire.true_label.label), self.output_wire.false_label.label)
        if r:
            entry2 = xor(entry2, settings.R)
        entry3 = xor(H(self.left_wire.false_label.label), self.output_wire.false_label.label)
        entry4 = xor(xor(H(self.left_wire.true_label.label), 
                     self.output_wire.false_label.label), self.right_wire.false_label.label)
        
        self.table[r] = entry1
        self.table[not r] = entry2
        self.table.extend([entry3, entry4])

    def update_output_wire(self, false_label, true_label):
        self.output_wire.false_label.label = false_label
        self.output_wire.true_label.label = true_label
        self.output_wire.false_label.pp_bit = get_last_bit(false_label)
        self.output_wire.true_label.pp_bit = get_last_bit(true_label)

    def set_zero_ciphertext(self):
        l, r = self.left_wire, self.right_wire
        zero_pp_left  = l.false_label if not l.false_label.pp_bit else l.true_label
        zero_pp_right = r.false_label if not r.false_label.pp_bit else r.true_label
        output_label  = generate_zero_ciphertext(zero_pp_left, zero_pp_right)
        in1, in2     = zero_pp_left.represents, zero_pp_right.represents
        logic_value  = self.evaluate_gate(in1, in2)
        true_label, false_label = self.output_wire.true_label, self.output_wire.false_label
        if logic_value:
            true_label.label  = output_label
            pp_bit = get_last_bit(output_label)
            true_label.pp_bit  = pp_bit
            false_label.pp_bit = not pp_bit
        else:
            false_label.label  = output_label
            pp_bit = get_last_bit(output_label)
            false_label.pp_bit = pp_bit
            true_label.pp_bit  = not pp_bit

    def modify_pp_bits(self, A0_, B0_, C0_):
        left, right, out = self.wires()
        l_pp_bit, r_pp_bit, out_pp_bit = get_last_bit(A0_), get_last_bit(B0_), get_last_bit(C0_)
        left.false_label.pp_bit = l_pp_bit
        left.true_label.pp_bit  = not l_pp_bit
        right.false_label.pp_bit = r_pp_bit
        right.true_label.pp_bit  = not r_pp_bit
        out.false_label.pp_bit = out_pp_bit
        out.true_label.pp_bit = not out_pp_bit

    def find_Ks(self):
        zero_ciphertext = bytes(settings.NUM_BYTES)
        l_f_label, l_t_label = self.left_wire.false_label, self.left_wire.true_label
        r_f_label, r_t_label = self.right_wire.false_label, self.right_wire.true_label
        if not l_f_label.pp_bit:
            lefts = (l_f_label, l_t_label)
        else:
            lefts = (l_t_label, l_f_label)
        if not r_f_label.pp_bit:
            rights = (r_f_label, r_t_label)
        else:
            rights = (r_t_label, r_f_label)
        ka0, ka1 = AESKey(lefts[0].to_base64()), AESKey(lefts[1].to_base64())
        kb0, kb1 = AESKey(rights[0].to_base64()), AESKey(rights[1].to_base64())
        Ks = [
              kb0.decrypt(ka0.decrypt(zero_ciphertext)),
              kb1.decrypt(ka0.decrypt(zero_ciphertext)),
              kb0.decrypt(ka1.decrypt(zero_ciphertext)),
              kb1.decrypt(ka1.decrypt(zero_ciphertext))
        ]
        K_f1 = (2 * l_f_label.pp_bit + r_f_label.pp_bit + 1, Ks[2 * l_f_label.pp_bit + r_f_label.pp_bit])
        K_f2 = (2 * l_f_label.pp_bit + r_t_label.pp_bit + 1, Ks[2 * l_f_label.pp_bit + r_t_label.pp_bit])
        K_f3 = (2 * l_t_label.pp_bit + r_f_label.pp_bit + 1, Ks[2 * l_t_label.pp_bit + r_f_label.pp_bit])
        K_t1 = (2 * l_t_label.pp_bit + r_t_label.pp_bit + 1, Ks[2 * l_t_label.pp_bit + r_t_label.pp_bit])
        return (K_f1, K_f2, K_f3, K_t1)

    def interpolate_polynomials(self, Ks):
        F = fields.GF(2, settings.NUM_BYTES * 8)
        K_f1, K_f2, K_f3, K_t1 = Ks
        X = [fields.to_poly(K_f1[0]), fields.to_poly(K_f2[0]), fields.to_poly(K_f3[0])]
        Y = [fields.to_poly(K_f1[1], rep='bytes'), fields.to_poly(K_f2[1], rep='bytes'), fields.to_poly(K_f3[1], rep='bytes')]
        P = fields.interpolate_polynomial(X, Y, F)
        P5, P6 = F.evaluate_polynomial(P, fields.to_poly(5)), F.evaluate_polynomial(P, fields.to_poly(6))
        X = [fields.to_poly(K_t1[0]), fields.to_poly(5), fields.to_poly(6)]
        Y = [fields.to_poly(K_t1[1], rep='bytes'), P5, P6]
        Q = fields.interpolate_polynomial(X, Y, F)
        P0, Q0 = F.evaluate_polynomial(P, [0]), F.evaluate_polynomial(Q, [0])
        P0, Q0 = fields.from_poly(P0), fields.from_poly(Q0)
        return (P0, Q0, P5, P6)

    def ungarble(self, garblers_label, evaluators_label):
        if settings.CLASSICAL:
            output_label = self.classical_ungarble(garblers_label, evaluators_label)
        elif settings.POINT_AND_PERMUTE:
            output_label = self.point_and_permute_ungarble(garblers_label, evaluators_label)
        elif settings.FREE_XOR:
            output_label = self.free_xor_ungarble(garblers_label, evaluators_label)
        elif settings.FLEXOR:
            output_label = self.flexor_ungarble(garblers_label, evaluators_label)
        elif settings.GRR3:
            output_label = self.grr3_ungarble(garblers_label, evaluators_label)
        elif settings.GRR2:
            output_label = self.grr2_ungarble(garblers_label, evaluators_label)
        elif settings.HALF_GATES:
            output_label = self.half_gates_ungarble(garblers_label, evaluators_label)

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
        key1, key2 = AESKey(garblers_label.to_base64()), AESKey(evaluators_label.to_base64())
        table_entry = self.table[2 * left_pp_bit + right_pp_bit]
        output_label = pickle.loads(key2.decrypt(key1.decrypt(table_entry)))
        return output_label

    def grr3_ungarble(self, garblers_label, evaluators_label):
        left_pp_bit  = garblers_label.pp_bit
        right_pp_bit = evaluators_label.pp_bit
        key1, key2   = AESKey(garblers_label.to_base64()), AESKey(evaluators_label.to_base64())
        if not left_pp_bit and not right_pp_bit:
            zero_ciphertext = bytes(settings.NUM_BYTES)
            output_label = Label(0)
            output_label.represents = None
            output_label.label = key2.decrypt(key1.decrypt(zero_ciphertext))
            output_label.pp_bit = get_last_bit(output_label.label)
        else:
            table_entry = self.table[2 * left_pp_bit + right_pp_bit - 1]
            output_label = pickle.loads(key2.decrypt(key1.decrypt(table_entry, from_base64=True)))
        return output_label

    def free_xor_ungarble(self, garblers_label, evaluators_label):
        if self.gate_type == 'XOR':
            output_label = Label(0)
            output_label.represents = None
            output_label.label = xor(garblers_label.label, evaluators_label.label)
            output_label.pp_bit = get_last_bit(output_label.label)
        else:
            if settings.GRR3:
                output_label = self.grr3_ungarble(garblers_label, evaluators_label)
            else:
                output_label = self.point_and_permute_ungarble(garblers_label, evaluators_label)
        return output_label

    def flexor_ungarble(self, garblers_label, evaluators_label):
        if self.gate_type == 'XOR':
            garblers_label   = self.transform_label(garblers_label, garbler=True)
            evaluators_label = self.transform_label(evaluators_label, garbler=False)
            output_label = self.free_xor_ungarble(garblers_label, evaluators_label)
        else:
            if settings.GRR3:
                output_label = self.grr3_ungarble(garblers_label, evaluators_label)
            elif settings.GRR2:
                output_label = self.grr2_ungarble(garblers_label, evaluators_label)
            else:
                output_label = self.point_and_permute_ungarble(garblers_label, evaluators_label)
        return output_label

    def grr2_ungarble(self, garblers_label, evaluators_label):
        key1, key2 = AESKey(garblers_label.to_base64()), AESKey(evaluators_label.to_base64())
        zero_ciphertext = bytes(settings.NUM_BYTES)
        Ki = key2.decrypt(key1.decrypt(zero_ciphertext))
        F = fields.GF(2, settings.NUM_BYTES * 8)
        r = 2 * garblers_label.pp_bit + evaluators_label.pp_bit + 1
        X = [fields.to_poly(r), fields.to_poly(5), fields.to_poly(6)]
        Y = [fields.to_poly(Ki, rep='bytes'), self.table[0], self.table[1]]
        R = fields.interpolate_polynomial(X, Y, F)
        output_label = Label(0)
        output_label.represents = None
        output_label.label = fields.from_poly(F.evaluate_polynomial(R, [0]))
        output_label.pp_bit = get_last_bit(output_label.label)
        return output_label

    def half_gates_ungarble(self, garblers_label, evaluators_label):
        import pdb; pdb.set_trace()
        br  = evaluators_label.pp_bit
        gen = hashlib.sha256(garblers_label.label).digest()
        eva = hashlib.sha256(evaluators_label.label).digest()

        if br:
            c1 = xor(self.table[3], gen)
            c1 = xor(c1, evaluators_label.label)
            c2 = xor(self.table[1], eva)
        else:
            c1 = xor(self.table[2], gen)
            c2 = xor(self.table[0], eva)

        output_label = Label(0)
        output_label.represents = None
        output_label.label = xor(c1, c2)
        output_label.pp_bit = get_last_bit(output_label.label)
        return output_label


    def transform_label(self, label, garbler=True):
        pp_bit = label.pp_bit
        key    = AESKey(label.label)
        table_entry = self.table[pp_bit if garbler else pp_bit + 2]
        if not table_entry:
            table_entry = bytes(settings.NUM_BYTES)
        label.label = key.decrypt(table_entry)
        return label

    def evaluate_gate(self, input1, input2):
        g = self.gates[self.gate_type]
        return g(input1, input2)

    def wires(self):
        return (self.left_wire, self.right_wire, self.output_wire)
















