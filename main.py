from parse import ParseTorrent
from torrent import Torrent
from tracker_connect import TrackerConnect
from manage import Connection
from filemanager import FileManager

torrent = ParseTorrent('temp.torrent').parse()
tc = TrackerConnect(torrent)
info_hash = torrent.get_info_hash()
f_manager = FileManager(torrent)
conn = Connection(tc, info_hash, f_manager)
