import math
import random
import hashlib

class FileManager(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.piece_hashes = torrent.hashes
        self.num_pieces = len(self.piece_hashes)
        self.block_size = 2**13
        self.completion_status = {i: [0]*math.ceil(torrent.piece_length/self.block_size) for i in range(self.num_pieces)}
        self.last_sizes()

    def get_block_size(self, piece, block):
        blocks_per_piece = len(self.completion_status[piece])
        if block != blocks_per_piece - 1:
            return self.block_size
        elif piece != self.num_pieces - 1:
            odd_block_size = self.torrent.piece_length % self.block_size
            return odd_block_size if odd_block_size != 0 else self.block_size
        else:
            return self.final_block_size

    def get_next_block(self, peer):
        needed_pieces = [ piece for piece in self.completion_status.keys() if 0 in self.completion_status[piece] ]
        print("The intersection of needed and have is: %r" % (set(needed_pieces) & set(peer.pieces)))

        if len(needed_pieces) == 0:
            self.download_complete()

        for piece in (set(needed_pieces) & set(peer.pieces)):
            blocks = self.completion_status[piece]
            try:
                index = blocks.index(0)
                block_size = self.get_block_size(piece, index)
                return piece, index*self.block_size, block_size
            except:
                pass

        if len(set(needed_pieces) & set(peer.pieces)) == 0:
            return None, None, None

    def download_complete(self):
        print("download complete")
        for piece, chunks in self.completion_status.items():
            self.validate_piece(piece)
        self.write_to_file()

    def update_status(self, piece, begin, data):
        block_index = begin // self.block_size
        self.completion_status[piece][block_index] = data
        if all(self.completion_status[piece]):
            print("Piece complete, checking hash")
            if not self.validate_piece(piece):
                self.completion_status[piece] == [0] * len(piece)

    def validate_piece(self, piece):
        h0 = self.piece_hashes[piece]
        piece_list = self.completion_status[piece]
        piece_bytes = b''.join(piece_list)
        h = self.get_hash(piece_bytes)
        if h != h0:
            print("%d: hashes don't match" % piece)
            return False
        print("%d: hashes match!"%piece)
        return True

    def get_hash(self, piece):
        sha1 = hashlib.sha1()
        sha1.update(piece)
        return sha1.digest()

    def write_to_file(self):
        f = open('test.epub', 'wb')
        for piece, blocks in self.completion_status.items():
            block_bytes = b''.join(blocks)
            f.write(block_bytes)
        f.close()

    def last_sizes(self):
        self.last_piece_size = self.torrent.length % self.torrent.piece_length
        self.num_blocks_last_piece = math.ceil(self.last_piece_size / self.block_size)
        self.final_block_size = self.last_piece_size % self.block_size
        self.completion_status[self.num_pieces-1] = [0]*self.num_blocks_last_piece
