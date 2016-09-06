class Torrent(object):

    def __init__(self, url, name, piece_length, pieces, length):
        self.url = url
        self.name = name
        self.piece_length = piece_length
        self.pieces = pieces
        self.length = length
        self.hashes = self.get_pieces()

    def get_pieces(self):
        return [ self.pieces[20*i:20*(i+1)] for i in range(len(self.pieces)//20) ]
