class Peer(object):

    def __init__(self, bin_string):
        self.parse_bin(bin_string)
        self.pieces = set()

    def parse_bin(self, bin_str):
        self.ip = '.'.join([str(x) for x in bin_str[:4]])
        self.port = int.from_bytes(bin_str[4:], byteorder='big')

    def add_piece(self, piece):
        self.pieces.add(piece)

    def add_from_bitfield(self, message):
        for piece in message:
            self.add_piece(piece)


