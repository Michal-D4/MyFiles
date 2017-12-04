# model/file_info.py

import os
import datetime
import sqlite3
from threading import Thread, Event
from PyPDF2 import PdfFileReader, utils

from model.utils.load_db_data import LoadDBData
from model.helpers import *
from controller.places import Places

SQL_AUTHOR_ID = 'select AuthorID from Authors where Author = ?;'

SQL_INSERT_AUTHOR = 'insert into Authors (Author) values (?);'

SQL_INSERT_FILEAUTHOR = 'insert into FileAuthor (FileID, AuthorID) values (?, ?);'

SQL_INSERT_COMMENT = 'insert into Comments (Comment) values (?);'

SQL_FILES_WITHOUT_INFO = ' '.join(('select f.FileID, f.FileName, d.Path',
                                   'from Files f, Dirs d',
                                   'where f.PlaceId = :place_id and',
                                   'f.Size = 0 and f.DirID = d.DirID;'))

SQL_UPDATE_FILE = ' '.join(('update Files set',
                            'CommentID = :comm_id,',
                            'Year = :year,',
                            'Pages = :page,',
                            'Size = :size',
                            'where FileID = :file_id;'))

E = Event()

class LoadFiles(Thread):
    def __init__(self, conn, cur_place, data_, group=None, target=None, name=None, args=(),
                 kwargs=None, *, daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.cur_place = cur_place
        self.conn = conn
        self.data = data_

    def run(self):
        super().run()
        start_time = datetime.datetime.now()
        # print('|===> LoadFiles start time', start_time)
        files = LoadDBData(self.conn, self.cur_place)
        files.load_data(self.data)
        end_time = datetime.datetime.now()
        # print('|===> LoadFiles end time', end_time, ' delta', end_time - start_time)
        E.set()


class FileInfo(Thread):
    def run(self):
        super().run()
        E.wait()
        start_time = datetime.datetime.now()
        # print('|===> FileInfo start time', start_time)
        self.update_files()
        end_time = datetime.datetime.now()
        # print('|===> FileInfo end time', end_time, ' delta', end_time - start_time)

    def __init__(self, conn, place_inst):
        super().__init__()
        self.places = place_inst
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
        self.cursor.execute(SQL_INSERT_FILEAUTHOR, (file_id, auth_id))
        self.conn.commit()

    def _insert_comment(self):
        if len(self.file_info) > 2:
            try:
                comm = 'Creation date {}\r\nTitle: {}'.format(self.file_info[4], self.file_info[5])
            except IndexError:
                print('IndexError ', len(self.file_info))
            self.cursor.execute(SQL_INSERT_COMMENT, (comm,))
            self.conn.commit()
            comm_id = self.cursor.lastrowid
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

    def get_pdf_info(self, file):
        with (open(file, "rb")) as pdf_file:
            try:
                fr = PdfFileReader(pdf_file, strict=False)
                fi = fr.documentInfo
                self.file_info.append(fr.getNumPages())
            except (ValueError, utils.PdfReadError, utils.PdfStreamError):
                self.file_info += [0, '', '', '']
            else:
                if fi is not None:
                    self.file_info.append(fi.getText('/Author'))
                    self.file_info.append(FileInfo.pdf_creation_date(fi))
                    self.file_info.append(fi.getText('/Title'))
                else:
                    self.file_info += ['', '', '']

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
        cur_place = self.places.get_curr_place()
        file_list = self.cursor.execute(SQL_FILES_WITHOUT_INFO,
                                        {'place_id': cur_place[1][0]}).fetchall()
        if cur_place[2] == Places.MOUNTED:
            root = self.places.get_mount_point()
            foo = lambda x: os.altsep.join((root, x))
        else:
            root = ''
            foo = lambda x: x
        print('|---> update_files:', root, foo(file_list[0][2]))
        for file_id, file, path in file_list:
            file_name = os.path.join(foo(path), file)
            print(file_id, file_name)
            self.update_file(file_id, file_name)
