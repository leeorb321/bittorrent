class Peer(object):

    def __init__(self, bin_string):
        self.parse_bin(bin_string)

    def parse_bin(self, bin_str):
        self.ip = '.'.join([str(x) for x in bin_str[:4]])
        self.port = int.from_bytes(bin_str[4:], byteorder='big')

