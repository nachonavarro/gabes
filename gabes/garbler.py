import socket
import pickle

def garbler(address, circuit_file):
	sock = connect_garbler(address)
	client, addr = sock.accept()
	data = client.recv(1024)
	hel = pickle.loads(data)
	print(hel)
	sock.close()

def connect_garbler(address):
	ip, port = address.split(':')
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((ip, int(port)))
	sock.listen(1)
	return sock