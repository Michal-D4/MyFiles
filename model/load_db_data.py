# model/load_db_data.py

import os
from model.helper import Shared, get_file_extension, get_parent_dir

FIND_PART_PATH = 'select ParentID from Dirs where Path like :newPath;'

FIND_EXACT_PATH = 'select DirID, Path from Dirs where Path = :newPath;'

CHANGE_PARENT_ID = '''update Dirs set ParentID = :newId
 where ParentID = :currId and Path like :newPath and DirID != :newId;'''

FIND_FILE = 'select * from Files where DirID = :dir_id and FileName = :file;'

INSERT_DIR = 'insert into Dirs (Path, ParentID, isVirtual) values (:path, :id, 0);'

INSERT_FILE = 'insert into Files (DirID, FileName, ExtID) values (:dir_id, :file, :ext_id);'

FIND_EXT = 'select ExtID from Extensions where Extension = ?;'

INSERT_EXT = 'insert into Extensions (Extension, GroupID) values (:ext, 0);'


class LoadDBData:
    """
    class LoadDBData
    """
    def __init__(self):
        """
        class LoadDBData
        :param connection: - connection to database
        """
        self.conn = Shared['DB connection']
        self.cursor = self.conn.cursor()
        self.updated_dirs = set()

    def get_updated_dirs(self):
        return self.updated_dirs

    def load_data(self, path_, ext_):
        """
        Load data in data base
        :param data: - iterable lines of file names with full path
        :return: None
        """
        files = LoadDBData._yield_files(path_, ext_)
        trantab = str.maketrans(os.sep, os.altsep)
        for line in files:
            path = os.path.dirname(line)
            idx = self.insert_dir(path)
            self.updated_dirs.add(str(idx))
            self.insert_file(idx, line)
        self.conn.commit()

    def insert_file(self, dir_id, full_file_name):
        """
        Insert file into Files table
        :param dir_id:
        :param full_file_name:
        :return: None
        """
        file_ = os.path.basename(full_file_name)

        item = self.cursor.execute(FIND_FILE, {'dir_id': dir_id, 'file': file_}).fetchone()
        if not item:
            ext_id, ext = self.insert_extension(file_)
            if ext_id > 0:      # files with an empty extension are not handled
                self.cursor.execute(INSERT_FILE, {'dir_id': dir_id,
                                                  'file': file_,
                                                  'ext_id': ext_id})

    def insert_extension(self, file):
        ext = get_file_extension(file)
        if ext:
            item = self.cursor.execute(FIND_EXT, (ext,)).fetchone()
            if item:
                idx = item[0]
            else:
                self.cursor.execute(INSERT_EXT, {'ext': ext})
                idx = self.cursor.lastrowid
                self.conn.commit()
        else:
            idx = 0
        return idx, ext

    def insert_dir(self, path):
        '''
        Insert directory into Dirs table
        :param path:
        :return: row ID of file dir
        '''
        idx, parent_path = self.search_closest_parent(path)
        if parent_path == path:
            return idx, False

        self.cursor.execute(INSERT_DIR, {'path': path, 'id': idx})
        idx = self.cursor.lastrowid

        self.change_parent(idx, path)
        self.conn.commit()
        return idx, True

    def change_parent(self, new_parent_id, path):
        old_parent_id = self.parent_id_for_child(path)
        if old_parent_id != -1:
            self.cursor.execute(CHANGE_PARENT_ID, {'currId': old_parent_id,
                                                       'newId': new_parent_id,
                                                       'newPath': path + '%'})

    def parent_id_for_child(self, path):
        '''
        Check the new file path:
          if it can be parent for other directories
        :param path:
        :return: parent Id of first found child, -1 if not children
        '''
        item = self.cursor.execute(FIND_PART_PATH, {'newPath': path + '%'}).fetchone()
        if item:
            idx = item[0]
        else:
            idx = -1

        return idx

    def search_closest_parent(self, path):
        '''
        Search parent directory
        :param path:  file path
        :return:  tuple of ID and path of parent directory or (0, '')
        '''
        res = (0, '')
        while path:
            item = self.cursor.execute(FIND_EXACT_PATH, (path)).fetchone()
            if item:
                res = tuple(item)
                break
            path = get_parent_dir(path)
        return res

    @staticmethod
    def _yield_files(root, extensions):
        """
        generator of file list
        :param root: root directory
        :param extensions: list of extensions
        :return: generator
        """
        ext_ = tuple(x.strip('. ') for x in extensions.split(','))
        for dir_name, _, file_names in os.walk(root):
            if (not extensions) | (extensions == '*'):
                for filename in file_names:
                    yield os.path.join(dir_name, filename)
            else:
                for filename in file_names:
                    if get_file_extension(filename) in ext_:
                        yield os.path.join(dir_name, filename)


if __name__ == "__main__":
    pass
