from bcoding import bencode, bdecode
from torrent import Torrent
from fileinfo import File, FileStructure

class ParseTorrent(object):

    def __init__(self, path):
        self.path = path

    def parse(self):
        with open(self.path, 'rb') as f:
            torrent_file = bdecode(f)

        urls = []
        if 'announce' in torrent_file:
            urls.append(torrent_file['announce'])
        if 'announce-list' in torrent_file:
            for tracker in torrent_file['announce-list']:
                urls.append(tracker[0])

        info = torrent_file['info']
        name = info['name']
        piece_length = info['piece length']
        pieces = info['pieces']

        if 'length' in info:
            length = info['length'] # only exists for single-file torrents
            file_list = [File(length, [name], 0)]
        else:
            files = info['files']
            file_list = []
            offset = 0
            for file in files:
                file_list.append(File(file['length'], file['path'], offset))
                offset += file['length']

        target = FileStructure(name, file_list)


        print("Torrent has %d pieces" % (len(pieces)//20))
        print("Torrent piece length = %d"%int(piece_length))
        # print("Torrent has %d bytes" % length)

        return Torrent(urls, info, piece_length, pieces, target)
