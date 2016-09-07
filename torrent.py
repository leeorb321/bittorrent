import hashlib
from bcoding import bencode

class Torrent(object):
    # Class containing information about a torrent given in the torrent file
    def __init__(self, url, info, name, piece_length, pieces, length):
        self.tracker_url = url
        self.name = name
        self.piece_length = piece_length
        self.pieces = pieces
        self.length = length
        self.hashes = self.get_pieces()
        self.info_hash = self.hash_info(info)

    def get_pieces(self):
        return [ self.pieces[20*i:20*(i+1)] for i in range(len(self.pieces)//20) ]

    def hash_info(self, info):
        info_bytes = bencode(info)
        sha1 = hashlib.sha1()
        sha1.update(info_bytes)
        return sha1.digest()

    def get_info_hash(self):
        return self.info_hash
