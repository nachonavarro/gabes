import gabes.settings as settings
import os

def ask_for_inputs(identifiers):

	print("To start the protocol please indicate with y/n which wires you supply:")
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
				decision = input("Sorry, didn't recognize that. Indicate with y or n whether you supply {}: ".format(identifier))

	inputs = {}
	for identifier in chosen_wires:
		label_choice = input("Choice for {}: ".format(identifier))
		while True:
			if label_choice in '01':
				break
			else:
				label_choice = input("Sorry, you must supply either a 0 (indicating false) or a 1 (indicating true) for wire {}: ".format(identifier))

		inputs[identifier] = label_choice

	return inputs

def get_last_bit(label):
	last_byte = label[-1]
	return bool((last_byte >> 7) & 1)

def xor(b1, b2):
	xored = int.from_bytes(b1, byteorder='big') ^ int.from_bytes(b2, byteorder='big')
	return int.to_bytes(xored, length=settings.NUM_BYTES, byteorder='big')

def adjust_wire_offset(wire):
	while get_last_bit(wire.false_label.label) == get_last_bit(wire.true_label.label):
		wire.true_label.label = os.urandom(settings.NUM_BYTES)

def get_first_distinct(false_label, true_label):
    b1 = int.from_bytes(false_label, byteorder='big')
    b1 = '{0:b}'.format(b1)[::-1]
    b2 = int.from_bytes(true_label, byteorder='big')
    b2 = '{0:b}'.format(b2)[::-1]
    for bit1, bit2 in zip(b1, b2):
    	if bit1 != bit2:
    		return bool(int(bit1))
















