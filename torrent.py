import hashlib
from bcoding import bencode

class Torrent(object):
    # Class containing information about a torrent given in the torrent file
    def __init__(self, urls, info, piece_length, pieces, file_structure):
        self.tracker_urls = urls
        print(urls)
        self.name = file_structure.root_dir
        self.piece_length = piece_length
        self.pieces = pieces
        self.file_structure = file_structure
        self.hashes = self.get_pieces()
        self.info_hash = self.hash_info(info)

        self.length = sum([ file.length for file in file_structure.files ])

    def get_pieces(self):
        return [ self.pieces[20*i:20*(i+1)] for i in range(len(self.pieces)//20) ]

    def hash_info(self, info):
        info_bytes = bencode(info)
        sha1 = hashlib.sha1()
        sha1.update(info_bytes)
        x = sha1.digest()
        return x

    def get_info_hash(self):
        return self.info_hash
