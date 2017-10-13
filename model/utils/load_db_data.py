import os

SQL_FIND_PART_PATH = '''select ParentID
    from Dirs where Path like :newPath and myPlaceId = :place;'''

SQL_FIND_EXACT_PATH = '''select DirID, Path
    from Dirs where Path = :newPath and myPlaceId = :place;'''

SQL_CHANGE_PARENT_ID = '''update Dirs set ParentID = :newId 
where ParentID = :currId and Path like :newPath and DirID != :newId;'''

SQL_FIND_FILE = '''select *
    from Files where DirID = :dir_id and FileName = :file;'''

SQL_INSERT_DIR = '''insert into Dirs
    (Path, ParentID, myPlaceId)
    values (:path, :id, :placeId);'''

SQL_INSERT_FILE = '''insert into Files
    (DirID, FileName, ExtID)
    values (:dir_id, :file, :ext_id);'''

SQL_FIND_EXT = '''select ExtID
    from Extensions where Extension = ?;'''

# Groups will be created manually and then GroupID will be updated TODO
SQL_INSERT_EXT = '''insert into Extensions
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
        self.set_current_place(current_place)

    def set_current_place(self, current_place):
        '''
        Check existence of place in myPlaces table and insert it if absent
        :return:  None
        '''
        count = self.cursor.execute('select count(*) from myPlaces where myPlaceId = :locID;',
                                   (self.place_id,)).fetchone()
        if count[0] == 0:
            self.cursor.execute('''insert into myPlaces (myPlaceId, myPlace, Title)
            values (:id, :place, :title)''', current_place)
            self.conn.commit()

    def load_data(self, data):
        """
        Load data in data base
        :param data: - iterable lines of file names with full path
        :return: None
        """
        for line in data:
            # print(line)
            ii = self.insert_dir(line)
            self.insert_file(ii, line)
        self.conn.commit()

    def insert_file(self, ii, line):
        """
        Insert file into Files table
        :param ii:
        :param line:
        :return: None
        """
        # TODO add additional data: creation date, size, page number.
        file = line.rpartition(os.sep)[2]

        rr = self.cursor.execute(SQL_FIND_FILE, {'dir_id': ii, 'file': file}).fetchone()
        if not rr:
            jj = self.insert_extension(file)
            self.cursor.execute(SQL_INSERT_FILE, {'dir_id': ii,
                                                  'file': file,
                                                  'ext_id': jj})

    def insert_extension(self, file):
        if file.rfind('.') > 0:
            ext = file.rpartition('.')[2]
        else:
            ext = ''
        if ext:
            rr = self.cursor.execute(SQL_FIND_EXT, (ext,)).fetchone()
            if rr:
                jj = rr[0]
            else:
                self.cursor.execute(SQL_INSERT_EXT, {'ext': ext})
                jj = self.cursor.lastrowid
        else:
            jj = 0
        return jj

    def insert_dir( self, full_file_name):
        '''
        Insert directory into Dirs table
        :param full_file_name:
        :return: row ID of file dir
        '''
        path = full_file_name.rpartition(os.sep)[0]
        rr = self.search_closest_parent(path)
        ii, pp = rr
        if pp == path:
            return ii

        self.cursor.execute(SQL_INSERT_DIR, {'path': path, 'id': ii, 'placeId': self.place_id})
        kk = self.cursor.lastrowid

        self.change_parent(kk, path)
        return kk

    def change_parent(self, new_parent_ID, path):
        old_parent_ID = self.parent_id_for_child(path)
        if old_parent_ID != -1:
            self.cursor.execute(SQL_CHANGE_PARENT_ID, {'currId': old_parent_ID,
                                                       'newId': new_parent_ID,
                                                       'newPath': path + '%'})

    def parent_id_for_child( self, path ):
        '''
        Check new file path:
          if it can be parent for other directories
        :param path:
        :return: parent Id of first found child, -1 if not children
        '''
        gg = self.cursor.execute(SQL_FIND_PART_PATH, {'newPath': path + '%',
                                                      'place': self.place_id}).fetchone()
        if gg:
            jj = gg[0]
        else:
            jj = -1

        return jj

    def search_closest_parent(self, path):
        '''
        Search parent directory
        :param path:  file path
        :return:  tuple of ID and path of parent directory or (0, '')
        '''
        res = (0, '')
        while path:
            ff = self.cursor.execute(SQL_FIND_EXACT_PATH, (path, self.place_id)).fetchone()
            if ff:
                res = tuple(ff)
                break
            path = path.rpartition(os.sep)[0]
        return res


if __name__ == "__main__":
    pass
