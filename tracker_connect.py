import requests
from os import urandom
import os.path
from bcoding import bencode, bdecode
from peer import Peer

class TrackerConnect(object):
    # Class to connect to torrent tracker and get peer info
    def __init__(self, torrent):
        self.torrent = torrent
        self.info_hash = torrent.get_info_hash()
        self.peer_id = urandom(20)
        self.port = 6881
        self.uploaded = 0
        self.downloaded = 0
        self.left = torrent.length - self.downloaded
        self.resp = self.send_request(event='started')

    def generate_payload(self, event):
        return {'info_hash': self.info_hash,
                    'peer_id': self.peer_id,
                    'port': self.port,
                    'uploaded': self.uploaded,
                    'downloaded': self.downloaded,
                    'left': self.left,
                    'event': event
                }

    def send_request(self, event):
        print("Sending request to tracker ...")
        payload = self.generate_payload(event)
        r = requests.get(self.torrent.tracker_url, params=payload)
        resp = bdecode(bytes(r.text, 'ISO-8859-1'))
        peers = resp['peers']
        peers_dict = {}
        print("Tracker response received ...")
        for i in range(0, len(peers), 6):
            if peers[i:i+6] not in peers_dict:
                peers_dict[peers[i:i+6]] = Peer(peers[i:i+6])

        resp['peers'] = peers_dict
        return resp
