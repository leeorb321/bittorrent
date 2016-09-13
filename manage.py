import socket
import random
import time
from queue import Queue
from threading import Thread, Lock

from filemanager import FileManager
from filewriter import FileWriter

class Connection(object):
    # Class to manage connections with peers
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

    MAX_CONNECTIONS = 10

    def __init__(self, tracker_response, torrent):
        self.tc = tracker_response
        self.info_hash = torrent.get_info_hash()
        self.num_peers = len(self.tc.resp['peers'])
        self.interval = self.tc.resp['interval']
        self.handshake = self.create_handshake()
        self.current_connections = []

        self.to_write = Queue()
        self.threads = {}
        self.peerlist_lock = Lock()
        self.file_lock = Lock()
        self.file_manager = FileManager(torrent, self.to_write)
        self.file_writer = FileWriter(torrent, self.to_write)

        self.download_file()

    def create_handshake(self):
        print("Creating handshake message ...")
        pstrlen = bytes([19])
        pstr = b'BitTorrent protocol'
        reserved = b'\0' * 8
        info_hash = self.info_hash
        peer_id = self.tc.peer_id
        return pstrlen + pstr + reserved + info_hash + peer_id

    def get_peers(self):
        index = 0
        while len(self.current_connections) < self.MAX_CONNECTIONS and not self.file_manager.complete and self.available_peers != []:
            peer = self.available_peers[index%len(self.available_peers)]
            self.available_peers.remove(peer)
            print("Checking peer:", peer)
            if peer not in self.current_connections:
                self.start(peer)
            index += 1

    def download_file(self):
        peers = self.tc.resp['peers']
        self.available_peers = list(peers.values())
        random.shuffle(self.available_peers)

        self.get_peers()
        self.start_maintain_peerlist()

    def start_maintain_peerlist(self):
        t = Thread(target=self.maintain_peers)
        t.start()

    def maintain_peers(self):
        while True:
            print("There are %r current connections and %r available peers." % (len(self.current_connections), len(self.available_peers)))
            print("Download is %r complete." % self.file_manager.download_status())
            for i, peer in enumerate(self.current_connections):
                print("Connection #%d: %r" % (i, peer))
            if self.available_peers == [] and not self.file_manager.complete:
                peers = self.tc.resp['peers']
                self.available_peers = list(peers.values())
                random.shuffle(self.available_peers)

            self.get_peers()
            if self.file_manager.complete:
                return
            time.sleep(1)

    def start(self, peer):
        print("Starting peer ...")
        self.peerlist_lock.acquire()
        try:
            self.current_connections.append(peer)
        finally:
            self.peerlist_lock.release()

        self.threads[peer] = Thread(target=self.connect_to_peer, args=(peer,))
        self.threads[peer].start()

    def connect_to_peer(self, peer):
        s = peer.connection()
        if s:
            print("Established socket connection for next peer")
            if self.initial_connection(peer):
                self.wait_for_response(peer)
        else:
            self.close_peer_connection(peer)
        return

    def initial_connection(self, peer):
        r = self.send_handshake(peer)
        s = peer.connection()
        if r is not None and len(r) > 0:
            if self.validate_hash(r) == False:
                print("Hash invalid")
                self.close_peer_connection(peer)
                return False
            else:
                print("Hash valid")
                return True
        else:
            self.close_peer_connection(peer)
            return False

    def send_handshake(self, peer):
        s = peer.connection()
        message = self.handshake
        try:
            sent = s.send(message)
            return self.wait_for_handshake(peer)
        except (ConnectionRefusedError, socket.timeout, BrokenPipeError, ConnectionResetError) as e:
            print("Error connecting: %r" % e)
            self.close_peer_connection(peer)
            return None

    def wait_for_handshake(self, peer):
        s = peer.connection()
        r0 = s.recv(1)
        expected_length = int.from_bytes(r0, byteorder = 'big') + 49
        print("Handshake received with length %d" % expected_length)
        bytes_received = len(r0)
        received_from_tracker = r0

        if bytes_received == 0:
            return received_from_tracker

        while bytes_received < expected_length:
            print("Reading bytes - received %d out of %d bytes so far" % (bytes_received, expected_length))
            bytes_read = s.recv(expected_length - bytes_received)

            if len(bytes_read) == 0:
                return received_from_tracker

            bytes_received += len(bytes_read)
            received_from_tracker += bytes_read
        if s:
            s.settimeout(None)
        return received_from_tracker

    def validate_hash(self, response):
        print("Validating hash for message")
        prefix = response[0]
        return response[prefix + 1 + 8:-20] == self.info_hash

    def send_message(self, peer, message):
        s = peer.connection()
        sent = s.send(message)
        if sent < 0:
            self.close_peer_connection(peer)
            return False
        else:
            return True

    def wait_for_response(self, peer):
        print("Message sent - waiting for response")
        s = peer.connection()

        msg_len = 1
        while msg_len != 0 and self.file_manager.complete == False:
            print ("Reading bytes ...")
            try:
                msg_len = int.from_bytes(s.recv(4), byteorder='big')
                msg_len = max(msg_len, 1)
            except:
                self.close_peer_connection(peer)
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
            print("Received message with id:", int.from_bytes(msg_id, byteorder='big'))
            handler(peer, received_from_peer)

        if msg_len == 1:
            self.close_peer_connection(peer)
            return False
        else:
            return received_from_peer

    def request_next_block(self, peer):
        self.file_lock.acquire()
        try:
            next_index, next_begin, block_length = self.file_manager.get_next_block(peer)
        finally:
            self.file_lock.release()
        print("Next index, next begin:", next_index, next_begin)
        if next_index != None:
            msg = self.compose_request_message(next_index, next_begin, block_length)
            self.send_message(peer, msg)
        else:
            self.close_peer_connection(peer)

    def handle_choke(self, peer, message):
        print("Choked")
        self.close_peer_connection(peer)

    def handle_unchoke(self, peer, message):
        print("Unchoked")
        self.request_next_block(peer)

    def handle_interested(self, peer, message):
        pass

    def handle_not_interested(self, peer, message):
        pass

    def handle_have(self, peer, message):
        print("Message type is 'have'")
        piece = int.from_bytes(message, byteorder='big')
        print(piece)
        peer.add_piece(piece)

        if peer.interested == False:
            interested_msg = self.compose_interested_message()
            peer_resp = self.send_message(peer, interested_msg)
            if peer_resp:
                peer.interested = True

        return True

    def handle_bitfield(self, peer, message):
        print("Message type is 'bitfield'")
        pieces = bin(int.from_bytes(message, byteorder='big'))[2:]
        available_indices = [i for i in range(len(pieces)) if pieces[i] == '1']
        peer.add_from_bitfield(available_indices)

        if peer.interested == False:
            interested_msg = self.compose_interested_message()
            peer_resp = self.send_message(peer, interested_msg)
            if peer_resp:
                peer.interested = True

        return True

    def handle_request(self, peer, message):
        pass

    def handle_piece(self, peer, message):
        index = int.from_bytes(message[:4], byteorder='big')
        begin = int.from_bytes(message[4:8], byteorder='big')
        block = message[8:]
        print("Received block of length: %d" % len(block))
        self.file_manager.update_status(index, begin, block)
        self.request_next_block(peer)

    def handle_cancel(self, peer, message):
        pass

    def handle_port(self, peer, message):
        pass

    def compose_interested_message(self):
        interested = (1).to_bytes(4, byteorder='big') + (2).to_bytes(1, byteorder='big')
        return interested

    def compose_request_message(self, index, begin, length):
        print("Requesting block of length", length)
        req = (13).to_bytes(4, byteorder='big') + (6).to_bytes(1, byteorder='big') + \
            (index).to_bytes(4, byteorder='big') +(begin).to_bytes(4, byteorder='big') + \
            (length).to_bytes(4, byteorder='big')
        return req

    def close_peer_connection(self, peer):
        self.peerlist_lock.acquire()
        try:
            self.current_connections.remove(peer)
        finally:
            self.peerlist_lock.release()
        del self.threads[peer]
        self.available_peers.append(peer)
        peer.shutdown()
