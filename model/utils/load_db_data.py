import os
import datetime

from PyPDF2 import PdfFileReader

SQL_FIND_PART_PATH = '''select ParentID
    from Dirs where Path like :newPath and PlaceId = :place;'''

SQL_FIND_EXACT_PATH = '''select DirID, Path
    from Dirs where Path = :newPath and PlaceId = :place;'''

SQL_CHANGE_PARENT_ID = '''update Dirs set ParentID = :newId
 where ParentID = :currId and Path like :newPath and DirID != :newId;'''

SQL_FIND_FILE = '''select *
    from Files where DirID = :dir_id and FileName = :file;'''

SQL_INSERT_DIR = '''insert into Dirs
    (Path, ParentID, PlaceId)
    values (:path, :id, :placeId);'''

SQL_INSERT_FILE = '''insert into Files
    (DirID, FileName, ExtID, PlaceId, CommentID, Year, Pages, Size)
    values (:dir_id, :file, :ext_id, :placeId, :comm_id, :year, :page, :size);'''

SQL_FIND_EXT = '''select ExtID
    from Extensions where Extension = ?;'''

# Groups will be created manually and then GroupID will be updated TODO
SQL_INSERT_EXT = '''insert into Extensions
    (Extension, GroupID) values (:ext, 0);'''

SQL_AUTHOR_ID = 'select AuthorID from Authors where Author = ?;'
SQL_INSERT_AUTHOR = 'insert into Authors (Author) values (?);'

SQL_INSERT_FILEAUTHOR = 'insert into FileAuthor (FileID, AuthorID) values (?, ?);'

SQL_INSERT_COMMENT = 'insert into Comments (Comment) values (?);'

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
        self.file_info = []

    def set_current_place(self, current_place):
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
        for line in data:
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

        item = self.cursor.execute(SQL_FIND_FILE, {'dir_id': dir_id, 'file': file}).fetchone()
        if not item:
            ext_id, ext = self.insert_extension(file)
            print('|---> insert_file', ext_id, ext)
            self.get_file_info(full_file_name, ext)
            comm_id, pages = self._insert_comment()

            self.cursor.execute(SQL_INSERT_FILE, {'dir_id': dir_id,
                                                  'file': file,
                                                  'ext_id': ext_id,
                                                  'placeId': self.place_id,
                                                  'comm_id': comm_id,
                                                  'year': self.file_info[1],
                                                  'page': pages,
                                                  'size': self.file_info[0]})
            file_id = self.cursor.lastrowid
            if len(self.file_info) > 3 and self.file_info[3]:
                self.insert_author(file_id)

    def insert_author(self, file_id):
        # todo need cycle in case of several authors
        auth_idl = self.cursor.execute(SQL_AUTHOR_ID, self.file_info[3]).fetchone()
        if not auth_idl:
            self.cursor.execute(SQL_INSERT_AUTHOR, (self.file_info[3],))
            auth_id = self.cursor.lastrowid
        else:
            auth_id = auth_idl[0]
        self.cursor.execute(SQL_INSERT_FILEAUTHOR, (file_id, auth_id))

    def _insert_comment(self):
        if len(self.file_info) > 2:
            comm = '\r\n'.join((str(x) for x in self.file_info[4:] if not x == ''))    # todo formatting
            self.cursor.execute(SQL_INSERT_COMMENT, (comm,))
            comm_id = self.cursor.lastrowid
            print('|---> _insert_comment', comm_id, comm)
            pages = self.file_info[2]
        else:
            comm_id = 0
            pages = ''
        return comm_id, pages

    def get_file_info(self, file, ext):
        '''
        Store info in self.file_info:
            0 - size,
            1 - year,  further - pdf-info
            2 - pages,
            3 - author,
            4 - CreationDate
            5 - Title
        :param file: full path
        :param ext: pdf or not pdf
        :return: None
        '''
        print('|---> get_file_info', ext, file)
        self.file_info.clear()
        if os._exists(file):
            st = os.stat(file)
            self.file_info.append(st.st_size)
            self.file_info.append(datetime.datetime.fromtimestamp(st.st_ctime).date().isoformat())
            if str.lower(ext) == 'pdf':
                self.get_pdf_info(file)
        else:
            self.file_info.append('')
            self.file_info.append('')
        print('|---> get_file_info', self.file_info)

    def get_pdf_info(self, file):
        print('|---> get_pdf_info', file)
        try:
            fr = PdfFileReader(open(file, "rb"), strict=False)
            self.file_info.append(fr.getNumPages())
            fi = fr.documentInfo
            if not fi is None:
                self.file_info.append(fi.getText('/Author'))
                ww = fi.getText('/CreationDate')
                if ww:
                    self.file_info.append('-'.join((ww[2:6], ww[6:8], ww[8:10])))
                else:
                    self.file_info.append('')
                self.file_info.append(fi.getText('/Title'))
        except IOError:
            pass

    def insert_extension(self, file):
        if file.rfind('.') > 0:
            ext = file.rpartition('.')[2]
        else:
            ext = ''
        if ext:
            item = self.cursor.execute(SQL_FIND_EXT, (ext,)).fetchone()
            if item:
                idx = item[0]
            else:
                self.cursor.execute(SQL_INSERT_EXT, {'ext': ext})
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
        path = full_file_name.rpartition(os.sep)[0]
        idx, parent_path = self.search_closest_parent(path)
        if parent_path == path:
            return idx

        self.cursor.execute(SQL_INSERT_DIR, {'path': path, 'id': idx, 'placeId': self.place_id})
        idx = self.cursor.lastrowid

        self.change_parent(idx, path)
        return idx

    def change_parent(self, new_parent_id, path):
        old_parent_id = self.parent_id_for_child(path)
        if old_parent_id != -1:
            self.cursor.execute(SQL_CHANGE_PARENT_ID, {'currId': old_parent_id,
                                                       'newId': new_parent_id,
                                                       'newPath': path + '%'})

    def parent_id_for_child(self, path):
        '''
        Check the new file path:
          if it can be parent for other directories
        :param path:
        :return: parent Id of first found child, -1 if not children
        '''
        item = self.cursor.execute(SQL_FIND_PART_PATH, {'newPath': path + '%',
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
            item = self.cursor.execute(SQL_FIND_EXACT_PATH, (path, self.place_id)).fetchone()
            if item:
                res = tuple(item)
                break
            path = path.rpartition(os.sep)[0]
        return res


if __name__ == "__main__":
    pass
