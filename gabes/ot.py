import pickle

from random import randint
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from network import send_data, receive_data, send_ack, wait_for_ack
from label import Label

def garbler_ot(client, m0, m1):
	private_key = rsa.generate_private_key(public_exponent=65537, key_size=512, backend=default_backend())
	d = private_key.private_numbers().d

	public_key = private_key.public_key()
	n, e = public_key.public_numbers().n, public_key.public_numbers().e
	
	x0, x1 = [randint(2, n // 2) for _ in range(2)]
	send_data(client, [x0, x1, n, e])
	v = receive_data(client)
	k0, k1 = [pow((v - x), d, n) for x in (x0, x1)]
	bytes_m0 = pickle.dumps(m0)
	bytes_m1 = pickle.dumps(m1)
	m0 = int.from_bytes(bytes_m0, byteorder='big')
	m1 = int.from_bytes(bytes_m1, byteorder='big')
	send_data(client, [m0 + k0, m1 + k1, len(bytes_m0), len(bytes_m1)])
	wait_for_ack(client)

def evaluator_ot(sock, b):
	x0, x1, n, e = receive_data(sock)
	k = randint(2, n // 2)
	chosen_x = x1 if b == '1' else x0
	v = (chosen_x + pow(k, e, n)) % n
	send_data(sock, v)
	t0, t1, size_m0, size_m1 = receive_data(sock)
	chosen_t = t1 if b == '1' else t0
	chosen_size = size_m1 if b == '1' else size_m0
	m = chosen_t - k
	label = pickle.loads(int.to_bytes(m, length=chosen_size, byteorder='big'))
	send_ack(sock)
	return label
