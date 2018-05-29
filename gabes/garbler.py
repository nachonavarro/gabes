import network as net
import time
import copy

from circuit import Circuit
from utils import ask_for_inputs
from ot import garbler_ot

def garbler(args):
	print("Welcome, garbler. Waiting for the evaluator...")
	sock, client = net.connect_garbler(args.address)
	circ = Circuit(args.circuit)
	identifiers = hand_over_wire_identifiers(client, circ)
	inputs = ask_for_inputs(identifiers)
	hand_over_labels(client, circ, inputs)
	hand_over_cleaned_circuit(client, circ)
	final_output = learn_output(client, circ)
	print("The final output of the circuit is: {}".format(final_output))
	sock.close()

def hand_over_wire_identifiers(client, circ):
	identifiers = [wire.identifier for wire in circ.get_input_wires()]
	net.send_data(client, *identifiers)
	net.wait_for_ack(client)
	return identifiers

def hand_over_cleaned_circuit(client, circ):
	new_circ = circ.clean()
	net.send_data(client, new_circ)

def hand_over_labels(client, circ, garbler_inputs):
	for wire in circ.get_input_wires():
		if wire.identifier in garbler_inputs:
			chosen_bit = garbler_inputs[wire.identifier]
			secret_label = wire.true_label if chosen_bit == '1' else wire.false_label
			net.send_data(client, secret_label)
			net.wait_for_ack(client)
		else:
			false_label = copy.deepcopy(wire.false_label)
			true_label  = copy.deepcopy(wire.true_label)
			# Clean before sending so that the evaluator does not learn anything.
			false_label.represents = true_label.represents = None
			garbler_ot(client, false_label, true_label)

def learn_output(client, circ):
	output_label = net.receive_data(client)[0]
	output_gate  = circ.tree.name
	output = output_label.to_base64() == output_gate.output_wire.true_label.to_base64()
	net.send_data(client, output)
	return output