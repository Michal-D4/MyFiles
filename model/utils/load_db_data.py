# model/utils/load_db_data.py

import os
from model.helpers import *
from controller.places import Places

FIND_PART_PATH = '''select ParentID
    from Dirs where Path like :newPath and PlaceId = :place;'''

FIND_EXACT_PATH = '''select DirID, Path
    from Dirs where Path = :newPath and PlaceId = :place;'''

CHANGE_PARENT_ID = '''update Dirs set ParentID = :newId
 where ParentID = :currId and Path like :newPath and DirID != :newId;'''

FIND_FILE = 'select * from Files where DirID = :dir_id and FileName = :file;'

INSERT_DIR = '''insert into Dirs
    (Path, ParentID, PlaceId)
    values (:path, :id, :placeId);'''

INSERT_FILE = '''insert into Files
    (DirID, FileName, ExtID, PlaceId, Size)
    values (:dir_id, :file, :ext_id, :placeId, 0);'''

FIND_EXT = '''select ExtID
    from Extensions where Extension = ?;'''

# Groups will be created manually and then GroupID will be updated TODO
INSERT_EXT = '''insert into Extensions
    (Extension, GroupID) values (:ext, 0);'''


class LoadDBData:
    """
    class LoadDBData
    """
    def __init__(self, connection, current_place):
        """
        class LoadDBData
        :param connection: - connection to database
        """
        self.conn = connection
        self.cursor = self.conn.cursor()
        self.place_id = current_place[0]
        self.place_status = current_place[2]
        self.insert_current_place(current_place)

    def insert_current_place(self, current_place):
        '''
        Check existence of place in Places table and insert it if absent
        :return:  None
        '''
        place_id = self.cursor.execute('select PlaceId from Places where Place = :loc;',
                                    (current_place[1][1],)).fetchone()
        if place_id is None:
            self.cursor.execute('''insert into Places (Place, Title)
            values (:place, :title)''', current_place)
            self.place_id = self.cursor.lastrowid
            self.conn.commit()
        else:
            self.place_id = place_id[0]

    def load_data(self, data):
        """
        Load data in data base
        :param data: - iterable lines of file names with full path
        :return: None
        """
        trantab = str.maketrans(os.sep, os.altsep)
        for line in data:
            line = line.translate(trantab)
            if self.place_status == Places.MOUNTED:
                line = line.partition(os.altsep)[2]
            idx = self.insert_dir(line)
            self.insert_file(idx, line)
        self.conn.commit()

    def insert_file(self, dir_id, full_file_name):
        """
        Insert file into Files table
        :param dir_id:
        :param full_file_name:
        :return: None
        """
        file = os.path.split(full_file_name)[1]

        item = self.cursor.execute(FIND_FILE, {'dir_id': dir_id, 'file': file}).fetchone()
        if not item:
            ext_id, ext = self.insert_extension(file)

            self.cursor.execute(INSERT_FILE, {'dir_id': dir_id,
                                                  'file': file,
                                                  'ext_id': ext_id,
                                                  'placeId': self.place_id})

    def insert_extension(self, file):
        ext = get_file_extension(file)
        if ext:
            item = self.cursor.execute(FIND_EXT, (ext,)).fetchone()
            if item:
                idx = item[0]
            else:
                self.cursor.execute(INSERT_EXT, {'ext': ext})
                idx = self.cursor.lastrowid
        else:
            idx = 0
        return idx, ext

    def insert_dir(self, full_file_name):
        '''
        Insert directory into Dirs table
        :param full_file_name:
        :return: row ID of file dir
        '''
        path = full_file_name.rpartition(os.altsep)[0]
        idx, parent_path = self.search_closest_parent(path)
        if parent_path == path:
            return idx

        self.cursor.execute(INSERT_DIR, {'path': path, 'id': idx, 'placeId': self.place_id})
        idx = self.cursor.lastrowid

        self.change_parent(idx, path)
        return idx

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
        item = self.cursor.execute(FIND_PART_PATH, {'newPath': path + '%',
                                                        'place': self.place_id}).fetchone()
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
            item = self.cursor.execute(FIND_EXACT_PATH, (path, self.place_id)).fetchone()
            if item:
                res = tuple(item)
                break
            path = path.rpartition(os.altsep)[0]
        return res


if __name__ == "__main__":
    pass
