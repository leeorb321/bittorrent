from parse import ParseTorrent
from torrent import Torrent
from tracker_connect import TrackerConnect

torrent = ParseTorrent('test.torrent').parse()
tc = TrackerConnect(torrent)

