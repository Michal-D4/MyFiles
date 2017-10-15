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
    for dir_name, dir_names, file_names in os.walk(root):
        if extensions:
            ext_ = tuple(x.strip('. ') for x in extensions.split(','))
            for filename in file_names:
                if filename.rpartition('.')[2] in ext_:
                    yield(os.path.join(dir_name, filename))
        else:
            for filename in file_names:
                yield(os.path.join(dir_name, filename))


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
        self.populate_all_widgets()

    def on_populate_view(self, widget_name):
        if widget_name == 'all':
            self.populate_all_widgets()
        elif widget_name == 'dirTree':
            self.populate_directory_tree()
        elif widget_name == 'extList':
            self.populate_ext_list()
        elif widget_name == 'tagsList':
            self.populate_tag_list()
        elif widget_name == 'authorsList':
            self.populate_author_list()
        elif widget_name == 'filesList':
            self.populate_file_list()
        elif widget_name == 'commentField':
            self.populate_comment_field()
        elif widget_name == 'cb_places':
            self.populate_cb_places()
        else:
            pass

    def populate_cb_places(self):
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
            self.about_change_place(data)

    def about_change_place(self, data):
        if data[0] >= len(self.places):
            self.add_place(data)
        else:
            self.change_place(data)

    def change_place(self, data):
        if self.is_place_available():
            self.curr_place = self.places[data[0]]
        else:
            res = self.ask_switch_to_unavailable_storage(data)
            if res == 0:                # Ok button
                self.curr_place = self.places[data[0]]
            else:                       # Cancel - return to prev.place
                self.view.cb_places.blockSignals(True)
                self.view.cb_places.setCurrentIndex(self.curr_place[0])
                self.view.cb_places.blockSignals(False)

    def ask_switch_to_unavailable_storage(self, data):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setText('The storage {} is not available'.format(data[1]))
        box.addButton('Ok', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    def add_place(self, data):
        res = self.ask_rename_or_new()
        if res == 0:                # add new
            self.curr_place = (data[0], data[1], data[1])
            self.places.append(self.curr_place)
            self.dbu.insert_other('PLACES', self.curr_place)
        elif res == 1:              # rename
            self.rename_place((self.curr_place[0], data[1]))
        else:                       # cancel
            self.view.cb_places.blockSignals(True)
            self.view.cb_places.clear()
            self.view.cb_places.addItems((x[2] for x in self.places))
            self.view.cb_places.blockSignals(False)
            self.view.cb_places.setCurrentIndex(self.curr_place[0])

    def rename_place(self, data):
        idx = [x[2] for x in self.places].index(self.curr_place[2])
        dd = (idx, self.places[idx][2], data[1])
        self.places[idx] = dd
        self.view.cb_places.clear()
        self.view.cb_places.addItems((x[2] for x in self.places))
        self.view.cb_places.setCurrentIndex(idx)
        self.dbu.update_other('PLACES', (dd[2], dd[0]))

    def ask_rename_or_new(self):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.addButton('Add new', QMessageBox.ActionRole)
        box.addButton('Rename', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    def populate_ext_list(self):
        ext_list = self.dbu.select_other('EXT')
        model = MyListModel()
        for ext in ext_list:
            model.append_row(ext[1::-1])       # = (ext[1], ext[0]) = (Extension, ExtID)
        self.view.extList.setModel(model)

    def populate_tag_list(self):
        print('populate_tag_list')

    def populate_author_list(self):
        print('populate_author_list')

    def populate_file_list(self):
        print('populate_file_list')

    def populate_comment_field(self):
        print('populate_comment_field')

    def populate_all_widgets(self):
        self.populate_directory_tree()
        self.populate_file_list()
        self.populate_comment_field()
        self.populate_ext_list()
        self.populate_tag_list()
        self.populate_author_list()
        self.populate_cb_places()

    def populate_directory_tree(self):
        dir_tree = self.dbu.dir_tree_select(dir_id=0, level=0)

        model = TreeModel(dir_tree)

        self.view.dirTree.setModel(model)

    def is_place_available(self):
        return True

    def on_scan_files(self):
        if self.is_place_available():
            _data = self.scan_file_system()
        else:
            _data = self.read_from_file()

        if _data:
            ld = LoadDBData(self._connection, self.curr_place)
            ld.load_data(_data)
            self.populate_directory_tree()

    def scan_file_system(self):
        ext_ = self.get_selected_extensions()
        ext_item, okPressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                   '', QLineEdit.Normal, ext_)
        if okPressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            if root:
                return yield_files(root, ext_item)
            else:
                return ()
        else:
            return ()

    def read_from_file(self):
        return ()

    def get_selected_extensions(self):
        extensions = self.view.extList.selectedIndexes()
        if extensions:
            model = self.view.extList.model()
            model.data(extensions[0], Qt.DisplayRole)
            ext_ = ', '.join(model.data(i, Qt.DisplayRole) for i in extensions)
        else:
            ext_ = ''
        return ext_