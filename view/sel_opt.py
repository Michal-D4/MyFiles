# view/sel_opt.py

from collections import namedtuple

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from view.ui_sel_opt import Ui_SelOpt
# from controller.my_controller import MyController


class SelOpt(QDialog):
    def __init__(self, controller, parent=None):
        super(SelOpt, self).__init__(parent)
        self.ui = Ui_SelOpt()
        self.ui.setupUi(self)

        self.ctrl = controller

        self.ui.chAuthor.stateChanged.connect(self.author_toggle)
        self.ui.chDate.stateChanged.connect(self.date_toggle)
        self.ui.chDirs.stateChanged.connect(self.dir_toggle)
        self.ui.chExt.stateChanged.connect(self.ext_toggle)
        self.ui.chTags.stateChanged.connect(self.tag_toggle)

    def author_toggle(self):
        state = self.ui.chAuthor.isChecked()
        self.ui.eAuthors.setEnabled(state)
        if state and not self.ui.eAuthors.text():
            self.ui.eAuthors.setText(self.ctrl.get_selected_items(self.ctrl.view.authorsList))
        else:
            self.ui.eAuthors.setText('')

    def date_toggle(self):
        state = self.ui.chDate.isChecked()
        self.ui.eDate.setEnabled(state)
        self.ui.dateBook.setEnabled(state)
        self.ui.dateFile.setEnabled(state)

        if state:
            if not self.ui.eDate.text():
                self.ui.eDate.setText('5')
        else:
            self.ui.eDate.setText('')

    def dir_toggle(self):
        if self.ui.chDirs.isChecked():
            self.ui.lDir.setText(self.ctrl.get_selected_items(self.ctrl.view.dirTree))
            if self.ui.lDir.text():
                self.ui.sbLevel.setEnabled(True)
        else:
            self.ui.lDir.setText('')
            self.ui.sbLevel.setEnabled(False)

    def ext_toggle(self):
        if self.ui.chExt.isChecked():
            self.ui.eExt.setEnabled(True)
            self.ui.eExt.setText(self.ctrl.get_selected_items(self.ctrl.view.extList))
        else:
            self.ui.eExt.setEnabled(False)
            self.ui.eExt.setText('')

    def tag_toggle(self):
        state = self.ui.chTags.isChecked()
        self.ui.tagAll.setEnabled(state)
        self.ui.tagAny.setEnabled(state)
        self.ui.eTags.setEnabled(state)
        if state:
            self.ui.eTags.setText(self.ctrl.get_selected_items(self.ctrl.view.tagsList))
        else:
            self.ui.eTags.setText('')

    def get_result(self):
        result = namedtuple('result', 'dir extension tags authors date')
        dir_ = namedtuple('dir', 'use list')
        extension = namedtuple('extension', 'use list')
        tags = namedtuple('tags', 'use match_all list')
        authors = namedtuple('authors', 'use list')
        doc_date = namedtuple('not_older', 'use date file_date')
        ext_ids = self._get_ext_ids()
        dir_ids = self._get_dir_ids()
        tag_ids = self._get_items_id(self.ctrl.view.tagsList)
        author_ids = self._get_items_id(self.ctrl.view.authorsList)
        res = result(dir=dir_(use=self.ui.chDirs.isChecked(), list=dir_ids),
                     extension=extension(use=self.ui.chExt.isChecked(),
                                         list=ext_ids),
                     tags=tags(use=self.ui.chTags.isChecked(),
                               list=tag_ids,
                               match_all=self.ui.tagAll.isChecked()),
                     authors=authors(use=self.ui.chAuthor.isChecked(),
                                     list=author_ids),
                     date=doc_date(use=self.ui.chDate.isChecked(),
                                   date=self.ui.eDate.text(),
                                   file_date=self.ui.dateFile.isChecked()))
        return res

    def _get_dir_ids(self):
        if self.ui.chDirs.isChecked():
            lvl = int(self.ui.sbLevel.text())
            idx = self.ctrl.view.dirTree.currentIndex()
            root_id = int(self.ctrl.view.dirTree.model().data(idx, Qt.UserRole)[0])
            place_id = self.ctrl.get_place_instance().get_curr_place()[1][0]

            ids = ','.join([str(id_[0]) for id_ in
                            self.ctrl.get_db_utils().dir_ids_select(root_id, lvl, place_id)])
            return ids
        return None

    def _get_ext_ids( self ):
        if self.ui.chExt.isChecked():
            sel_idx = self.ctrl.view.extList.selectedIndexes()
            model = self.ctrl.view.extList.model()
            aux = []
            for id_ in sel_idx:
                aux.append(model.data(id_, Qt.UserRole))

            idx = []
            for id in aux:
                if id[0] > 1000:
                    idx.append(id[0]-1000)
                else:
                    idx += self._ext_in_group(id[0])

            idx.sort()
            return ','.join([str(id_) for id_ in idx])
        return None

    def _ext_in_group(self, gr_id):
        curr = self.ctrl.get_db_utils().select_other('EXT_ID_IN_GROUP', (gr_id,))
        idx = []
        for id_ in curr:
            idx.append(id_[0])

        return idx

    def _get_items_id(self, view):
        if self.ui.chTags.isChecked():
            sel_idx = view.selectedIndexes()
            model = view.model()
            aux = []
            for id_ in sel_idx:
                aux.append(model.data(id_, Qt.UserRole))

            aux.sort()
            return ','.join([str(id_) for id_ in aux])

        return None

