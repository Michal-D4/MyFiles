# view/main_flow.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QComboBox, QMenu, QTreeView
from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QSize, Qt, QModelIndex
from PyQt5.QtGui import QMouseEvent

from view.my_db_choice import MyDBChoice
from view.ui_new_view import Ui_MainWindow


class MainFlow(QMainWindow):
    change_data_signal = pyqtSignal(str, tuple)   # str - name of Widget, tuple - data
    scan_files_signal = pyqtSignal()

    def __init__(self, parent=None, open_dialog=MyDBChoice):
        QWidget.__init__(self, parent)
        self.ui_main = Ui_MainWindow()
        self.ui_main.setupUi(self)

        self.ui_main.cb_places = QComboBox()
        self.ui_main.cb_places.setEditable(True)
        self.ui_main.toolBar.addWidget(self.ui_main.cb_places)

        self.restore_setting()

        self.ui_main.actionOpenDB.triggered.connect(self.open_data_base)
        self.ui_main.actionScanFiles.triggered.connect(self.scan_files)
        self.ui_main.actionGetFiles.triggered.connect(self.go)

        self.ui_main.cb_places.currentIndexChanged.connect(self.change_place)
        self.ui_main.filesList.clicked.connect(self.file_changed)

        self.ui_main.filesList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.filesList.customContextMenuRequested.connect(self._file_pop_menu)

        self.ui_main.commentField.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.commentField.customContextMenuRequested.connect(self._comment_menu)

        self.open_dialog = open_dialog

    def _comment_menu(self, pos):
        menu = QMenu(self)
        edit_tags = menu.addAction('Edit key words')
        edit_authors = menu.addAction('Edit authors')
        edit_comment = menu.addAction('Edit comment')
        action = menu.exec_(self.ui_main.commentField.mapToGlobal(pos))
        if action:
            print('|---> _comment_menu', action.text())
            self.change_data_signal.emit(action.text(), ())

    def _file_pop_menu(self, pos):
        # todo method _file_pop_menu not implemented yet -- not clear yet
        menu = QMenu(self)
        action1 = menu.addAction('Delete')
        action2 = menu.addAction('Open')
        action = menu.exec_(self.ui_main.filesList.mapToGlobal(pos))
        if action:
            print('|---> _file_pop_menu', action.text())
            self.change_data_signal.emit(action.text(), ())

    def file_changed(self, curr_idx: QModelIndex):
        idx_ = self.ui_main.filesList.model().data(curr_idx, Qt.UserRole)
        self.change_data_signal.emit('commentField', idx_)

    def change_place(self, idx):
        self.change_data_signal.emit('cb_places', (idx, self.ui_main.cb_places.currentText()))

    def restore_setting(self):
        settings = QSettings('myorg', 'myapp')
        if settings.contains("MainFlow/Size"):
            size = settings.value("MainFlow/Size", QSize(600, 500))
            self.resize(size)
            position = settings.value("MainFlow/Position")
            self.move(position)
            self.restoreState(settings.value("MainFlow/State"))
            self.restoreState(settings.value("MainFlow/State"))
            self.ui_main.splitter_files.restoreState(settings.value("FilesSplitter"))
            self.ui_main.opt_splitter.restoreState(settings.value("OptSplitter"))
            self.ui_main.main_splitter.restoreState(settings.value("MainSplitter"))
        else:
            self.ui_main.main_splitter.setStretchFactor(0, 2)
            self.ui_main.main_splitter.setStretchFactor(1, 5)
            self.ui_main.main_splitter.setStretchFactor(2, 1)

            self.ui_main.splitter_files.setStretchFactor(0, 5)
            self.ui_main.splitter_files.setStretchFactor(1, 2)

    def scan_files(self):
        self.scan_files_signal.emit()

    def go(self):
        # todo - implement file selection according selected ext., authors, tags, root
        print('go ====>')
        params = ()
        self.change_data_signal.emit('advanced_file_list', params)

    def open_data_base(self):
        """
        Open DB with click button on toolbar
        :return:
        """
        self.open_dialog.exec_()

    def first_open_data_base(self):
        """
        Open DB when application starts
        :return:
        """
        if not self.open_dialog.skip_open_dialog():
            self.open_dialog.exec_()
        else:
            self.open_dialog.emit_open_dialog()
        self.ui_main.dirTree.mousePressEvent = self.mousePressEvent

    def mousePressEvent(self, event: QMouseEvent):
        """
        Deselect all when click on empty place
        :param event:
        :return:
        """
        self.ui_main.dirTree.clearSelection()
        QTreeView.mousePressEvent(self.ui_main.dirTree, event)

    def closeEvent(self, event):
        settings = QSettings('myorg', 'myapp')
        settings.setValue("MainFlow/Size", QVariant(self.size()))
        settings.setValue("MainFlow/Position",
                          QVariant(self.pos()))
        settings.setValue("MainFlow/State",
                          QVariant(self.saveState()))
        settings.setValue("FilesSplitter",
                          QVariant(self.ui_main.splitter_files.saveState()))
        settings.setValue("OptSplitter",
                          QVariant(self.ui_main.opt_splitter.saveState()))
        settings.setValue("MainSplitter",
                          QVariant(self.ui_main.main_splitter.saveState()))
        # event.accept()
        super(MainFlow, self).closeEvent(event)

