import os

class File(object):

    def __init__(self, length, path, offset):
        self.length = length
        self.path = path
        self.name = self.path[-1]
        self.offset = offset

    def __repr__(self):
        return os.path.join(*self.path)

class FileStructure(object):

    def __init__(self, root_dir, files):
        self.root_dir = os.path.join(os.getcwd(), 'Downloads', root_dir)
        self.files = files

