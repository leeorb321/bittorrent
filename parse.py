from bcoding import bencode, bdecode
from torrent import Torrent

class ParseTorrent(object):

    def __init__(self, path):
        self.path = path

    def parse(self):
        with open(self.path, 'rb') as f:
            torrent_file = bdecode(f)

        url = torrent_file['announce']
        info = torrent_file['info']
        name = info['name']
        piece_length = info['piece length']
        pieces = info['pieces']
        length = info['length'] # only exists for single-file torrents

        return Torrent(url, info, name, piece_length, pieces, length)
