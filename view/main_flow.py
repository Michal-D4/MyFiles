# view/main_flow.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QMenu
from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QSize, Qt, QUrl, QCoreApplication

from view.my_db_choice import MyDBChoice
from view.ui_new_view import Ui_MainWindow

APP_NAME = 'File manager'
ORG_DOMAIN = 'fake_domain.org'
ORG_NAME = 'Fake organization'


class MainFlow(QMainWindow):
    change_data_signal = pyqtSignal(str)   # str - name of action
    scan_files_signal = pyqtSignal()

    def __init__(self, parent=None, open_dialog=MyDBChoice):
        QWidget.__init__(self, parent)
        self.ui_main = Ui_MainWindow()
        self.ui_main.setupUi(self)

        QCoreApplication.setApplicationName(APP_NAME)
        QCoreApplication.setOrganizationDomain(ORG_DOMAIN)
        QCoreApplication.setOrganizationName(ORG_NAME)

        self.restore_setting()

        self.ui_main.actionOpenDB.triggered.connect(lambda: self.open_dialog.exec_())
        self.ui_main.actionScanFiles.triggered.connect(lambda: self.
                                                       scan_files_signal.emit())
        self.ui_main.actionGetFiles.triggered.connect(lambda:
                                                      self.change_data_signal.
                                                      emit('get_sel_files'))
        self.ui_main.actionFavorites.triggered.connect(lambda:
                                                       self.change_data_signal.
                                                       emit('Favorites'))

        self.ui_main.cb_places.currentIndexChanged.connect(self.change_place)
        self.ui_main.filesList.resizeEvent = self.resize_event
        self.ui_main.filesList.doubleClicked.connect(lambda:
                                                     self.change_data_signal.
                                                     emit('File_doubleClicked'))
        menu = QMenu(self)
        change_font = menu.addAction('Change Font')
        opt2 = menu.addAction('options 2')
        self.ui_main.btnOption.setMenu(menu)
        change_font.triggered.connect(lambda: self.change_data_signal.
                                      emit('change_font'))

        menu2 = QMenu(self)
        sel_opt = menu2.addAction('Selection options')
        self.ui_main.btnGetFiles.setMenu(menu2)

        sel_opt.triggered.connect(lambda: self.change_data_signal.
                                  emit('advanced_file_list'))

        self.setup_context_menu()

        self.ui_main.commentField.anchorClicked.connect(self.ref_clicked)

        self.open_dialog = open_dialog

        lines = ['9999-99-99 99', 'Pages 99', '9 999 999 999 ']
        self.widths = [self.ui_main.filesList.fontMetrics().boundingRect(line)
                           .width() for line in lines]

    def setup_context_menu(self):
        self.ui_main.filesList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.filesList.customContextMenuRequested.connect(self._file_menu)

        self.ui_main.extList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.extList.customContextMenuRequested.connect(self._ext_menu)

        self.ui_main.tagsList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.tagsList.customContextMenuRequested.connect(self._tag_menu)

        self.ui_main.authorsList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.authorsList.customContextMenuRequested.connect(self._author_menu)

        self.ui_main.dirTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.dirTree.customContextMenuRequested.connect(self._dir_menu)

    def _file_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Open')
        menu.addAction('Open folder')
        menu.addAction('Add to favorites')
        menu.addAction('Delete')
        menu.addSeparator()
        menu.addAction('Copy file name')
        menu.addAction('Copy full path')
        action = menu.exec_(self.ui_main.filesList.mapToGlobal(pos))
        if action:
            self.change_data_signal.emit(action.text())

    def _ext_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        menu.addAction('Create group')
        action = menu.exec_(self.ui_main.extList.mapToGlobal(pos))
        if action:
            act = 'Ext {}'.format(action.text())
            self.change_data_signal.emit(act)

    def _tag_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        menu.addAction('Scan in names')
        action = menu.exec_(self.ui_main.tagsList.mapToGlobal(pos))
        if action:
            act = 'Tag {}'.format(action.text())
            self.change_data_signal.emit(act)

    def _author_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        action = menu.exec_(self.ui_main.authorsList.mapToGlobal(pos))
        if action:
            act = 'Author {}'.format(action.text())
            self.change_data_signal.emit(act)

    def _dir_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Update tree')
        action = menu.exec_(self.ui_main.dirTree.mapToGlobal(pos))
        if action:
            act = 'Dirs {}'.format(action.text())
            self.change_data_signal.emit(act)

    def ref_clicked(self, argv_1):
        self.ui_main.commentField.setSource(QUrl())
        self.change_data_signal.emit(argv_1.toString())

    def resize_event(self, event):
        """
        Resize columns width of file list
        :param event:
        :return:
        """
        self.ui_main.filesList.blockSignals(True)
        w = event.size().width()
        ww = [sum(self.widths)] + self.widths
        if w > ww[0]*2:
            ww[0] = w - ww[0]
        for k in range(4):
            self.ui_main.filesList.setColumnWidth(k, ww[k])
        self.ui_main.filesList.blockSignals(False)

    def change_place(self, idx):
        self.change_data_signal.emit('cb_places')

    def restore_setting(self):
        settings = QSettings()
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

    def first_open_data_base(self):
        """
        Open DB when application starts
        :return:
        """
        if not self.open_dialog.skip_open_dialog():
            self.open_dialog.exec_()
        else:
            self.open_dialog.emit_open_dialog()

    def closeEvent(self, event):
        settings = QSettings()
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
        super(MainFlow, self).closeEvent(event)

