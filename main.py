import sys
from parse import ParseTorrent
from torrent import Torrent
from tracker_connect import TrackerConnect
from manage import Connection
from filemanager import FileManager


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('No torrent file specified.\nUsage: "python main.py <torrent filename>"')
        sys.exit(1)
    else:
        filename = sys.argv[1]
    torrent = ParseTorrent(filename).parse()
    tc = TrackerConnect(torrent)
    conn = Connection(tc, torrent)
