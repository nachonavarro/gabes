import os
import base64


class Label(object):
	"""The :class:`Label` object, which contains the label
	that will represent either the boolean *False* or *True* for a particular gate.
	"""

	def __init__(self, represents, pp_bit=None):
		self.label = os.urandom(32)
		self.represents = represents
		self.pp_bit = pp_bit

	def __repr__(self):
		return str(self.to_base64())

	def __str__(self):
		return str(self.to_base64())

	def __int__(self):
		return int.from_bytes(self.label, byteorder='big')

	def to_base64(self):
		return base64.urlsafe_b64encode(self.label)

	@staticmethod
	def int_to_bytes(n):
		return int.to_bytes(n, length=32, byteorder='big')
