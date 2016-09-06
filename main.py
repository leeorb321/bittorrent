from parse import ParseTorrent
from torrent import Torrent
from tracker_connect import TrackerConnect
from manage import Connection

torrent = ParseTorrent('test2.torrent').parse()
tc = TrackerConnect(torrent)
info_hash = torrent.get_info_hash()
conn = Connection(tc, info_hash)

