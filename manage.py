import socket

class Connection(object):

    def __init__(self, tracker_response, info_hash):
        self.tc = tracker_response
        self.num_peers = len(self.tc.resp['peers'])
        self.interval = self.tc.resp['interval']
        self.info_hash = info_hash
        peers = self.tc.resp['peers']

        self.handshake = self.create_handshake()

        k = list(peers.keys())
        self.initial_connection(peers[k[0]])

    def create_handshake(self):
        pstrlen = bytes([19])
        pstr = b'BitTorrent protocol'
        reserved = b'\0' * 8
        info_hash = self.info_hash
        peer_id = self.tc.peer_id

        return pstrlen + pstr + reserved + info_hash + peer_id

    def initial_connection(self, peer):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer.ip, peer.port))
        sent = s.send(self.handshake)

        if self.validate_hash(s.recv(sent)) == False:
            pass
            # remove from peer list
        else:
            self.send_message(peer)


    def validate_hash(self, response):
        prefix = response[0]
        return response[prefix + 1 + 8:-20] == self.info_hash

    def send_message(self, peer):
        interested = (1).to_bytes(4, byteorder='big') + (2).to_bytes(1, byteorder='big')
        req = (13).to_bytes(4, byteorder='big') + (6).to_bytes(1, byteorder='big') + (0).to_bytes(4, byteorder='big') +(0).to_bytes(4, byteorder='big') + (2**15).to_bytes(4, byteorder='big')

