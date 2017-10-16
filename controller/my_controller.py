import sqlite3
import os

from PyQt5.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtCore import Qt

from controller.my_qt_model import TreeModel, MyListModel
from model.db_utils import DBUtils
from model.utils import create_db
from model.utils.load_db_data import LoadDBData

DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES


def yield_files(root, extensions):
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


class MyController():
    def __init__(self, view):
        self._connection = None
        self.dbu = None
        self.view = view.ui_main
        self.places = []
        self.curr_place = ()

    def on_open_db(self, file_name, create):
        if create:
            self._connection = sqlite3.connect(file_name, detect_types=DETECT_TYPES)
            create_db.create_all_objects(self._connection)
        else:
            self._connection = sqlite3.connect(file_name, detect_types=DETECT_TYPES)

        self.dbu = DBUtils(self._connection)
        self._populate_all_widgets()

    def on_populate_view(self, widget_name):
        if widget_name == 'all':
            self._populate_all_widgets()
        elif widget_name == 'dirTree':
            self._populate_directory_tree()
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
            self._populate_cb_places()
        else:
            pass

    def _populate_cb_places(self):
        self.view.cb_places.blockSignals(True)
        self.view.cb_places.clear()
        plc = self.dbu.select_other('PLACES')
        if plc:
            self.places = list(plc)
            self.view.cb_places.addItems((x[2] for x in self.places))
            self.view.cb_places.setCurrentIndex(0)
        self.curr_place = self.places[0]
        self.view.cb_places.blockSignals(False)

    def on_change_data(self, sender, data):
        '''
        handle of changing data in widgets
        :param sender: - widget name (consider the widget itself)
        :param data:   - widget specific data
        :return:
        '''
        print('|--> MyController.on_change_data', sender, data)
        if sender == 'cb_places':
            self._about_change_place(data)

    def _about_change_place(self, data):
        if data[0] >= len(self.places):
            self._add_place(data)
        else:
            self._change_place(data)

    def _change_place(self, data):
        """
        Check if selected place is available
        Ask for confirmation for switch to unavailable place/storage
        Save current item in self.curr_place if confirmed or available
        :param data: only first item is used, it contains current index
        :return: None
        """
        if self._is_place_available():
            self.curr_place = self.places[data[0]]
        else:
            res = self._ask_switch_to_unavailable_storage(data)
            if res == 0:                # Ok button
                self.curr_place = self.places[data[0]]
            else:                       # Cancel - return to prev.place
                self.view.cb_places.blockSignals(True)
                self.view.cb_places.setCurrentIndex(self.curr_place[0])
                self.view.cb_places.blockSignals(False)

    def _ask_switch_to_unavailable_storage(self, data):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setText('The storage {} is not available'.format(data[1]))
        box.addButton('Ok', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    def _add_place(self, data):
        res = self._ask_rename_or_new()
        if res == 0:                # add new
            self.curr_place = (data[0], data[1], data[1])
            self.places.append(self.curr_place)
            self.dbu.insert_other('PLACES', self.curr_place)
        elif res == 1:              # rename
            self._rename_place((self.curr_place[0], data[1]))
        else:                       # cancel
            self.view.cb_places.blockSignals(True)
            self.view.cb_places.removeItem(self.view.cb_places.currentIndex())
            self.view.cb_places.setCurrentIndex(self.curr_place[0])
            self.view.cb_places.blockSignals(False)

    def _rename_place(self, data):
        self.view.cb_places.blockSignals(True)
        self.view.cb_places.removeItem(self.view.cb_places.currentIndex())
        self.places[self.curr_place[0]] = (self.curr_place[0:1], data[1])
        self.view.cb_places.setCurrentIndex(self.curr_place[0])
        self.view.cb_places.blockSignals(False)
        self.dbu.update_other('PLACES', (data[1], self.curr_place[0]))

    def _ask_rename_or_new(self):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.addButton('Add new', QMessageBox.ActionRole)
        box.addButton('Rename', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    def _populate_ext_list(self):
        ext_list = self.dbu.select_other('EXT')
        model = MyListModel()
        for ext in ext_list:
            model.append_row(ext[1::-1])       # = (ext[1], ext[0]) = (Extension, ExtID)
        self.view.extList.setModel(model)

    def _populate_tag_list(self):
        print('_populate_tag_list')

    def _populate_author_list(self):
        print('_populate_author_list')

    def _populate_file_list(self):
        print('_populate_file_list')

    def _populate_comment_field(self):
        print('_populate_comment_field')

    def _populate_all_widgets(self):
        self._populate_directory_tree()
        self._populate_file_list()
        self._populate_comment_field()
        self._populate_ext_list()
        self._populate_tag_list()
        self._populate_author_list()
        self._populate_cb_places()

    def _populate_directory_tree(self):
        dir_tree = self.dbu.dir_tree_select(dir_id=0, level=0)

        model = TreeModel(dir_tree)

        self.view.dirTree.setModel(model)

    def _is_place_available(self):
        return True

    def on_scan_files(self):
        if self._is_place_available():
            _data = self._scan_file_system()
        else:
            _data = self._read_from_file()

        if _data:
            ld = LoadDBData(self._connection, self.curr_place)
            ld.load_data(_data)
            self._populate_directory_tree()

    def _scan_file_system(self):
        ext_ = self._get_selected_extensions()
        ext_item, okPressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                   '', QLineEdit.Normal, ext_)
        if okPressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            if root:
                return yield_files(root, ext_item)

        return ()       # not okPressed or root is empty

    def _read_from_file(self):
        return ()

    def _get_selected_extensions(self):
        extensions = self.view.extList.selectedIndexes()
        if extensions:
            model = self.view.extList.model()
            model.data(extensions[0], Qt.DisplayRole)
            ext_ = ', '.join(model.data(i, Qt.DisplayRole) for i in extensions)
        else:
            ext_ = ''
        return ext_
