from bcoding import bencode, bdecode
from torrent import Torrent

class ParseTorrent(object):

    def __init__(self, path):
        self.path = path

    def parse(self):
        with open(self.path, 'rb') as f:
            torrent_file = bdecode(f)


        try:
            url = torrent_file['announce']
        except:
            trackers_list = []
            for tracker in torrent_file['announce-list']:
                trackers_list.append(tracker[0])

            # Use only first tracker for now
            url = trackers_list[0]

        info = torrent_file['info']
        name = info['name']
        piece_length = info['piece length']
        pieces = info['pieces']
        length = info['length'] # only exists for single-file torrents

        print("Torrent has %d pieces" % (len(pieces)//20))

        return Torrent(url, info, name, piece_length, pieces, length)
