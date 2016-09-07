import socket
import random

class Connection(object):
    # Class to manage connections with peers
    CHUNK_SIZE = 4
    TIMEOUT = 1

    MESSAGE_HANDLERS = {
                0: 'handle_choke',
                1: 'handle_unchoke',
                2: 'handle_interested',
                3: 'handle_not_interested',
                4: 'handle_have',
                5: 'handle_bitfield',
                6: 'handle_request',
                7: 'handle_piece',
                8: 'handle_cancel',
                9: 'handle_port'
            }

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
        next_peer = self.get_next_peer(peers)
        print("Response received, sending file request ...")
        msg = self.compose_request_message(index=1, begin=1)
        # msg = self.compose_interested_message()
        self.send_message(next_peer, msg)

    def get_next_peer(self, peers):
        for _, peer in peers.items():
            print("Checking peer ...")
            s = self.initial_connection(peer)
            if s:
                self.wait_for_response(s, peer)

                return peer

    def initial_connection(self, peer):
        r, s = self.send_handshake(peer)
        if r is not None and len(r) > 0:
            if self.validate_hash(r) == False:
                print("Hash invalid")
                return False
            else:
                print("Hash valid")
                return s
        return False

    def send_handshake(self, peer):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.TIMEOUT)
        message = self.handshake
        try:
            s.connect((peer.ip, peer.port))
            sent = s.send(message)
            return self.wait_for_handshake(s)
        except (ConnectionRefusedError, socket.timeout) as e:
            print("Error connecting: %r" % e)
            return None, None

    def wait_for_handshake(self, s):
        r0 = s.recv(1)
        expected_length = int.from_bytes(r0, byteorder = 'big') + 49
        print("Handshake received with length %d" % expected_length)
        bytes_received = len(r0)
        received_from_tracker = r0

        if bytes_received == 0:
            return received_from_tracker, None

        while bytes_received < expected_length:
            print("Reading bytes - received %d out of %d bytes so far" % (bytes_received, expected_length))
            bytes_read = s.recv(expected_length - bytes_received)

            if len(bytes_read) == 0:
                return received_from_tracker, None

            bytes_received += len(bytes_read)
            received_from_tracker += bytes_read
        return received_from_tracker, s

    def validate_hash(self, response):
        print("Validating hash for message")
        prefix = response[0]
        return response[prefix + 1 + 8:-20] == self.info_hash

    def compose_request_message(self, index, begin):
        req = (13).to_bytes(4, byteorder='big') + (6).to_bytes(1, byteorder='big') + \
            (index).to_bytes(4, byteorder='big') +(begin).to_bytes(4, byteorder='big') + \
            (self.CHUNK_SIZE).to_bytes(4, byteorder='big')
        return req

    def send_message(self, peer, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.settimeout(2)
        try:
            s.connect((peer.ip, peer.port))
            sent = s.send(message)
            return self.wait_for_response(s, peer)
        except (ConnectionRefusedError, socket.timeout) as e:
            print("Error connecting: %r" % e)

    def wait_for_response(self, s, peer):
        print("Message sent - waiting for response")

        msg_len = 1
        while msg_len != 0:
            print ("Reading bytes ...")
            try:
                msg_len = int.from_bytes(s.recv(4), byteorder='big')
            except:
                return None

            msg_id = s.recv(1)

            print("Message id is %d, length is %d" % (int.from_bytes(msg_id, byteorder='big'), msg_len))

            bytes_read = s.recv(msg_len - 1)
            received_from_peer = b''
            received_from_peer += bytes_read
            bytes_received = 1

            while len(bytes_read) != 0 and bytes_received < msg_len - 1:
                bytes_read = s.recv(msg_len - 1 - len(received_from_peer))
                bytes_received += len(bytes_read)
                received_from_peer += bytes_read

            print("Just read %d bytes" % len(bytes_read))

            handler = getattr(self, self.MESSAGE_HANDLERS[int.from_bytes(msg_id, byteorder='big')])
            handler(peer, received_from_peer)
            print(peer.pieces)

        print("Received %d bytes" % bytes_received)
        return received_from_peer


    def handle_choke(self, peer, message):
        pass

    def handle_unchoke(self, peer, message):
        pass

    def handle_interested(self, peer, message):
        pass

    def handle_not_interested(self, peer, message):
        pass

    def handle_have(self, peer, message):
        print("Message type is 'have'")
        piece = int.from_bytes(message, byteorder='big')
        print(piece)
        peer.add_piece(piece)

    def handle_bitfield(self, peer, message):
        print("Message type is 'bitfield'")
        # num_pieces = self.tc.pieces
        # if len(message) // 8 + 1 != num_pieces:
        #     print("Incorrect length, bitfield.")
        #     return False
        # else:
        pieces = bin(int.from_bytes(message, byteorder='big'))[2:]
        available_indices = [i for i in range(len(pieces)) if pieces[i] == '1']
        peer.add_from_bitfield(available_indices)

    def handle_request(self, peer, message):
        pass

    def handle_piece(self, peer, message):
        index = int.from_bytes(message[:4], byteorder='big')
        begin = int.from_bytes(message[4:8], byteorder='big')
        block = message[8:]
        print("Received block of length: %d" % len(block))

    def handle_cancel(self, peer, message):
        pass

    def handle_port(self, peer, message):
        pass

    def compose_interested_message(self):
        interested = (1).to_bytes(4, byteorder='big') + (2).to_bytes(1, byteorder='big')
        return interested
