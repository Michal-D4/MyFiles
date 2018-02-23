# view/main_flow.py

from PyQt5.QtCore import (pyqtSignal, QSettings, QVariant, QSize, Qt, QUrl, QEvent, QMimeData)
from PyQt5.QtGui import QResizeEvent, QDrag, QPixmap, QDropEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QMenu

from view.ui_main_window import Ui_MainWindow
from model.helper import *


class AppWindow(QMainWindow):
    change_data_signal = pyqtSignal(str)   # str - name of action
    scan_files_signal = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        Shared['AppWindow'] = self

        self.old_size = None
        self.old_pos = None
        self.restore_setting()

        self.set_actions()

        self.set_menus()

        self.setup_context_menu()

        self.open_dialog = Shared['DB choice dialog']

    def set_actions(self):
        """
        Connect handlers to tool bar actions and widgets' events
        :return:
        """
        self.ui.actionOpenDB.triggered.connect(lambda: self.open_dialog.exec_())
        self.ui.actionScanFiles.triggered.connect(lambda: self.scan_files_signal.emit())
        self.ui.actionGetFiles.triggered.connect(lambda: self.change_data_signal.emit('Select files'))
        self.ui.actionFavorites.triggered.connect(lambda: self.change_data_signal.emit('Favorites'))

        self.ui.cb_places.currentIndexChanged.connect(lambda: self.change_data_signal.emit('Change place'))
        self.ui.commentField.anchorClicked.connect(self.ref_clicked)
        self.ui.filesList.doubleClicked.connect(lambda: self.change_data_signal.emit('File_doubleClicked'))

        self.ui.dirTree.startDrag = self._start_drag
        self.ui.dirTree.dropEvent = self._drop_event
        self.ui.filesList.startDrag = self._start_drag_files

        self.ui.filesList.resizeEvent = self.resize_event

    def _drop_event(self, event: QDropEvent):
        mime_data: QMimeData = event.mimeData()
        index = self.ui.dirTree.indexAt(event.pos())

        act = self._set_action(index, mime_data, event.pos())
        if act & (DropMoveFolder | DropMoveFile):
            event.setDropAction(Qt.MoveAction)
        elif act & (DropCopyFolder | DropCopyFile):
            event.setDropAction(Qt.CopyAction)

        res = self.ui.dirTree.model().dropMimeData(mime_data, act, -1, -1, index)
        if res:
            event.accept()
        else:
            event.ignore()

    def _set_action(self, index, mime_data, pos):
        if mime_data.hasFormat(MimeTypes[real_folder]):
            if self.ui.dirTree.model().is_virtual(index):
                return DropCopyFolder
            return DropNoAction
        if mime_data.hasFormat(MimeTypes[file]):
            if self.ui.dirTree.model().is_virtual(index):
                return DropCopyFile
            return self._ask_action_file(pos)
        if mime_data.hasFormat(MimeTypes[file_virtual]):
            return self._ask_action_file(pos)
        if mime_data.hasFormat(MimeTypes[virtual_folder]):
            return self._ask_action_folder(pos)
        return DropNoAction

    def _ask_action_file(self, pos):
        return self._ask_action_folder(pos) * 4

    def _ask_action_folder(self, pos):
        menu = QMenu(self)
        menu.addAction('Copy')
        menu.addAction('Move')
        menu.addSeparator()
        menu.addAction('Cancel')
        action = menu.exec_(self.ui.dirTree.mapToGlobal(pos))
        if action:
            if action.text() == 'Copy':
                return DropCopyFolder
            elif action.text() == 'Move':
                return DropMoveFolder
        return DropNoAction

    def _start_drag_files(self, action):
        drag = QDrag(self)
        drag.setPixmap(QPixmap(":/image/List.png"))
        indexes = self.ui.filesList.selectionModel().selectedRows()
        mime_data = self.ui.filesList.model().mimeData(indexes)
        drag.setMimeData(mime_data)
        drag.exec_(Qt.CopyAction)

    def _start_drag(self, action):
        drag = QDrag(self)
        drag.setPixmap(QPixmap(":/image/Folder.png"))
        indexes = self.ui.dirTree.selectionModel().selectedRows()
        mime_data = self.ui.dirTree.model().mimeData(indexes)
        drag.setMimeData(mime_data)
        if mime_data.hasFormat(MimeTypes[real_folder]):
            drag.exec_(Qt.CopyAction)
        elif mime_data.hasFormat(MimeTypes[virtual_folder]):
            drag.exec_(Qt.MoveAction)

    def set_menus(self):
        """
        Set actions of main menu
        :return:
        """
        menu = QMenu(self)
        change_font = menu.addAction('Change Font')
        set_fields = menu.addAction('Set fields')
        self.ui.btnOption.setMenu(menu)
        change_font.triggered.connect(lambda: self.change_data_signal.emit('change_font'))
        set_fields.triggered.connect(lambda: self.change_data_signal.emit('Set fields'))

        menu2 = QMenu(self)
        sel_opt = menu2.addAction('Selection options')
        self.ui.btnGetFiles.setMenu(menu2)
        sel_opt.triggered.connect(lambda: self.change_data_signal.emit('Selection options'))

    def setup_context_menu(self):
        """
        Set context menus for each widget
        :return:
        """
        self.ui.dirTree.customContextMenuRequested.connect(self._dir_menu)
        self.ui.filesList.customContextMenuRequested.connect(self._file_menu)
        self.ui.extList.customContextMenuRequested.connect(self._ext_menu)
        self.ui.tagsList.customContextMenuRequested.connect(self._tag_menu)
        self.ui.authorsList.customContextMenuRequested.connect(self._author_menu)

    def _file_menu(self, pos):
        idx = self.ui.filesList.indexAt(pos)
        if idx.isValid():
            menu = QMenu(self)
            menu.addAction('Open')
            menu.addAction('Open folder')
            menu.addAction('Add to favorites')
            menu.addAction('Delete row')
            menu.addSeparator()
            menu.addAction('Copy file name')
            menu.addAction('Copy path')
            menu.addSeparator()
            menu.addAction('Rename file')
            menu.addAction('Copy file(s)')
            if self.ui.filesList.model().in_real_folder(idx):
                menu.addAction('Move file(s)')
                menu.addAction('Delete file(s)')
            action = menu.exec_(self.ui.filesList.mapToGlobal(pos))
            if action:
                self.change_data_signal.emit('File {}'.format(action.text()))

    def _ext_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        menu.addAction('Create group')
        action = menu.exec_(self.ui.extList.mapToGlobal(pos))
        if action:
            self.change_data_signal.emit('Ext {}'.format(action.text()))

    def _tag_menu(self, pos):
        idx = self.ui.tagsList.indexAt(pos)
        menu = QMenu(self)
        menu.addAction('Remove unused')
        if idx.isValid():
            menu.addAction('Scan in names')
            menu.addAction('Rename')

        action = menu.exec_(self.ui.tagsList.mapToGlobal(pos))
        if action:
            self.change_data_signal.emit('Tag {}'.format(action.text()))

    def _author_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        action = menu.exec_(self.ui.authorsList.mapToGlobal(pos))
        if action:
            self.change_data_signal.emit('Author {}'.format(action.text()))

    def _dir_menu(self, pos):
        idx = self.ui.dirTree.indexAt(pos)
        menu = QMenu(self)
        menu.addAction('Remove empty folders')
        if idx.isValid():
            if self.ui.dirTree.model().is_virtual(idx):
                if not self.ui.dirTree.model().is_favorites(idx):
                    menu.addSeparator()
                    menu.addAction('Rename folder')
                    menu.addAction('Delete folder')
            else:
                parent = self.ui.dirTree.model().parent(idx)
                if self.ui.dirTree.model().is_virtual(parent):
                    menu.addSeparator()
                    menu.addAction('Delete folder')
                menu.addAction('Rescan dir')
            menu.addSeparator()
            menu.addAction('Create virtual folder')
            menu.addAction('Create virtual folder as child')
        else:
            menu.addAction('Create virtual folder')

        action = menu.exec_(self.ui.dirTree.mapToGlobal(pos))
        if action:
            self.change_data_signal.emit('Dirs {}'.format(action.text()))

    def ref_clicked(self, href):
        """
        Invoke methods to change file information: tags, authors, comment
        :param href:
        :return:
        """
        self.ui.commentField.setSource(QUrl())
        self.change_data_signal.emit(href.toString())

    def resizeEvent(self, event):
        """
        resizeEvent - when changed main window. To save size for next run
        :param event:
        :return:
        """
        super().resizeEvent(event)
        self.old_size = event.oldSize()
        settings = QSettings()
        settings.setValue("MainFlow/Size", QVariant(self.size()))

    def resize_event(self, event: QResizeEvent):
        """
        resizeEvent of filesList, to change width of columns
        :param event:
        :return:
        """
        old_w = event.oldSize().width()
        w = event.size().width()
        if not old_w == w:
            self.change_data_signal.emit('Resize columns')

    def changeEvent(self, event):
        """
        Save size and position of window before it maximized
        :param event:
        :return:
        """
        if event.type() == QEvent.WindowStateChange:
            settings = QSettings()
            if event.oldState() == Qt.WindowMaximized:
                settings.setValue("MainFlow/isFullScreen", QVariant(False))
            elif event.oldState() == Qt.WindowNoState and \
                    self.windowState() == Qt.WindowMaximized:
                settings.setValue("MainFlow/isFullScreen", QVariant(True))
                if self.old_size:
                    settings.setValue("MainFlow/Size", QVariant(self.old_size))
                if self.old_pos:
                    settings.setValue("MainFlow/Position", QVariant(self.old_pos))
        else:
            super().changeEvent(event)

    def moveEvent(self, event):
        """
        Save new position of window
        :param event:
        :return:
        """
        self.old_pos = event.oldPos()
        settings = QSettings()
        settings.setValue("MainFlow/Position", QVariant(self.pos()))
        super().moveEvent(event)

    def restore_setting(self):
        settings = QSettings()
        if settings.contains("MainFlow/Size"):
            size = settings.value("MainFlow/Size", QSize(640, 480))
            self.resize(size)
            position = settings.value("MainFlow/Position")
            self.move(position)
            self.restoreState(settings.value("MainFlow/State"))
            self.restoreState(settings.value("MainFlow/State"))
            self.ui.splitter_files.restoreState(settings.value("FilesSplitter"))
            self.ui.opt_splitter.restoreState(settings.value("OptSplitter"))
            self.ui.main_splitter.restoreState(settings.value("MainSplitter"))
            if settings.value("MainFlow/isFullScreen", False, type=bool):
                self.showMaximized()
        else:
            self.ui.main_splitter.setStretchFactor(0, 2)
            self.ui.main_splitter.setStretchFactor(1, 5)
            self.ui.main_splitter.setStretchFactor(2, 1)

            self.ui.splitter_files.setStretchFactor(0, 5)
            self.ui.splitter_files.setStretchFactor(1, 2)

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
        self.open_dialog.save_init_data()
        settings = QSettings()
        settings.setValue("MainFlow/State", QVariant(self.saveState()))
        settings.setValue("FilesSplitter", QVariant(self.ui.splitter_files.saveState()))
        settings.setValue("OptSplitter", QVariant(self.ui.opt_splitter.saveState()))
        settings.setValue("MainSplitter", QVariant(self.ui.main_splitter.saveState()))
        super(AppWindow, self).closeEvent(event)

