import socket
import pickle
import time
import struct

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

def send_data(sock, data):
    data = pickle.dumps(data)
    size = struct.pack('>I', len(data))
    sock.send(size + data)

def receive_data(from_whom):
    size = _receive_data(from_whom, 4)
    size = struct.unpack('>I', size)[0] 
    data = _receive_data(from_whom, size)
    pickled_data = pickle.loads(data)
    return pickled_data

def _receive_data(sock, num_bytes):
    data = b''
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            break
        data += packet
    return data

def send_ack(sock):
    send_data(sock, 'ACK')

def wait_for_ack(sock):
    while True:
        msg = receive_data(sock)
        if msg == 'ACK':
            break