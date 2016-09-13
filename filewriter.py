import time
from threading import Thread

class FileWriter(object):

    def __init__(self, torrent, to_write):
        self.torrent = torrent
        self.to_write = to_write
        self.init_file()
        self.start()

    def init_file(self):
        f = open(self.torrent.name, 'wb')
        f.seek(self.torrent.length-1)
        f.write(b'\0')
        f.close()

    def writing(self):
        while True:
            while not self.to_write.empty():
                index, data = self.to_write.get()
                if index == -1:
                    return
                self.write_piece(index, data)
            time.sleep(0.05)

    def write_piece(self, index, data):
        print("Current piece:",index)
        f = open(self.torrent.name, 'rb+')
        f.seek(self.torrent.piece_length * index)
        f.write(data)
        f.close()

    def start(self):
        self.t = Thread(target=self.writing)
        self.t.start()

