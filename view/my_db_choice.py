import sys
import pickle

from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem
from PyQt5.QtCore import pyqtSignal

from view.ui_db_choice import Ui_ChoiceDB

SKIP_OPEN_DIALOG = 2


class MyDBChoice(QDialog):
    open_DB_signal = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super(MyDBChoice, self).__init__(parent)

        self.ui_db_choice = Ui_ChoiceDB()
        self.ui_db_choice.setupUi(self)

        self.ui_db_choice.newButton.clicked.connect(self.new_db)
        self.ui_db_choice.okButton.clicked.connect(self.accept)
        self.ui_db_choice.addButton.clicked.connect(self.add)
        self.ui_db_choice.delButton.clicked.connect(self.delete)
        self.ui_db_choice.listOfBDs.currentRowChanged.connect(self.row_changed)

        self.ui_db_choice.listOfBDs.setSelectionMode(1)

        self.init_data = None
        self.load_init_data()
        self.initiate_window(self.init_data)

    def row_changed(self, curr_row):
        self.init_data[1] = curr_row

    def add(self):
        options = QFileDialog.Options(QFileDialog.HideNameFilterDetails |
                                      QFileDialog.DontConfirmOverwrite)
        file_name, _ = QFileDialog.getSaveFileName(self, "Create DB", "",
                                                  options=options)
        if file_name:
            self.create_new_db(file_name)

    def delete(self):
        idx = self.ui_db_choice.listOfBDs.currentIndex()
        if idx.isValid():
            i = idx.row()
            self.ui_db_choice.listOfBDs.takeItem(idx.row())
            self.init_data[2].remove(self.init_data[2][i])

    def accept(self):
        self.emit_open_dialog()
        self.save_init_data()
        super(MyDBChoice, self).accept()

    def new_db(self):
        options = QFileDialog.Options(QFileDialog.HideNameFilterDetails |
                                      QFileDialog.DontConfirmOverwrite)
        file_name, _ = QFileDialog.getSaveFileName(self, "Create DB", "",
                                                  options=options)
        if file_name:
            if not file_name in self.init_data[2]:
                self.create_new_db(file_name)
                self.open_DB_signal.emit(file_name, True)
                self.save_init_data()
                super(MyDBChoice, self).accept()
            else:
                self.ui_db_choice.listOfBDs.setCurrentRow(self.init_data[2].index(file_name))

    def create_new_db(self, file_name):
        if not file_name in self.init_data[2]:
            self.init_data[2].append(file_name)
            item = QListWidgetItem(file_name)
            self.ui_db_choice.listOfBDs.addItem(item)
            self.ui_db_choice.listOfBDs.setCurrentItem(item)
            self.ui_db_choice.okButton.setDisabled(False)
        else:
            self.ui_db_choice.listOfBDs.setCurrentRow(self.init_data[2].index(file_name))
            # self.init_data[1] = self.init_data[2].index(file_name)

        self.init_data[0] = self.ui_db_choice.skipThisWindow.checkState()

    def emit_open_dialog(self):
        file_name = self.ui_db_choice.listOfBDs.currentItem().text()
        self.open_DB_signal.emit(file_name, False)

    def initiate_window(self, init_data):
        '''
        Initiate data in widgets
        :param init_data: list of 3 items:
            1 - skipThisWindow flag, 0 or 2; 2 - skip
            2 - index of last used DB
            3 - list of DBs
        :return: None
        '''
        if init_data:
            self.ui_db_choice.skipThisWindow.setCheckState(init_data[0])
            db_index = init_data[1]
            if init_data[2]:
                for db in init_data[2]:
                    self.ui_db_choice.listOfBDs.addItem(db)
                self.ui_db_choice.listOfBDs.setCurrentRow(db_index)
            if self.ui_db_choice.listOfBDs.count() == 0:
                self.ui_db_choice.okButton.setDisabled(True)

    def get_file_name(self):
        return self.init_data[2][self.init_data[1]]

    def load_init_data(self):
        _data = [0, 0, []]
        try:
            with open('setup.pcl', 'rb') as f:
                _data = pickle.load(f)
                file = _data[2][_data[1]]
                _data[2].sort()
                _data[1] = _data[2].index(file)
        except (EOFError, FileNotFoundError):
            pass
        self.init_data = _data

    def save_init_data(self):
        self.init_data[0] = self.ui_db_choice.skipThisWindow.checkState()
        with open('setup.pcl', 'wb') as f:
            pickle.dump(self.init_data, f)

    def skip_open_dialog(self):
        return self.init_data[0] == SKIP_OPEN_DIALOG


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    myapp = MyDBChoice()
    if myapp.exec_() == QDialog.Accepted:
        print('name of DB file =', myapp.get_file_name())
    sys.exit(app.exec_())


