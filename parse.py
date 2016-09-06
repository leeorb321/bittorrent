from bcoding import bencode, bdecode
from torrent import Torrent


class ParseTorrent(object):

    def __init__(self, path):
        self.path = path
        self.parse()

    def parse(self):
        with open(self.path, 'rb') as f:
            torrent = bdecode(f)

        url = torrent['announce']
        info = torrent['info']
        name = info['name']
        piece_length = info['piece length']
        pieces = info['pieces']
        length = info['length'] # only exists for single-file torrents

        return Torrent(url, name, piece_length, pieces, length)
