"""
This module is in charge of handling all the communication between the garbler
and the evaluator, providing an easy API to hide the lower-level sockets.
"""

import socket
import pickle
import time
import struct


def connect_garbler(address):
    """
        Connects the garbler to the socket. The garbler will act as
        the server, and the evaluator as the client.

        :param str address: the address of the socket (IP and the port \
        number in the format IP:port)
        :return: the socket and the client (the evaluator)

    """
    ip, port = address.split(':')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, int(port)))
    sock.listen(1)
    client, addr = sock.accept()
    return sock, client


def connect_evaluator(address):
    """
        Connects the evaluator to the socket. The garbler will act as
        the server, and the evaluator as the client.

        :param str address: the address of the socket (IP and the port \
        number in the format IP:port)
        :return: the socket

    """
    ip, port = address.split(':')
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, int(port)))
            break
        except Exception as e:
            time.sleep(1)
    return sock


def send_data(sock, data):
    """
        Sends :code:`data` through the socket. The data is pickled so that
        objects can be sent through the socket. As the socket can accept a
        fixed size number of bytes, the function sends the size of the data
        to know how many bytes to receive through the network.

        :param sock: the socket or the client
        :param bytes data: the data to send through the socket

    """
    data = pickle.dumps(data)
    size = struct.pack('>I', len(data))
    sock.send(size + data)


def receive_data(from_whom):
    """
        Receives data through the socket.

        :param from_whom: either the client (evaluator) or the socket \
        (the garbler)
        :return: the unpickled data

    """
    size = _receive_data(from_whom, 4)
    size = struct.unpack('>I', size)[0]
    data = _receive_data(from_whom, size)
    unpickled_data = pickle.loads(data)
    return unpickled_data


def _receive_data(sock, num_bytes):
    data = b''
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            break
        data += packet
    return data


def send_ack(sock):
    """
        Sends an *ACK* through the socket. This will be useful for
        the OT protocol.

        :param sock: either the client (evaluator) or the socket (the garbler)

    """
    send_data(sock, 'ACK')


def wait_for_ack(sock):
    """
        Waits until it receives an *ACK* through the socket. This will be
        useful for the OT protocol.

        :param sock: either the client (evaluator) or the socket (the garbler)

    """
    while True:
        msg = receive_data(sock)
        if msg == 'ACK':
            break
