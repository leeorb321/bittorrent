import socket
import re
import requests
import random
from os import urandom
import os.path
from bcoding import bencode, bdecode
from peer import Peer

class TrackerConnect(object):

    '''Class to connect to torrent tracker and get peer info.'''

    def __init__(self, torrent):
        self.torrent = torrent
        self.info_hash = torrent.get_info_hash()
        self.peer_id = urandom(20)
        self.port = 6881
        self.uploaded = 0
        self.downloaded = 0
        self.left = torrent.length - self.downloaded
        self.resp = self.get_tracker(event='started')

    def generate_payload(self, event):
        return {'info_hash': self.info_hash,
                    'peer_id': self.peer_id,
                    'port': self.port,
                    'uploaded': self.uploaded,
                    'downloaded': self.downloaded,
                    'left': self.left,
                    'event': event
                }

    def get_tracker(self, event):
        max_tracker_attempts = 3
        counter = 0
        main_counter = 0
        response = {}
        for tracker_url in self.torrent.tracker_urls:
            counter = 0
            tracker_response = False
            while not tracker_response and counter < max_tracker_attempts:
                tracker_response = self.try_next_tracker(counter, event)
                counter += 1
                main_counter += 1
            if 'peers' not in response:
                response['peers'] = {}

            if tracker_response:
                if 'interval' not in response:
                    response['interval'] = tracker_response['interval']
                else:
                    response['interval'] = max(response['interval'], tracker_response['interval'])

                for key, peer in tracker_response['peers'].items():
                    if peer.ip not in response['peers']:
                        response['peers'][peer.ip] = peer
                tracker_response = False

            if main_counter == max_tracker_attempts*len(self.torrent.tracker_urls):
                print("No working trackers found.")

        return response

    def try_next_tracker(self, counter, event):
        url = self.torrent.tracker_urls[counter%len(self.torrent.tracker_urls)]
        return self.send_request(event, url)

    def send_request(self, event, url):
        print("Sending request to tracker ...")
        if url.startswith('http'):
            return self._send_http_request(event, url)
        elif url.startswith('udp'):
            return self._send_udp_request(event, url)

    def _send_http_request(self, event, url):
        payload = self.generate_payload(event)
        try:
            r = requests.get(url, params=payload, timeout=1)
            resp = bdecode(bytes(r.text, 'ISO-8859-1'))
            peers = resp['peers']
            peers_dict = {}

            print("HTTP tracker response received ...")
            for i in range(0, len(peers), 6):
                if peers[i:i+6] not in peers_dict:
                    peers_dict[peers[i:i+6]] = Peer(peers[i:i+6])

            resp['peers'] = peers_dict

            print("List of %d peers received" % len(resp['peers']))

            return resp

        except (ConnectionResetError, ConnectionError) as e:
            return False


    def _send_udp_request(self, event, url):
        s_tracker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_tracker.settimeout(1)
        addr, port = self.parse_udp_url(url)

        msg, txn_id = self.udp_connection_request()

        try:
            s_tracker.sendto(msg, (addr, int(port)))
            response, _ = s_tracker.recvfrom(2048)
            print("UDP tracker response received ...")
            print("Length of response:", len(response))
        except:
            print("UDP tracker failed:", url)
            return False

        if len(response) >= 16:
            action_resp = int.from_bytes(response[:4], byteorder='big')
            txn_id_resp = int.from_bytes(response[4:8], byteorder='big')
            conn_id_resp = int.from_bytes(response[8:], byteorder='big')
            if txn_id_resp != txn_id or action_resp != 0:
                return False
        else:
            return False

        # Send announce message
        client_port = s_tracker.getsockname()[1]

        events = {
            'none': 0,
            'completed': 1,
            'started': 2,
            'stopped': 3
        }

        return self.send_udp_announce(response[8:], client_port, events[event], addr, port, s_tracker)

    def send_udp_announce(self, conn_id, client_port, event, addr, port, s_tracker):
        msg, txn_id = self.compose_udp_announce(conn_id, client_port, event)

        s_tracker.sendto(msg, (addr, int(port)))

        print("Announce request sent ...")
        response, tracker_addr = s_tracker.recvfrom(4096)
        print("Length of response:", len(response))

        if len(response) >= 20:
            resp = {}

            resp['action'] = int.from_bytes(response[:4], byteorder='big')
            resp['txn_id'] = int.from_bytes(response[4:8], byteorder='big')
            resp['interval'] = int.from_bytes(response[8:12], byteorder='big')
            resp['leechers'] = int.from_bytes(response[12:16], byteorder='big')
            resp['seeders'] = int.from_bytes(response[16:20], byteorder='big')

            if resp['action'] != 1:
                print("Response action type is not 'announce.'")
                return False
            if resp['txn_id'] != txn_id:
                print("Transaction IDs do not match.")
                return False

            peers_dict = {}
            for i in range(20, len(response)-6, 6):
                if response[i:i+6] not in peers_dict:
                    peers_dict[response[i:i+6]] = Peer(response[i:i+6])

            resp['peers'] = peers_dict

            print("List of %d peers received" % len(resp['peers']))

            return resp

        else:
            return False

    def parse_udp_url(self, url):
        port_ip = re.match(r'^udp://(.+):(\d+)', url).groups()
        return port_ip[0], port_ip[1]

    def udp_connection_request(self):
        conn_id = 0x41727101980 # default, required initial value to identify the protocol
        action = 0x0 # 0 for connection request
        txn_id = int(random.randrange(0, 2**32 - 1))
        msg = conn_id.to_bytes(8, byteorder='big') + action.to_bytes(4, byteorder='big') + \
                txn_id.to_bytes(4, byteorder='big')

        return msg, txn_id

    def compose_udp_announce(self, conn_id, port, event):
        action = 1
        txn_id = int(random.randrange(0, 2**31 - 1))
        ip = 0
        key = int(random.randrange(0, 2**31 - 1))
        num_want = 2**17

        msg = conn_id + action.to_bytes(4, byteorder='big') + txn_id.to_bytes(4, byteorder='big') + \
                self.info_hash + self.peer_id + self.downloaded.to_bytes(8, byteorder='big') + \
                self.left.to_bytes(8, byteorder='big') + self.uploaded.to_bytes(8, byteorder='big') + \
                event.to_bytes(4, byteorder='big') + ip.to_bytes(4, byteorder='big') + \
                key.to_bytes(4, byteorder='big') + num_want.to_bytes(4, byteorder='big') + port.to_bytes(2, byteorder='big')

        return msg, txn_id
