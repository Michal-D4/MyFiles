# model/file_info.py

import re
import datetime
from PyPDF2 import PdfFileReader, utils
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot

from model.utils.load_db_data import LoadDBData
from model.helpers import *
from controller.places import Places

AUTHOR_ID = 'select AuthorID from Authors where Author = ?;'

INSERT_AUTHOR = 'insert into Authors (Author) values (?);'

FILE_AUTHOR = 'select * from FileAuthor where FileID=? and AuthorID=?'

INSERT_FILEAUTHOR = 'insert into FileAuthor (FileID, AuthorID) values (?, ?);'

SELECT_COMMENT = 'select BookTitle from Comments where CommentID=?;'

INSERT_COMMENT = 'insert into Comments (BookTitle, Comment) values (?, ?);'

FILES_IN_LOAD = ' '.join(('select f.FileID, f.FileName, d.Path, f.CommentID,',
                          'f.IssueDate, f.Pages from Files f, Dirs d',
                          'where f.DirID = d.DirID and d.DirID in ({});'))

UPDATE_FILE = ' '.join(('update Files set',
                        'CommentID = :comm_id,',
                        'FileDate = :date,',
                        'Pages = :page,',
                        'Size = :size,',
                        'IssueDate = :issue_date',
                        'where FileID = :file_id;'))


class LoadFiles(QObject):
    finished = pyqtSignal()

    def __init__(self, conn, cur_place, data_):
        super().__init__()
        self.cur_place = cur_place
        self.conn = conn
        self.data = data_
        self.updated_dirs = None

    @pyqtSlot()
    def run(self):
        files = LoadDBData(self.conn, self.cur_place)
        files.load_data(self.data)
        self.updated_dirs = files.get_updated_dirs()
        self.finished.emit()

    def get_updated_dirs(self):
        return self.updated_dirs


class FileInfo(QObject):
    finished = pyqtSignal()

    @pyqtSlot()
    def run(self):
        self._update_files()
        self.finished.emit()           # 'Updating of files is finished'
        # print('--> FileInfo.run finished')

    def __init__(self, conn, place_inst, updated_dirs):
        super().__init__()
        self.upd_dirs = updated_dirs
        self.places = place_inst
        self.conn = conn
        self.cursor = conn.cursor()
        self.file_info = []

    def _insert_author(self, file_id):
        authors = re.split(r',|;|&|\band\b', self.file_info[3])
        for author in authors:
            aut = author.strip()
            auth_idl = self.cursor.execute(AUTHOR_ID, (aut,)).fetchone()
            if not auth_idl:
                self.cursor.execute(INSERT_AUTHOR, (aut,))
                self.conn.commit()
                auth_id = self.cursor.lastrowid
            else:
                auth_id = auth_idl[0]
                check = self.cursor.execute(FILE_AUTHOR, (file_id, auth_id))
                if check:
                    return
            self.cursor.execute(INSERT_FILEAUTHOR, (file_id, auth_id))
            self.conn.commit()

    def _insert_comment(self, _file):
        if len(self.file_info) > 2:
            try:
                pages = self.file_info[2]
                issue_date = self.file_info[4]
                book_title = self.file_info[5]
            except IndexError:
                print('IndexError ', len(self.file_info))

            self.cursor.execute(INSERT_COMMENT, (book_title, ''))
            self.conn.commit()
            comm_id = self.cursor.lastrowid
        else:
            comm_id = _file.comment_id
            pages = _file.pages
            issue_date = _file.issue_date
        return comm_id, pages, issue_date

    def _get_file_info(self, full_file_name):
        """
        Store info in self.file_info
        :param full_file_name:
        :return: None
        """
        self.file_info.clear()
        if os.path.isfile(full_file_name):
            st = os.stat(full_file_name)
            self.file_info.append(st.st_size)
            self.file_info.append(datetime.datetime.fromtimestamp(st.st_mtime).date().isoformat())
            if get_file_extension(full_file_name) == 'pdf':
                self._get_pdf_info(full_file_name)
        else:
            self.file_info.append('')
            self.file_info.append('')

    def _get_pdf_info(self, file):
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
                    self.file_info.append(FileInfo._pdf_creation_date(fi))
                    self.file_info.append(fi.getText('/Title'))
                else:
                    self.file_info += ['', '', '']

    @staticmethod
    def _pdf_creation_date(fi):
        ww = fi.getText('/CreationDate')
        if ww:
            return '-'.join((ww[2:6], ww[6:8], ww[8:10]))
        return ''

    def _update_file(self, file_):
        """
        Update file info in tables Files, Authors and Comments
        :param file_: file_id, full_name, comment_id, issue_date, pages
        :return: None
        """
        self._get_file_info(file_.full_name)
        if file_.comment_id == 0:
            comm_id, pages, issue_date = self._insert_comment(file_)
        else:
            comm_id = file_.comment_id
            pages = file_.pages
            issue_date = file_.issue_data
        print('--> _update_file', comm_id, pages, issue_date)

        self.cursor.execute(UPDATE_FILE, {'comm_id': comm_id,
                                          'date': self.file_info[1],
                                          'page': pages,
                                          'size': self.file_info[0],
                                          'issue_date': issue_date,
                                          'file_id': file_.file_id})
        self.conn.commit()
        if len(self.file_info) > 3 and self.file_info[3]:
            self._insert_author(file_.file_id)

    def _update_files(self):
        db_file_info = namedtuple('db_file_info',
                                  'file_id full_name comment_id issue_date pages')
        dir_ids = ','.join(self.upd_dirs)
        file_list = self.cursor.execute(FILES_IN_LOAD.
                                        format(dir_ids)).fetchall()

        cur_place = self.places.get_curr_place()
        if cur_place[2] == Places.MOUNTED:
            root = self.places.get_mount_point()
            full_path = lambda x: os.altsep.join((root, x))
        else:
            full_path = lambda x: x

        # file_id, file_name, path, comment_id, issue_date
        for it in file_list:
            file_name = os.path.join(full_path(it[2]), it[1])
            file_ = db_file_info._make((it[0], file_name) + it[-3:])
            self._update_file(file_)
