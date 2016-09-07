import hashlib

class FileManager(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.piece_length = torrent.piece_length
        self.piece_hashes = torrent.hashes
        self.num_pieces = len(self.piece_hashes)
        self.block_size = 2**14
        self.completion_status = {i: [0]*(self.piece_length//self.block_size) for i in range(self.num_pieces)}

    def get_next_block(self):
        for piece, blocks in self.completion_status.items():
            try:
                index = blocks.index(0)
                return piece, index*self.block_size
            except:
                pass
        self.download_complete()

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
            self.validate_piece(piece)

    def validate_piece(self, piece):
        h0 = self.piece_hashes[piece]
        piece_list = self.completion_status[piece]
        piece_bytes = b''.join(piece_list)
        h = self.get_hash(piece_bytes)
        if h != h0:
            print("hashes don't match")
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
