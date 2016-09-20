import stacktracer
from parse import ParseTorrent
from torrent import Torrent
from tracker_connect import TrackerConnect
from manage import Connection
from filemanager import FileManager

stacktracer.trace_start("trace.html",interval=5,auto=True)

torrent = ParseTorrent('multifile.torrent').parse()
tc = TrackerConnect(torrent)
conn = Connection(tc, torrent)
