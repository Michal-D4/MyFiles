# view/my_db_choice.py

from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QCoreApplication
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem

from view.ui_db_choice import Ui_ChoiceDB
from model.helper import Shared

SKIP_OPEN_DIALOG = 2
APP_NAME = 'File manager'
ORG_DOMAIN = 'fake_domain.org'
ORG_NAME = 'Fake organization'


class DBChoice(QDialog):
    open_DB_signal = pyqtSignal(str, bool, bool)

    def __init__(self, parent=None):
        super(DBChoice, self).__init__(parent)

        self.ui_db_choice = Ui_ChoiceDB()
        self.ui_db_choice.setupUi(self)
        Shared['DB choice dialog'] = self

        self.ui_db_choice.okButton.clicked.connect(self.accept)
        self.ui_db_choice.newButton.clicked.connect(self.new_db)
        self.ui_db_choice.addButton.clicked.connect(self.add)
        self.ui_db_choice.delButton.clicked.connect(self.delete)
        self.ui_db_choice.listOfBDs.currentRowChanged.connect(self.row_changed)

        QCoreApplication.setApplicationName(APP_NAME)
        QCoreApplication.setOrganizationDomain(ORG_DOMAIN)
        QCoreApplication.setOrganizationName(ORG_NAME)

        self.ui_db_choice.listOfBDs.setSelectionMode(1)

        self.init_data = None
        self.last_db_no = -1
        self.load_init_data()
        self.initiate_window(self.init_data)

    def row_changed(self, curr_row):
        self.init_data[1] = curr_row

    def add(self):
        """
        the program is called by click of 'Add' button of this dialog
        :return:
        """
        options = QFileDialog.Options(QFileDialog.HideNameFilterDetails |
                                      QFileDialog.DontConfirmOverwrite)
        file_name, _ = QFileDialog.getOpenFileName(self, "Create DB", "", options=options)
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
        super(DBChoice, self).accept()

    def new_db(self):
        """
        the program is called by click of 'New' button of this dialog
        :return:
        """
        options = QFileDialog.Options(QFileDialog.HideNameFilterDetails |
                                      QFileDialog.DontConfirmOverwrite)
        file_name, _ = QFileDialog.getSaveFileName(self, "Create DB", "",
                                                  options=options)
        if file_name:
            if not (file_name in self.init_data[2]):
                self.create_db(file_name)
                self.open_DB_signal.emit(file_name, True, False)
                super(DBChoice, self).accept()
            else:
                self.ui_db_choice.listOfBDs.setCurrentRow(self.init_data[2].index(file_name))

    def create_new_db(self, file_name):
        if not (file_name in self.init_data[2]):
            self.create_db(file_name)
        else:
            self.ui_db_choice.listOfBDs.setCurrentRow(self.init_data[2].index(file_name))

        self.init_data[0] = self.ui_db_choice.skipThisWindow.checkState()

    def create_db(self, file_name):
        self.init_data[2].append(file_name)
        item = QListWidgetItem(file_name)
        self.ui_db_choice.listOfBDs.addItem(item)
        self.ui_db_choice.listOfBDs.setCurrentItem(item)
        self.ui_db_choice.okButton.setDisabled(False)

    def emit_open_dialog(self):
        if self.ui_db_choice.listOfBDs.currentIndex().isValid():
            file_name = self.ui_db_choice.listOfBDs.currentItem().text()
            self.open_DB_signal.emit(file_name, False, self.last_db_no == self.init_data[1])

    def initiate_window(self, init_data):
        '''
        Initiate data in widgets
        :param init_data: list of 3 items:
            0 - skipThisWindow flag, 0 or 2; 2 - skip
            1 - index of last used DB
            2 - list of DBs
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
        setting = QSettings()
        if setting.contains('DB/init_data'):
            _data = setting.value('DB/init_data', [0, 0, []])
        else:
            _data = [0, 0, []]
        self.last_db_no = _data[1]
        self.init_data = _data

    def save_init_data(self):
        self.init_data[0] = self.ui_db_choice.skipThisWindow.checkState()
        self._save_settings()

    def _save_settings(self):
        setting = QSettings()
        setting.setValue('DB/init_data', QVariant(self.init_data))

    def skip_open_dialog(self):
        res = self.init_data[0] == SKIP_OPEN_DIALOG
        self.init_data[0] = 0
        self._save_settings()
        return res


if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    myapp = DBChoice()
    if myapp.exec_() == QDialog.Accepted:
        print('name of DB file =', myapp.get_file_name())
    sys.exit(app.exec_())


