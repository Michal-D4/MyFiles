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

    def on_ext_list_change(self, action):
        if action == 'add':
            ext_item, okPressed = QInputDialog.getText(self.view.extList, "Input extension",
                                                       "", QLineEdit.Normal)
            if okPressed:
                self.add_extension(ext_item)
        elif action == 'remove':
            self.remove_extension()
        else:
            pass

    def add_extension(self, ext_):
        cnt = self.dbu.select_other('HAS_EXT', (ext_,)).fetchone()
        if cnt[0] == 0:
            idx = self.dbu.insert_other('EXT', {'ext': ext_})
            if idx > 0:
                mod = self.view.extList.model()
                mod.appendData((ext_, idx))
                self.view.extList.setCurrentIndex(mod.createIndex(mod.rowCount() - 1, 0, 0))

    def remove_extension(self):
        mod = self.view.extList.model()
        index = self.view.extList.currentIndex()
        ext_id = mod.data(index, mod.MyDataRole)
        if self.allowed_removal(ext_id):
            self.dbu.delete_other('EXT', (ext_id,))
            mod.removeRows(index.row())
            self.view.extList.setCurrentIndex(self.view.extList.currentIndex())

    def allowed_removal(self, ext_item):
        res = self.dbu.select_other('EXT_IN_FILES', (ext_item,)).fetchone()
        return not res

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
        cb = self.view.cb_places
        cb.blockSignals(True)
        cb.clear()
        plc = self.dbu.select_other('PLACES')
        if plc:
            self.places = list(plc)
            cb.addItems((x[2] for x in self.places))
        cb.setCurrentIndex(0)
        self.curr_place = self.places[0]
        cb.blockSignals(False)

    def on_change_data(self, sender, data):
        '''
        handle of changing data in widgets
        :param sender: - widget name (consider the widget itself)
        :param data:   - widget specific data
        :return:
        '''
        print('|--> MyController.on_change_data', sender, data)
        if sender == 'cb_places':
            self.add_place(data)

    def add_place(self, data):
        idx = data[0]
        if idx >= len(self.places):
            res = self.ask_rename_or_new()
            if res == 0:                # add new
                self.curr_place = (idx, data[1], data[1])
                self.places.append(self.curr_place)
                self.dbu.insert_other('PLACES', self.curr_place)
            elif res == 1:              # rename
                self.rename_place((self.curr_place[0], data[1]))
            else:                       # cancel
                cb = self.view.cb_places
                cb.clear()
                cb.addItems((x[2] for x in self.places))
                cb.setCurrentIndex(self.curr_place[0])
        else:
            self.curr_place = self.places[idx]

    def rename_place(self, data):
        idx = [x[2] for x in self.places].index(self.curr_place[2])
        dd = (idx, self.places[idx][2], data[1])
        self.places[idx] = dd
        cb = self.view.cb_places
        cb.clear()
        cb.addItems((x[2] for x in self.places))
        cb.setCurrentIndex(idx)
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
        print('type of MyListModel', type(MyListModel))
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

    def on_scan_files(self):
        ext_ = self.get_selected_extensions()

        ext_item, okPressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                   '', QLineEdit.Normal, ext_)
        if okPressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            if root:
                _data = yield_files(root, ext_item)

                ld = LoadDBData(self._connection, self.curr_place)
                ld.load_data(_data)
                self.populate_directory_tree()

    def get_selected_extensions(self):
        extensions = self.view.extList.selectedIndexes()
        if extensions:
            model = self.view.extList.model()
            model.data(extensions[0], Qt.DisplayRole)
            ext_ = ', '.join(model.data(i, Qt.DisplayRole) for i in extensions)
        else:
            ext_ = ''
        return ext_