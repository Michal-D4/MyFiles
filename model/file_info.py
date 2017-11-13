# model/file_info.py

import os
import datetime
import sqlite3
from threading import Thread
from PyPDF2 import PdfFileReader, utils

from model.helpers import *

SQL_AUTHOR_ID = 'select AuthorID from Authors where Author = ?;'

SQL_INSERT_AUTHOR = 'insert into Authors (Author) values (?);'

SQL_INSERT_FILEAUTHOR = 'insert into FileAuthor (FileID, AuthorID) values (?, ?);'

SQL_INSERT_COMMENT = 'insert into Comments (Comment) values (?);'

SQL_FILES_WITHOUT_INFO = '''select f.FileID, f.FileName, d.Path 
from Files f, Dirs d 
where f.PlaceId = :place_id and f.Size = 0 and f.DirID = d.DirID;'''
SQL_UPDATE_FILE = '''update Files set
CommentID = :comm_id,
Year = :year,
Pages = :page,
Size = :size
where FileID = :file_id;'''


# TODO send the result of SQL_FILES_WITHOUT_INFO and yield the file info from here
class FileInfo(Thread):
    def run(self):
        super().run()
        print('|===> FileInfo start time', sqlite3.time.time())
        self.update_files()

    def __init__( self, conn, place_id ):
        super().__init__()
        # print('|--> FileInfo.__init__', conn, place_id)
        self.place_id = place_id
        self.conn = conn
        self.cursor = conn.cursor()
        self.file_info = []

    def insert_author(self, file_id):
        # todo need cycle in case of several authors
        auth_idl = self.cursor.execute(SQL_AUTHOR_ID, (self.file_info[3],)).fetchone()
        if not auth_idl:
            self.cursor.execute(SQL_INSERT_AUTHOR, (self.file_info[3],))
            self.conn.commit()
            auth_id = self.cursor.lastrowid
        else:
            auth_id = auth_idl[0]
        # print('|--> insert_author', self.file_info[3], file_id, auth_id)
        self.cursor.execute(SQL_INSERT_FILEAUTHOR, (file_id, auth_id))
        self.conn.commit()

    def _insert_comment(self):
        if len(self.file_info) > 2:
            comm = 'Creation date {}\r\nTitle: {}'.format(self.file_info[4], self.file_info[5])
            self.cursor.execute(SQL_INSERT_COMMENT, (comm,))
            self.conn.commit()
            comm_id = self.cursor.lastrowid
            # print('|---> _insert_comment', comm_id, comm)
            pages = self.file_info[2]
        else:
            comm_id = 0
            pages = ''
        return comm_id, pages

    def get_file_info(self, full_file_name):
        """
        Store info in self.file_info:
            0 - size,
            1 - year,  further - pdf-info
            2 - pages,
            3 - author,
            4 - CreationDate from PDF
            5 - Title
        :param full_file_name:
        :return: None
        """
        # print('|---> get_file_info', full_file_name)
        self.file_info.clear()
        if os.path.isfile(full_file_name):
            st = os.stat(full_file_name)
            self.file_info.append(st.st_size)
            self.file_info.append(datetime.datetime.fromtimestamp(st.st_ctime).date().isoformat())
            if get_file_extension(full_file_name) == 'pdf':
                self.get_pdf_info(full_file_name)
        else:
            self.file_info.append('')
            self.file_info.append('')
        # print('|---> get_file_info', self.file_info)

    def get_pdf_info(self, file):
        # print('|---> get_pdf_info', file)
        with (open(file, "rb")) as pdf_file:
            fr = PdfFileReader(pdf_file, strict=False)
            try:
                self.file_info.append(fr.getNumPages())
            except (ValueError, utils.PdfReadError):
                print('|---> error', file)
                self.file_info.append(0)
                self.file_info.append('')
                self.file_info.append('')
                self.file_info.append('')
            else:
                fi = fr.documentInfo
                if fi is not None:
                    self.file_info.append(fi.getText('/Author'))
                    self.file_info.append(FileInfo.pdf_creation_date(fi))
                    self.file_info.append(fi.getText('/Title'))

    @staticmethod
    def pdf_creation_date(fi):
        ww = fi.getText('/CreationDate')
        if ww:
            return '-'.join((ww[2:6], ww[6:8], ww[8:10]))
        return ''

    def update_file(self, file_id, full_file_name):
        """
        Update file info in tables Files, Authors and Comments
        :param file_id:
        :param full_file_name:
        :return: None
        """
        self.get_file_info(full_file_name)
        comm_id, pages = self._insert_comment()

        self.cursor.execute(SQL_UPDATE_FILE, {'comm_id': comm_id,
                                              'year': self.file_info[1],
                                              'page': pages,
                                              'size': self.file_info[0],
                                              'file_id': file_id})
        self.conn.commit()
        if len(self.file_info) > 3 and self.file_info[3]:
            self.insert_author(file_id)

    def update_files(self):
        curr = self.cursor.execute(SQL_FILES_WITHOUT_INFO, {'place_id': self.place_id})
        file_list = list(curr)
        for file_id, file, path in file_list:
            file_name = os.path.join(path, file)
            # print(file_name)
            self.update_file(file_id, file_name)
        print('|===> FileInfo end time', sqlite3.time.time())
