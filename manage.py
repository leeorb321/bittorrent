import socket
import random

class Connection(object):
    # Class to manage connections with peers
    CHUNK_SIZE = 2**14

    def __init__(self, tracker_response, info_hash):
        self.tc = tracker_response
        self.num_peers = len(self.tc.resp['peers'])
        self.interval = self.tc.resp['interval']
        self.info_hash = info_hash
        self.handshake = self.create_handshake()
        self.download_file()

    def create_handshake(self):
        print("Creating handshake message ...")
        pstrlen = bytes([19])
        pstr = b'BitTorrent protocol'
        reserved = b'\0' * 8
        info_hash = self.info_hash
        peer_id = self.tc.peer_id
        return pstrlen + pstr + reserved + info_hash + peer_id

    def download_file(self):
        peers = self.tc.resp['peers']
        p = self.get_next_peer(peers)
        print("Response recieved, sending file request ...")
        m = self.compose_request_message(0, 0)
        self.send_message(p, m)

    def get_next_peer(self, peers):
        for key, peer in peers.items():
            print("Checking peer ...")
            if self.initial_connection(peer):
                return peer

    def initial_connection(self, peer):
        r = self.send_handshake(peer)
        if r is not None and len(r) > 0:
            if self.validate_hash(r) == False:
                print("Hash invalid")
                return False
            else:
                return True
        return False

    def send_message(self, peer, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect((peer.ip, peer.port))
            sent = s.send(message)
            return self.wait_for_response(s)
        except (ConnectionRefusedError, socket.timeout) as e:
            print("Error connecting: %r" % e)

    def send_handshake(self, peer):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        message = self.handshake
        try:
            s.connect((peer.ip, peer.port))
            sent = s.send(message)
            return self.wait_for_handshake(s)
        except (ConnectionRefusedError, socket.timeout) as e:
            print("Error connecting: %r" % e)

    def wait_for_handshake(self, s):
        r0 = s.recv(1)
        expected_length = int.from_bytes(r0, byteorder = 'big') + 49
        print("Handshake received with length %d"%expected_length)
        bytes_received = len(r0)
        r = r0
        if bytes_received == 0: return r
        while bytes_received < expected_length:
            print ("Reading bytes - received %d out of %d bytes so far"%(bytes_received,expected_length))
            bytes_read = s.recv(expected_length - bytes_received)
            if len(bytes_read) == 0: return r
            bytes_received += len(bytes_read)
            r += bytes_read
        return r

    def wait_for_response(self, s):
        print("Message sent - waiting for response")
        r0 = s.recv(4)
        expected_length = int.from_bytes(r0, byteorder = 'big')
        print("Message received with length %d"%expected_length)
        msg_id = int.from_bytes(s.recv(1), byteorder = 'big')
        print("Message received with id %d"%msg_id)

        bytes_received = 1
        r = b''

        while bytes_received < expected_length:
            print ("Reading bytes ...")
            bytes_read = s.recv(self.CHUNK_SIZE)
            bytes_received += len(bytes_read)
            r += bytes_read

        print("Received %d bytes"%bytes_received)
        return r

    def handle_piece(self, response):
        index = int.from_bytes(response[:4], byteorder = 'big')
        begin = int.from_bytes(response[4:8], byteorder = 'big')
        block = response[8:]
        print("Received block of length: %d"%len(block))

    def validate_hash(self, response):
        print("Validating hash for message")
        prefix = response[0]
        return response[prefix + 1 + 8:-20] == self.info_hash

    def compose_request_message(self, index, begin):
        req = (13).to_bytes(4, byteorder='big') + (6).to_bytes(1, byteorder='big') + \
            (index).to_bytes(4, byteorder='big') +(begin).to_bytes(4, byteorder='big') + (self.CHUNK_SIZE).to_bytes(4, byteorder='big')
        return req

    def compose_interested_message(self, peer):
        interested = (1).to_bytes(4, byteorder='big') + (2).to_bytes(1, byteorder='big')
        return interested
