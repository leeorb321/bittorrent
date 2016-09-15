from bcoding import bencode, bdecode
from torrent import Torrent

class ParseTorrent(object):

    def __init__(self, path):
        self.path = path

    def parse(self):
        with open(self.path, 'rb') as f:
            torrent_file = bdecode(f)

        urls = []
        try:
            urls.append(torrent_file['announce'])
        except:
            pass
        try:
            for tracker in torrent_file['announce-list']:
                urls.append(tracker[0])
        except:
            pass

        info = torrent_file['info']
        name = info['name']
        piece_length = info['piece length']
        pieces = info['pieces']
        length = info['length'] # only exists for single-file torrents

        print("Torrent has %d pieces" % (len(pieces)//20))
        print("Torrent piece length = %d"%int(piece_length))
        print("Torrent has %d bytes" % length)

        return Torrent(urls, info, name, piece_length, pieces, length)
