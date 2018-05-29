import socket
import pickle
import time

def connect_garbler(address):
	ip, port = address.split(':')
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((ip, int(port)))
	sock.listen(1)
	client, addr = sock.accept()
	return sock, client

def connect_evaluator(address):
	ip, port = address.split(':')
	print("Welcome, evaluator. Waiting for the garbler...", flush=True)
	while True:
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((ip, int(port)))
			break
		except Exception as e:
			time.sleep(1)

	return sock

def send_data(sock, *data, serialize=True):
	if serialize:
		data = pickle.dumps(data)
	sock.send(data)

def receive_data(from_whom, buff=8192, deserialize=True):
	if deserialize:
		data = pickle.loads(from_whom.recv(buff))
	else:
		data = from_whom.recv(buff)
	return data

def send_ack(sock):
	send_data(sock, 'ACK')

def wait_for_ack(sock):
	while True:
		msg = receive_data(sock)[0]
		if msg == 'ACK':
			break