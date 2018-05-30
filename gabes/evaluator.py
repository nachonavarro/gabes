import network as net
import time

from ot import evaluator_ot
from utils import ask_for_inputs
from circuit import Circuit

def evaluator(args):
	sock   = net.connect_evaluator(args.address)
	idents = request_wire_identifiers(sock)
	inputs = ask_for_inputs(idents)
	labels = request_labels(sock, idents, inputs)
	circ   = request_cleaned_circuit(sock)
	secret_output = circ.reconstruct(labels)
	final_output  = learn_output(sock, secret_output)
	print("The final output of the circuit is: {}".format(final_output))
	sock.close()

def request_cleaned_circuit(sock):
	circuit = net.receive_data(sock)
	return circuit

def request_wire_identifiers(sock):
	identifiers = net.receive_data(sock)
	net.send_ack(sock)
	return identifiers

def request_labels(sock, identifiers, evaluator_inputs):
	labels = []
	for identifier in identifiers:
		if identifier in evaluator_inputs:
			chosen_bit = evaluator_inputs[identifier]
			secret_label = evaluator_ot(sock, chosen_bit)
		else:
			secret_label = net.receive_data(sock)
			net.send_ack(sock)
		labels.append(secret_label)
	return labels

def learn_output(sock, secret_output):
	net.send_data(sock, secret_output)
	final_output = net.receive_data(sock)
	return final_output