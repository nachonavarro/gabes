"""
This module handles all the cryptography involved with garbled circuits.
The external module :mod:`cryptography` offers a Fernet encryption scheme
that suits well for classical garbled circuits as it shows if decryption was
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


class AESKey(object):
    """
        The :class:`AESKey` object handles the key to AES and the
        encryption/decryption routines. To ensure that the key
        can be fed into AES, the input to the object is hashed
        with SHA256 to a 32 bytestring (AES only allows 16/32/64
        bytes inputs).

        :param bytes key: parameter to be hashed and used as a key

        .. code-block:: python

            >>> from gabes.crypto import AESKey
            >>> from gabes.label import Label
            >>> label = Label(1)
            >>> key = AESKey(label.to_base64())
            >>> enc = key.encrypt(b"The winner is...")
            >>> key.decrypt(enc)
            b'The winner is...'

    """

    def __init__(self, key):
        m = hashlib.sha256()
        m.update(key)
        self.key = m.digest()
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def encrypt(self, msg, to_base64=False, pad=True):
        """
            Encrypts the message ``msg`` by first padding it
            if necessary since AES requires prespecified input sizes.
            It then converts the cipher into base64 if needed.

            :param msg: the message to be encrypted
            :type msg: bytes
            :param bool to_base64: (optional) whether to convert the cipher \
            to base64
            :param bool pad: (optional) whether to pad the message
            :return: encrypted message
            :rtype: bytes

        """
        msg = self.pad(msg) if pad else msg
        cip = self.cipher.encrypt(msg)
        if to_base64:
            return base64.urlsafe_b64encode(cip)
        else:
            return cip

    def decrypt(self, msg, from_base64=False, unpad=True):
        """
            Decrypts the message ``msg`` by first unpadding it or decoding it
            from base64 if necessary.

            :param msg: the message to be decrypted
            :type msg: bytes
            :param bool from_base64: (optional) whether to decode the cipher \
            from base64
            :param bool unpad: (optional) whether to unpad the message
            :return: decrypted message
            :rtype: bytes

        """
        if from_base64:
            msg = base64.urlsafe_b64decode(msg)
        t = self.cipher.decrypt(msg)
        return self.unpad(t) if unpad else t

    def pad(self, msg, size=16):
        """
            Takes a bytestring and pads it to be a multiple of ``size``.
            To keep track of the padding, the first four bytes store
            the size of the padded bytestring.

            :param bytes msg: the bytestring to pad
            :param int size: (optional) padded result must be a multiple of \
            this number
            :return: padded bytestring
            :rtype: bytes

        """
        with_size = struct.pack('>I', len(msg)) + msg
        padded = with_size + bytes((size - len(with_size) % size) % size)
        return padded

    def unpad(self, msg):
        """
            Takes a bytestring and unpads it to the original bytestring.
            Since the first four bytes store the original unpadded `size` of
            the bytestring, we extract those four bytes and return the
            bytestring from position 4
            to :code:`size + 4` .

            :param bytes msg: the bytestring to unpad
            :return: unpadded bytestring
            :rtype: bytes

        """
        n = struct.unpack('>I', msg[:4])[0]
        if n:
            return msg[4:n + 4]
        else:
            return msg


def generate_zero_ciphertext(left_label, right_label):
    """
        Generates the label `c` that when decrypted using
        the ``left_label`` and ``right_label`` keys will
        yield the zero ciphertext.

        :param left_label: left label to use as key
        :type left_label: :class:`Label`
        :param right_label: right label to use as key
        :type right_label: :class:`Label`
        :return: encrypted text
        :rtype: bytes

        .. code-block:: python

            >>> from gabes.crypto import AESKey, generate_zero_ciphertext
            >>> from gabes.label import Label
            >>> left_label, right_label = Label(0), Label(1)
            >>> key1 = AESKey(left_label.to_base64())
            >>> key2 = AESKey(right_label.to_base64())
            >>> enc = generate_zero_ciphertext(left_label, right_label)
            >>> enc
            b'\\\\\\x07\\x08\\xd8\\x05\\x8bX\\x1dE\\x05\\x83D ?\\xe6
            \\x10\\\\\\x07\\x08\\xd8\\x05\\x8bX\\x1dE\\x05\\x83D ?\\xe6\\x10'
            >>> key1.encrypt(key2.encrypt(enc, pad=False), pad=False)
            b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00
            \\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\
            x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'

        """
    k1 = AESKey(left_label.to_base64())
    k2 = AESKey(right_label.to_base64())
    enc = k2.decrypt(k1.decrypt(bytes(settings.NUM_BYTES), unpad=False),
                     unpad=False)
    return enc
