import socket
from manage import Connection

class Peer(object):

    def __init__(self, bin_string):
        self.parse_bin(bin_string)
        self.pieces = set()
        self.interested = False
        self.s = None

    def parse_bin(self, bin_str):
        self.ip = '.'.join([str(x) for x in bin_str[:4]])
        self.port = int.from_bytes(bin_str[4:], byteorder='big')

    def add_piece(self, piece):
        self.pieces.add(piece)

    def add_from_bitfield(self, message):
        for piece in message:
            self.add_piece(piece)

    def connection(self):
        if not self.s:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(Connection.TIMEOUT)
            try:
                self.s.connect((self.ip, self.port))
            except (ConnectionRefusedError, socket.timeout, BrokenPipeError) as e:
                print("Error connecting: %r" % e)
                return False
        return self.s
