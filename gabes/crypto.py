"""

gabes.crypto
~~~~~~~~~~~~

This module handles all the cryptography involved with garbled circuits.
The module *cryptography* offers a Fernet encryption scheme that suits
well for classical garbled circuits as it shows if decryption was
successful or not. However, for the majority of optimizations decrypting
the zero ciphertext is necessary. Therefore, the encryption/decryption 
scheme used is AES. While probably an unfit
choice for a secure application, AES suffices for simple applications.
If more security is needed, the recommendation is to change AES for 
a stronger cryptographic encryption scheme such as AES256.
"""

import struct
import hashlib
import base64
import gabes.settings as settings

from Crypto.Cipher import AES

def _pad(s, size=16):
    """
    Takes a bytes object and pads it to be a multiple of :size
    """
    with_size = struct.pack('>I', len(s)) + s
    padded =  with_size + bytes((size - len(with_size) % size) % size)
    return padded

def _unpad(s):
    n = struct.unpack('>I', s[:4])[0]
    if n:
        return s[4:n + 4]
    else:
        return s

class AESKey(object):
    def __init__( self, key ):
        m = hashlib.sha256()
        m.update(key)
        self.key = m.digest()
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def encrypt(self, msg, to_base64=False, pad=True):
        msg = _pad(msg)
        cip = self.cipher.encrypt(msg)
        if to_base64:
            return base64.urlsafe_b64encode(cip)
        else:
            return cip

    def decrypt(self, msg, unpad=True, from_base64=False):
        if from_base64:
            msg = base64.urlsafe_b64decode(msg)
        t = self.cipher.decrypt(msg)
        return _unpad(t) if msg != bytes(settings.NUM_BYTES) else t

def generate_zero_ciphertext(left_label, right_label):
    k1  = AESKey(left_label.to_base64())
    k2  = AESKey(right_label.to_base64())
    enc = k2.decrypt(k1.decrypt(bytes(settings.NUM_BYTES)))
    return enc