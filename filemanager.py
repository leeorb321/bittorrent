import math
import random
import hashlib
from queue import Queue
import time

class FileManager(object):

    RESEND_TIMEOUT = 1

    def __init__(self, torrent, to_write):
        self.torrent = torrent
        self.piece_hashes = torrent.hashes
        self.num_pieces = len(self.piece_hashes)
        self.block_size = 2**13
        self.completion_status = {i: [0]*math.ceil(torrent.piece_length/self.block_size) for i in range(self.num_pieces)}
        self.last_sizes()
        self.complete = False
        self.to_write = to_write
        self.download_queue = self.setup_download_queue()
        self.outstanding_requests = {}

    def get_block_size(self, piece, block):
        blocks_per_piece = len(self.completion_status[piece])
        if block != blocks_per_piece - 1:
            return self.block_size
        elif piece != self.num_pieces - 1:
            odd_block_size = self.torrent.piece_length % self.block_size
            return odd_block_size if odd_block_size != 0 else self.block_size
        else:
            return self.final_block_size

    def setup_download_queue(self):
        q = Queue()
        for piece in self.completion_status:
            for index, block in enumerate(self.completion_status[piece]):
                to_download = (piece, index)
                q.put(to_download)
        return q

    def get_next_block(self, peer):
        needed_pieces = [piece for piece in self.completion_status.keys() if 0 in self.completion_status[piece] ]
        if self.download_queue.qsize() == 0 and len(needed_pieces) == 0:
            if self.complete == False:
                self.download_complete()
            return None, None, None

        next_block = self.download_queue.get()
        max_tries = self.download_queue.qsize()
        counter = 0
        while next_block[0] not in set(peer.pieces):
            self.download_queue.put(next_block)
            next_block = self.download_queue.get()
            while self.completion_status[next_block[0]][next_block[1]]:
                next_block = self.download_queue.get()
            counter += 1
            if counter == max_tries: return None, None, None
        if self.download_queue.qsize() + len(self.outstanding_requests) < 20 or self.download_status() > 96:
            self.download_queue.put(next_block)

        self.outstanding_requests[next_block] = time.time()
        piece, block_index = next_block
        block_size = self.get_block_size(piece, block_index)
        return piece, block_index*self.block_size, block_size


    def download_complete(self):
        self.to_write.put((-1, 0))
        print("Download of %r complete." % self.torrent.name)
        self.complete = True

    def enqueue_outstanding_requests(self):
        for request, t0 in self.outstanding_requests.items():
            if time.time() - t0 > self.RESEND_TIMEOUT:
                self.download_queue.put(request)

    def update_status(self, piece, begin, data):
        block_index = begin // self.block_size
        if (piece, block_index) in self.outstanding_requests:
            del self.outstanding_requests[(piece, block_index)]
        if all(self.completion_status[piece]):
            return
        self.completion_status[piece][block_index] = data
        if all(self.completion_status[piece]):
            # print("Piece complete, checking hash")
            if self.validate_piece(piece) == False:
                self.handle_invalid_hash(piece)
            else:
                self.add_completed_piece(piece)

        needed_pieces = [piece for piece in self.completion_status.keys() if 0 in self.completion_status[piece] ]
        if self.download_queue.qsize() == 0 and len(needed_pieces) == 0 and self.complete == False:
            self.download_complete()

    def handle_invalid_hash(self, piece):
        self.completion_status[piece] = [0] * len(self.completion_status[piece])
        for index, _ in enumerate(self.completion_status[piece]):
            self.download_queue.put((piece, index))

    def add_completed_piece(self, piece):
        data = b''.join(self.completion_status[piece])
        self.to_write.put((piece, data))
        self.completion_status[piece] = [1] * len(self.completion_status[piece])

    def validate_piece(self, piece):
        h0 = self.piece_hashes[piece]
        piece_list = self.completion_status[piece]
        piece_bytes = b''.join(piece_list)
        h = self.get_hash(piece_bytes)
        if h != h0:
            print("%d: hashes don't match" % piece)
            return False
        return True

    def get_hash(self, piece):
        sha1 = hashlib.sha1()
        sha1.update(piece)
        return sha1.digest()

    def last_sizes(self):
        self.last_piece_size = self.torrent.length % self.torrent.piece_length
        self.num_blocks_last_piece = math.ceil(self.last_piece_size / self.block_size)
        self.final_block_size = self.last_piece_size % self.block_size
        self.completion_status[self.num_pieces-1] = [0]*self.num_blocks_last_piece

    def download_status(self):
        total = sum([len(self.completion_status[x]) for x in self.completion_status])
        complete = sum([len(self.completion_status[block]) for block in self.completion_status if 0 not in self.completion_status[block]])
        percent = (complete / total) * 100
        return percent

    def get_piece_numbers(self):
        needed_pieces = [ piece for piece in self.completion_status.keys() if 0 in self.completion_status[piece] ]
        needed = len(set(needed_pieces))
        total = self.num_pieces
        return needed, total
