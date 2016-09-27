import time
import os
from threading import Thread

class FileWriter(object):

    def __init__(self, torrent, to_write, file_manager):
        self.torrent = torrent
        self.cwd = os.getcwd()
        self.file_structure = torrent.file_structure
        self.to_write = to_write
        self.written = self.get_written()
        self.file_manager = file_manager
        self.init_files()
        self.start()

    def init_files(self):
        if self.written == []:
            print("File Structure:", self.file_structure.files)
            if not os.path.exists(os.path.join(self.cwd, 'Downloads', self.torrent.name)):
                os.makedirs(os.path.join('./Downloads', self.torrent.name))
            for file in self.file_structure.files:
                print(file)
                self.create_file(file)
            self.create_status_file()

    def get_written(self):
        file_name = self.torrent.name + "_status.txt"
        file_path = os.path.join(self.cwd, 'Downloads', self.torrent.name, file_name)
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r') as f:
            status_bit_vector = f.read().strip()
        written = [i for i, char in enumerate(status_bit_vector) if char == "1"]
        print(written)
        return written

    def create_status_file(self):
        file_name = self.torrent.name + "_status.txt"
        file_path = os.path.join(self.cwd, 'Downloads', self.torrent.name, file_name)
        if not os.path.exists(file_path):
            print("creating new status file")
            f = open(file_path, "w")
            f.seek(len(self.torrent.hashes))
            f.write('\0')
            f.close()

    def update_status_file(self):
        num_pieces = len(self.torrent.hashes)
        self.completed_bit_vector = "".join(["1" if i in self.written else "0" for i in range(num_pieces)])
        file_name = self.torrent.name + "_status.txt"
        self.status_file_path = os.path.join(self.cwd, 'Downloads', self.torrent.name, file_name)
        f = open(self.status_file_path, "w")
        f.write(self.completed_bit_vector)
        f.close()

    def create_file(self, file):
        dirs = file.path[:-1]
        current_path = self.file_structure.root_dir
        for folder in dirs:
            new_path = os.path.join(self.cwd, 'Downloads', current_path, folder)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            current_path = new_path

        f = open(os.path.join(self.cwd, 'Downloads', current_path, file.name), 'wb')
        f.seek(file.length-1)
        f.write(b'\0')
        f.close()

    def writing(self):
        while True:
            while not self.to_write.empty():
                index, data = self.to_write.get()
                if index == -1:
                    file_name = self.torrent.name + "_status.txt"
                    file_path = os.path.join(self.cwd, 'Downloads', self.torrent.name, file_name)
                    os.remove(file_path)
                    return
                self.write_piece(index, data)
            self.update_status_file()
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

        self.written.append(index)

    def start(self):
        self.t = Thread(target=self.writing)
        self.t.start()
