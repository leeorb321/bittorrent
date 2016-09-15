import time
import os
from threading import Thread

class FileWriter(object):

    def __init__(self, torrent, to_write):
        self.torrent = torrent
        self.file_structure = torrent.file_structure
        self.to_write = to_write
        self.init_files()
        self.start()

    def init_files(self):
        print("File Structure:", self.file_structure.files)
        if not os.path.exists(self.torrent.name):
            os.makedirs(self.torrent.name)
        for file in self.file_structure.files:
            print(file)
            self.create_file(file)

    def create_file(self, file):
        dirs = file.path[:-1]
        current_path = self.file_structure.root_dir
        for folder in dirs:
            new_path = os.path.join(current_path, folder)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            current_path = new_path

        f = open(os.path.join(current_path, file.name), 'wb')
        f.seek(file.length-1)
        f.write(b'\0')
        f.close()

    def writing(self):
        while True:
            while not self.to_write.empty():
                index, data = self.to_write.get()
                if index == -1:
                    print("returned")
                    return
                self.write_piece(index, data)
            time.sleep(0.05)

    def get_file_by_index(self, byte_index):
        location = 0
        for file_index, file in enumerate(self.file_structure.files):
            location += file.length
            if location > byte_index:
                return file_index

    def get_files_to_write(self, index, data):
        byte_index = index * self.torrent.piece_length
        file_index = self.get_file_by_index(byte_index)
        current_file = self.file_structure.files[file_index]
        space_left_in_file = current_file.length - (byte_index - current_file.offset)
        if len(data) > space_left_in_file:
            data1 = data[:space_left_in_file]
            data2 = data[space_left_in_file:]
            next_file = self.file_structure.files[file_index+1]
            return [(current_file, data1, byte_index - current_file.offset), (next_file, data2, 0)]

        return [(current_file, data, byte_index - current_file.offset)]

    def write_piece(self, index, data):
        files = self.get_files_to_write(index, data)

        for file, data_to_write, offset in files:
            f = open(os.path.join(self.file_structure.root_dir, *file.path), 'rb+')
            f.seek(offset)
            f.write(data_to_write)
            f.close()

    def start(self):
        self.t = Thread(target=self.writing)
        self.t.start()
