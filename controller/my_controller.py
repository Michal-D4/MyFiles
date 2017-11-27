# controller/my_controller.py

import sqlite3
import os

from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QModelIndex

from controller.my_qt_model import TreeModel, TableModel
from controller.places import Places
from model.db_utils import DBUtils
from model.utils import create_db
from model.file_info import FileInfo, LoadFiles
from model.helpers import *
# from model.utils.load_db_data import LoadDBData

DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES


class MyController():
    def __init__(self, view):
        self._connection = None
        self._dbu = None
        self._cb_places = None
        self.view = view.ui_main

    def get_places_view(self):
        return self.view.cb_places

    def get_db_utils(self):
        return self._dbu

    @staticmethod
    def _yield_files(root, extensions):
        """
        generator of file list
        :param root: root directory
        :param extensions: list of extensions
        :return: generator
        """
        for dir_name, _, file_names in os.walk(root):
            if extensions:
                ext_ = tuple(x.strip('. ') for x in extensions.split(','))
                for filename in file_names:
                    if get_file_extension(filename) in ext_:
                        yield os.path.join(dir_name, filename)
            else:
                for filename in file_names:
                    yield os.path.join(dir_name, filename)

    def on_open_db(self, file_name, create):
        if create:
            self._connection = sqlite3.connect(file_name, check_same_thread=False,
                                               detect_types=DETECT_TYPES)
            create_db.create_all_objects(self._connection)
        else:
            self._connection = sqlite3.connect(file_name, check_same_thread=False,
                                               detect_types=DETECT_TYPES)

        self._dbu = DBUtils(self._connection)
        self._populate_all_widgets()

    def on_change_data(self, sender, data):
        '''
        handle of changing data in widgets
        :param sender: - widget name (consider the widget itself)
        :param data:   - widget specific data
        :return:
        '''
        if sender == 'cb_places':
            self._cb_places.about_change_place(data)
        elif sender == 'filesList':
            self._populate_file_list(data[0])
        elif sender == 'dirTree':
            self._populate_directory_tree(data[0])
        elif sender == 'commentField':
            self._populate_comment_field(data)
        elif sender == 'Edit key words':
            self._edit_key_words()
        elif sender == 'Edit authors':
            self._edit_authors()
        elif sender == 'Edit comment':
            self._edit_comment()
        elif sender == 'Delete':
            self._delete_file()
        elif sender == 'Open':
            self._open_file()
        elif sender == 'advanced_file_list':
            self.advanced_file_list()

    def advanced_file_list(self):
        # todo - select files
        # extensions - or
        # tags       - and
        # authors    - or
        # dir        - tree, level
        # date ???   - after
        dd = self.view.dirTree.selectionModel().selectedRows()  # list of indexes
        if dd:
            dir_ = self.view.dirTree.model().data(dd[0], Qt.UserRole)
            print('|---> advanced_file_list', dir_)

    def _delete_file(self):
        # todo - delete file from DB
        pass

    def _open_file(self):
        idx = self.view.dirTree.currentIndex()
        dir_ = self.view.dirTree.model().data(idx, Qt.UserRole)
        f_idx = self.view.filesList.currentIndex()
        file_name = self.view.filesList.model().data(f_idx)
        full_file_name = os.path.join(dir_[2], file_name)
        if os.path.isfile(full_file_name):
            os.startfile(full_file_name)
        else:
            MyController._show_message("Can't find file {}".format(full_file_name))

    def _edit_key_words(self):
        # todo - provide the list/table of existed and allow add new
        pass

    def _edit_authors(self):
        # todo - provide the list/table of existed and allow add new
        pass

    def _edit_comment(self):
        # todo - edit comment
        pass

    def _populate_ext_list(self):
        ext_list = self._dbu.select_other('EXT')
        model = TreeModel(ext_list)
        model.setHeaderData(0, Qt.Horizontal, "Extensions")
        self.view.extList.setModel(model)

    def _populate_tag_list(self):
        tag_list = self._dbu.select_other('TAGS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, ("Key words",))
        for tag, id in tag_list:
            model.append_row(tag, id)
        self.view.tagsList.setModel(model)

    def _populate_author_list(self):
        author_list = self._dbu.select_other('AUTHORS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, "Authors")
        for author, id in author_list:
            model.append_row(author, id)
        self.view.authorsList.setModel(model)

    def _populate_file_list(self, dir_idx):
        if dir_idx:
            model = TableModel()
            files = self._dbu.select_other('FILES_CUR_DIR', (dir_idx[0],))
            model.setHeaderData(0, Qt.Horizontal, 'File Date Pages Size')
            for ff in files:
                model.append_row(ff[3:], ff[:3])
            self.view.filesList.setModel(model)

            self.view.filesList.setAlternatingRowColors(True)

            self.view.statusbar.showMessage('{} ({})'.format(dir_idx[2], model.rowCount(QModelIndex())))
        else:
            self.view.statusbar.showMessage('No data')

    def _populate_comment_field(self, data):
        file_id = data[0]
        comment_id = data[2]
        if file_id:
            assert isinstance(file_id, int), \
                "the type of file_id is {} instead of int".format(type(file_id))
            tags = self._dbu.select_other("FILE_TAGS", (file_id,))
            tgs = []
            for tt in tags:
                tgs.append(tt)
            authors = self._dbu.select_other("FILE_AUTHORS", (file_id,))
            auth = []
            for aa in authors:
                auth.append(aa[0])
            if comment_id:
                comment = tuple(self._dbu.select_other("FILE_COMMENT", (comment_id,)))
                comm = []
                for cc in comment:
                    comm.append(cc[0])
            else:
                comm = ('',)
            self.view.commentField.setText('\r\n'.join((
                'Key words: {}'.format(', '.join(tgs)),
                'Authors: {}'.format(', '.join(auth)),
                comm[0])))

    def _populate_all_widgets(self):
        self._cb_places = Places(self)
        self._cb_places.populate_cb_places()
        self._populate_directory_tree(self._cb_places.get_curr_place()[1][0])
        self._populate_ext_list()
        self._populate_tag_list()
        self._populate_author_list()

    def _populate_directory_tree(self, place_id):
        dirs = self._get_dirs(place_id)

        model = TreeModel(dirs)
        model.setHeaderData(0, Qt.Horizontal, ("Directories",))

        self.view.dirTree.setModel(model)
        idx = model.index(0, 0)
        self.view.dirTree.setCurrentIndex(idx)

        self._populate_file_list(model.data(idx, role=Qt.UserRole))

        self.view.dirTree.selectionModel().selectionChanged.connect(self.sel_changed)

    def _get_dirs(self, place_id):
        """
        Returns directory tree for current place
        :param place_id:
        :return: list of tuples (Dir name, DirID, ParentID, Full path of dir)
        """
        # TODO for removal places - substitute root (i.e. E:\\)
        root = self._cb_places.get_mount_point()
        dir_tree = self._dbu.dir_tree_select(dir_id=0, level=0, place_id=place_id)
        dirs = []
        for rr in dir_tree:         # DirID, Path, ParentID, level
            if self._cb_places.get_disk_state() == Places.NOT_REMOVAL:
                dirs.append((os.path.split(rr[1])[1], rr[0], rr[2], rr[1]))
            else:
                dirs.append((os.path.split(rr[1])[1], rr[0], rr[2], os.altsep.join((root, rr[1]))))
        return dirs

    def sel_changed(self, sel1, sel2):
        """
        Changed selection in dirTree
        :param sel1: QList<QModelIndex>
        :param sel2: QList<QModelIndex>
        :return: None
        """
        idx = sel1.indexes()
        if idx:
            dir_idx = self.view.dirTree.model().data(idx[0], Qt.UserRole)
            self._populate_file_list(dir_idx)

    def on_scan_files(self):
        """
        The purpose is to fill the data base with files by means of
        1) scanning the file system for  mounted disk
        or
        2) reading from prepared file for  unmounted disk
        :return: None
        """
        if self._cb_places.get_disk_state() == Places.NOT_MOUNTED:
            _data = self._read_from_file()
        else:
            _data = self._scan_file_system()

        if _data:
            curr_place = self._cb_places.get_curr_place()
            load_files = LoadFiles(self._connection, curr_place, _data)
            load_files.start()

            thread = FileInfo(self._connection, curr_place[1][0])
            thread.start()

    def _scan_file_system(self):
        ext_ = self._get_selected_extensions()
        ext_item, ok_pressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                    '', QLineEdit.Normal, ext_)
        if ok_pressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            if root:
                self._cb_places.update_place_name(root)
                return MyController._yield_files(root, ext_item)

        return ()       # not ok_pressed or root is empty

    def _read_from_file(self):
        file_name = QFileDialog().getOpenFileName(self.view.extList, 'Choose input file',
                                                  os.getcwd())
        with open(file_name, 'rb') as a_file:
            line = next(a_file)
            if not self._cb_places.get_curr_place()[1][1] in line:
                # todo : in case of 'other place' check if place defined in the first line of file
                # 1) if not defined - possible action:
                #    a)  show message and stop action
                #    b)  ???
                # 2) if defined - possible action:
                #    a)  - switch to place in file
                #    b)  - create new place
                MyController._show_message("The file {} doesn't have data from current place!".
                                           format(file_name))
                a_file = ()
            return a_file
        return ()

    @staticmethod
    def _show_message(message, message_type=QMessageBox.Critical):
        box = QMessageBox()
        box.setIcon(message_type)
        box.setText(message)
        box.addButton('Ok', QMessageBox.AcceptRole)
        box.exec_()

    def _get_selected_extensions(self):
        extensions = self.view.extList.selectedIndexes()
        if extensions:
            model = self.view.extList.model()
            ext_ = ', '.join(model.data(i, Qt.DisplayRole) for i in extensions)
        else:
            ext_ = ''
        return ext_
