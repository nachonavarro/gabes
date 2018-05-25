import socket
import pickle
from utils import ask_for_inputs

def evaluator(address, circuit_file):
	sock   = connect_evaluator(address)
	inputs = ask_for_inputs(circuit_file)
	serialized = pickle.dumps(inputs)
	sock.send(serialized)
	data = sock.recv(1024)
	sock.close()

def connect_evaluator(address):
	ip, port = address.split(':')
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((ip, int(port)))
	return sock