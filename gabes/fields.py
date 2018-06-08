# Credits to:
# https://stackoverflow.com/questions/48065360
# /interpolate-polynomial-over-a-finite-field

import itertools
import math
import sympy.polys.galoistools as gf

from functools import reduce
from sympy.polys.domains import ZZ


IRREDUCIBLE_POLYNOMIALS = {
    1: b'\x03',
    2: b'\x07',
    4: b'\x19',
    8: b'\x01q',
    16: b'\x01h\x01',
    32: b'\x012\x82\x00\x01',
    64: b'\x01\xdax_\xc4\x80\x00\x00\x01',
    128: b'\x01k+\x9f9\x1a\xe1\x1cB\xcd\xaa\x8b\x9e\xf9\xfb\xa9\xf3',
    256: b'\x01H\x1b\x91\x07EN\xac\xd9\xc9F\xf9\xed \
           \x95\xb9\x02\x10\xe8\x81N\xc220\x0cC\x07\xf1\xe7\xc2w\xa6\x11\x99'
}


class GF():
    def __init__(self, p, n=1):
        if n <= 0 or n not in IRREDUCIBLE_POLYNOMIALS:
            raise ValueError("n must be a positive integer or a power of 2")
        self.p = p
        self.n = n
        self.reducing = to_poly(IRREDUCIBLE_POLYNOMIALS[n], rep='bytes')

    def add(self, x, y):
        return gf.gf_add(x, y, self.p, ZZ)

    def sub(self, x, y):
        return gf.gf_sub(x, y, self.p, ZZ)

    def mul(self, x, y):
        return gf.gf_rem(gf.gf_mul(x, y, self.p, ZZ),
                         self.reducing, self.p, ZZ)

    def inv(self, x):
        s, t, h = gf.gf_gcdex(x, self.reducing, self.p, ZZ)
        return s

    def evaluate_polynomial(self, poly, point):
        val = []
        for c in poly:
            val = self.mul(val, point)
            val = self.add(val, c)
        return val


class PolynomialRing():
    def __init__(self, field):
        self.K = field

    def add(self, p, q):
        zipped = itertools.zip_longest(p[::-1], q[::-1], fillvalue=[])
        s = [self.K.add(x, y) for x, y in zipped]
        return s[::-1]

    def sub(self, p, q):
        zipped = itertools.zip_longest(p[::-1], q[::-1], fillvalue=[])
        s = [self.K.sub(x, y) for x, y in zipped]
        return s[::-1]

    def mul(self, p, q):
        if len(p) < len(q):
            p, q = q, p
        s = [[]]
        for j, c in enumerate(q):
            ls = [[]] * (len(q) - j - 1)
            s = self.add(s, [self.K.mul(b, c) for b in p] + ls)
        return s


def to_poly(b, rep='num'):
    if rep == 'bytes':
        b = int.from_bytes(b, byteorder='big')
    bits = '{0:b}'.format(b)
    poly = [int(bit) for bit in bits]
    return poly


def from_poly(poly, to='num'):
    bits = ''.join([str(bit) for bit in poly])
    num_bytes = math.ceil(len(bits) / 8)
    return int(bits, 2).to_bytes(length=num_bytes, byteorder='big')


def interpolate_polynomial(X, Y, K):
    R = PolynomialRing(K)
    poly = [[]]
    for j, y in enumerate(Y):
        Xe = X[:j] + X[j+1:]
        numer = reduce(lambda p, q: R.mul(p, q),
                       ([[1], K.sub([], x)] for x in Xe))
        denom = reduce(lambda x, y: K.mul(x, y),
                       (K.sub(X[j], x) for x in Xe))
        poly = R.add(poly, R.mul(numer, [K.mul(y, K.inv(denom))]))
    return poly


def find_Ks(self):
    zero_ciphertext = bytes(settings.NUM_BYTES)
    l_f_label = self.left_wire.false_label
    l_t_label = self.left_wire.true_label
    r_f_label = self.right_wire.false_label
    r_t_label = self.right_wire.true_label
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
    K_f1 = (2 * l_f_label.pp_bit + r_f_label.pp_bit + 1,
            Ks[2 * l_f_label.pp_bit + r_f_label.pp_bit])
    K_f2 = (2 * l_f_label.pp_bit + r_t_label.pp_bit + 1,
            Ks[2 * l_f_label.pp_bit + r_t_label.pp_bit])
    K_f3 = (2 * l_t_label.pp_bit + r_f_label.pp_bit + 1,
            Ks[2 * l_t_label.pp_bit + r_f_label.pp_bit])
    K_t1 = (2 * l_t_label.pp_bit + r_t_label.pp_bit + 1,
            Ks[2 * l_t_label.pp_bit + r_t_label.pp_bit])
    return (K_f1, K_f2, K_f3, K_t1)


def interpolate_polynomials(self, Ks):
    F = fields.GF(2, settings.NUM_BYTES * 8)
    K_f1, K_f2, K_f3, K_t1 = Ks
    X = [fields.to_poly(K_f1[0]), fields.to_poly(K_f2[0]),
         fields.to_poly(K_f3[0])]
    Y = [fields.to_poly(K_f1[1], rep='bytes'),
         fields.to_poly(K_f2[1], rep='bytes'),
         fields.to_poly(K_f3[1], rep='bytes')]
    P = fields.interpolate_polynomial(X, Y, F)
    P5 = F.evaluate_polynomial(P, fields.to_poly(5))
    P6 = F.evaluate_polynomial(P, fields.to_poly(6))
    X = [fields.to_poly(K_t1[0]), fields.to_poly(5), fields.to_poly(6)]
    Y = [fields.to_poly(K_t1[1], rep='bytes'), P5, P6]
    Q = fields.interpolate_polynomial(X, Y, F)
    P0, Q0 = F.evaluate_polynomial(P, [0]), F.evaluate_polynomial(Q, [0])
    P0, Q0 = fields.from_poly(P0), fields.from_poly(Q0)
    return (P0, Q0, P5, P6)