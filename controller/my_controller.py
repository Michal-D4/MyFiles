import sqlite3
import os

from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

from controller.my_qt_model import TreeModel, TableModel
from controller.places import Places
from model.db_utils import DBUtils
from model.utils import create_db
from model.utils.load_db_data import LoadDBData

DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES


class MyController():
    def __init__(self, view):
        self._connection = None
        self._dbu = None
        self._cb_places = None
        self.view = view.ui_main

    def get_places_view(self):
        return self._cb_places

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
        for dir_name, dir_names, file_names in os.walk(root):
            if extensions:
                ext_ = tuple(x.strip('. ') for x in extensions.split(','))
                for filename in file_names:
                    if filename.rpartition('.')[2] in ext_:
                        yield os.path.join(dir_name, filename)
            else:
                for filename in file_names:
                    yield os.path.join(dir_name, filename)

    def on_open_db(self, file_name, create):
        if create:
            self._connection = sqlite3.connect(file_name, detect_types=DETECT_TYPES)
            create_db.create_all_objects(self._connection)
        else:
            self._connection = sqlite3.connect(file_name, detect_types=DETECT_TYPES)

        self._dbu = DBUtils(self._connection)
        self._populate_all_widgets()

    def on_populate_view(self, widget_name):
        if widget_name == 'all':
            self._populate_all_widgets()
        elif widget_name == 'dirTree':
            self._populate_directory_tree((0, 0))
        elif widget_name == 'extList':
            self._populate_ext_list()
        elif widget_name == 'tagsList':
            self._populate_tag_list()
        elif widget_name == 'authorsList':
            self._populate_author_list()
        elif widget_name == 'filesList':
            self._populate_file_list()
        elif widget_name == 'commentField':
            self._populate_comment_field()
        elif widget_name == 'cb_places':
            self._cb_places.populate_cb_places()
        else:
            pass

    def on_change_data(self, sender, data):
        '''
        handle of changing data in widgets
        :param sender: - widget name (consider the widget itself)
        :param data:   - widget specific data
        :return:
        '''
        if sender == 'cb_places':
            self._cb_places.about_change_place(data)

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
            model.append_row((tag,), id)
        self.view.tagsList.setModel(model)

    def _populate_author_list(self):
        author_list = self._dbu.select_other('AUTHORS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, "Authors")
        for author, id in author_list:
            print('_populate_author_list', author, id)
            model.append_row(author, id)
        self.view.authorsList.setModel(model)

    def _populate_file_list(self):
        sel_idx = self.view.dirTree.selectedIndexes()
        cur_idx = self.view.dirTree.currentIndex()
        print('_populate_file_list', cur_idx, sel_idx)

    def _populate_comment_field(self):
        file_idx = self.view.filesList.selectedIndexes()
        if file_idx:
            _idx = file_idx[0]
            assert isinstance(_idx, int), \
                "the type is {} instead of int".format(type(_idx))
            tags = self._dbu.select_other("FILE_TAGS", _idx)
            authors = self._dbu.select_other("FILE_AUTHORS", _idx)
            comment = self._dbu.select_other("FILE_COMMENT", _idx)
            self.view.commentField.setText('\\n'.join((
                'Key words: {}'.format(', '.join(tags)),
                'Authors: {}'.format(', '.join(authors)),
                comment)))
            print('_populate_comment_field', tags, authors, comment)

    def _populate_all_widgets(self):
        self._cb_places = Places(self)
        self._populate_directory_tree((0, 0))
        # self._populate_file_list()        # populate only on demand
        # self._populate_comment_field()    # populate only on demand
        self._populate_ext_list()
        self._populate_tag_list()
        self._populate_author_list()
        self._cb_places.populate_cb_places()

    def _populate_directory_tree(self, data):
        dir_tree = self._dbu.dir_tree_select(dir_id=data[0], level=data[1])

        model = TreeModel(dir_tree)
        model.setHeaderData(0, Qt.Horizontal, ("Directories",))

        self.view.dirTree.setModel(model)

    def on_scan_files(self):
        """
        The purpose is to fill the data base with files by means of
        1) scanning the file system for  mounted disk
        or
        2) reading from prepared file for  unmounted disk
        :return: None
        """
        if self._cb_places.is_disk_mounted() == Places.NOT_MOUNTED:
            _data = self._read_from_file()
        else:
            _data = self._scan_file_system()

        if _data:
            files = LoadDBData(self._connection, self._cb_places.get_curr_place())
            files.load_data(_data)
            self._populate_directory_tree()

    def _scan_file_system(self):
        ext_ = self._get_selected_extensions()
        ext_item, ok_pressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                    '', QLineEdit.Normal, ext_)
        if ok_pressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            if root:
                self._cb_places.update_disk_info(root)
                return MyController._yield_files(root, ext_item)

        return ()       # not ok_pressed or root is empty

    def _read_from_file(self):
        file_name = QFileDialog().getOpenFileName(self.view.extList, 'Choose input file',
                                                  os.getcwd())
        try:
            a_file = open(file_name)
        except IOError:
            a_file = ()

        if a_file:
            line = next(a_file)
            if not self._cb_places.get_curr_place()[1] in line:
                MyController._bad_file_message(file_name)
                a_file = ()

        return a_file

    @staticmethod
    def _bad_file_message(file_name):
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setText("The file {} doesn't have data from current place!".format(file_name))
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
