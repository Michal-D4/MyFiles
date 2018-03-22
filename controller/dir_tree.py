# controller/dir_tree.py

import os

from PyQt5.QtCore import (Qt, QModelIndex, QItemSelectionModel, QSettings,
                          QVariant, QPersistentModelIndex)
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QTreeView

from controller.places import Places
from controller.edit_tree_model import EditTreeModel, EditTreeItem
from model.helper import Shared


class DirTree():
    """
    manage all folders to save files:
    real folders,
    group of folders,
    virtual folders,
    favorites folder,
    link to folders (aka copy)
    """

    def __init__(self, view: QTreeView, places, db_utils):
        self.dirTree = view
        self.places = places
        self.dbu = db_utils

    def add_group_folder(self):
        """
        group of real folders - organise for better vision
        """
        folder_name = '<Group name>'
        new_name, ok_ = QInputDialog.getText(self.dirTree,
                                             'Input folder name', '',
                                             QLineEdit.Normal, folder_name)
        print('--> _add_group_folder', new_name, ok_)
        if ok_:
            curr_idx = self.dirTree.currentIndex()
            idx_list = self._curr_selected_dirs(curr_idx)

            d_dat = self.dirTree.model().data(curr_idx, Qt.UserRole)
            new_parent = (new_name, d_dat.parent_id, self.places.get_curr_place().id_, 3)
            new_parent_id = self.dbu.insert_other('DIR', new_parent)
            self.dirTree.model().create_new_parent(curr_idx, (new_parent_id, *new_parent), idx_list)

    def _curr_selected_dirs(self, curr_idx):
        if not self.dirTree.selectionModel().isSelected(curr_idx):
            self.dirTree.selectionModel().select(curr_idx, QItemSelectionModel.SelectCurrent)
        selected_indexes = self.dirTree.selectionModel().selectedRows()

        idx_list = []
        for idx in selected_indexes:
            idx_list.append(QPersistentModelIndex(idx))

        return idx_list

    def create_virtual_child(self):
        folder_name = 'New folder'
        new_name, ok_ = QInputDialog.getText(self.dirTree,
                                             'Input folder name', '',
                                             QLineEdit.Normal, folder_name)
        if ok_:
            cur_idx = self.dirTree.currentIndex()
            self._create_virtual_folder(new_name, cur_idx)

    def create_virtual(self):
        folder_name = 'New folder'
        new_name, ok_ = QInputDialog.getText(self.dirTree,
                                             'Input folder name', '',
                                             QLineEdit.Normal, folder_name)
        if ok_:
            cur_idx = self.dirTree.currentIndex()
            parent = self.dirTree.model().parent(cur_idx)
            self._create_virtual_folder(new_name, parent)

    def _create_virtual_folder(self, folder_name, parent):
        if parent.isValid():
            parent_id = self.dirTree.model().data(parent, role=Qt.UserRole).dir_id
        else:
            parent_id = 0
        place_id = self.places.get_curr_place().id_
        dir_id = self.dbu.insert_other('DIR', (folder_name, parent_id, place_id, 2))

        item = EditTreeItem((folder_name, ), (dir_id, parent_id, 2, folder_name))

        self.dirTree.model().append_child(item, parent)

    def delete_virtual(self):
        cur_idx = self.dirTree.currentIndex()
        parent = self.dirTree.model().parent(cur_idx)
        parent_id = 0 if not parent.isValid() else \
                    self.dirTree.model().data(parent, role=Qt.UserRole).dir_id
        dir_id = self.dirTree.model().data(cur_idx, role=Qt.UserRole).dir_id
        print('--> delete_virtual: parent_id {}, dir_id {}'.format(parent_id, dir_id))

        if self._exist_in_virt_dirs(dir_id, parent_id):
            self.dbu.delete_other('FROM_VIRT_DIRS', (parent_id, dir_id))
            self.dirTree.model().remove_row(cur_idx)
            print('***     exist')
        else:
            self.dbu.delete_other('VIRT_FROM_DIRS', (dir_id,))
            self.dbu.delete_other('VIRT_DIR_ID', (dir_id,))
            self.dirTree.model().remove_all_copies(cur_idx)
            print('*** not exist')

    def _exist_in_virt_dirs(self, dir_id, parent_id):
        return self.dbu.select_other('EXIST_IN_VIRT_DIRS', (dir_id, parent_id)).fetchone()

    def rename_folder(self):
        cur_idx = self.dirTree.currentIndex()
        u_data = self.dirTree.model().data(cur_idx, role=Qt.UserRole)
        folder_name = u_data.path
        new_name, ok_ = QInputDialog.getText(self.dirTree,
                                             'Input new folder name', '',
                                             QLineEdit.Normal, folder_name)
        if ok_:
            self.dbu.update_other('DIR_NAME', (new_name, u_data.dir_id))
            self.dirTree.model().update_folder_name(cur_idx, new_name)

    # def _is_virtual_dir(self):
    #     cur_idx = self.dirTree.currentIndex()
    #     return self.dirTree.model().is_virtual(cur_idx)

    def populate_directory_tree(self, same_db):
        # TODO - do not correctly restore when reopen from toolbar button
        print('====> _populate_directory_tree')
        dirs = self._get_dirs(self.places.get_curr_place().id_)
        self._insert_virt_dirs(dirs)

        for dir_ in dirs:
            print(dir_)

        model = EditTreeModel()
        model.set_alt_font(Shared['AppFont'])

        model.set_model_data(dirs)

        model.setHeaderData(0, Qt.Horizontal, ("Directories",))
        self.dirTree.setModel(model)

        self.dirTree.selectionModel().currentRowChanged.connect(self._cur_dir_changed)
        cur_dir_idx = self._restore_path(same_db)

        return cur_dir_idx

    def _cur_dir_changed(self, curr_idx):
        """
        currentRowChanged in dirTree
        :param curr_idx:
        :return: None
        """
        # TODO move this method to listFiles
        if curr_idx.isValid():
            DirTree._save_path(curr_idx)
            dir_idx = self.dirTree.model().data(curr_idx, Qt.UserRole)
            print('--> _cur_dir_changed', self.dirTree.model().rowCount(curr_idx), dir_idx)
            # return self.dirTree.model().is_virtual(curr_idx), dir_idx
            # TODO need call filesList methods: _populate_virtual or _populate_file_list
            if self.dirTree.model().is_virtual(curr_idx):
                Shared['Controller']._populate_virtual(dir_idx.dir_id)
            else:
                Shared['Controller']._populate_file_list(dir_idx)

    @staticmethod
    def _save_path(index):
        path = DirTree.full_tree_path(index)

        settings = QSettings()
        settings.setValue('TREE_SEL_IDX', QVariant(path))

    @staticmethod
    def full_tree_path(index):
        idx = index
        path = []
        while idx.isValid():
            path.append(idx.row())
            idx = idx.parent()
        path.reverse()
        return path

    def _restore_path(self, same_db: bool):
        """
        restore expand state and current index of dirTree
        :return: current index
        """
        print('--> _restore_path: same_db=', same_db)
        model = self.dirTree.model()
        parent = QModelIndex()
        if same_db:
            settings = QSettings()
            aux = settings.value('TREE_SEL_IDX', [0])
            for id_ in aux:
                if parent.isValid():
                    if not self.dirTree.isExpanded(parent):
                        self.dirTree.setExpanded(parent, True)
                idx = model.index(int(id_), 0, parent)
                self.dirTree.setCurrentIndex(idx)
                parent = idx

        if parent.isValid():
            print('   parent.isValid')
            return parent

        idx = model.index(0, 0, QModelIndex())
        print('   idx.isValid', idx.isValid())

        self.dirTree.setCurrentIndex(idx)
        return idx

    def del_empty_dirs(self, same_db):
        self.dbu.delete_other('EMPTY_DIRS', ())
        self.populate_directory_tree(same_db)

    def rescan_dir(self):
        idx = self.dirTree.currentIndex()
        dir_ = self.dirTree.model().data(idx, Qt.UserRole).path
        ext_ = self._get_selected_ext()
        ext_item, ok_pressed = QInputDialog.getText(self.dirTree, "Input extensions",
                                                    'Input extensions (* - all)',
                                                    QLineEdit.Normal, ext_)
        return ok_pressed, dir_, ext_item.strip()

    def _insert_virt_dirs(self, dir_tree: list):
        virt_dirs = self.dbu.select_other('VIRT_DIRS', (self.places.get_curr_place().id_,))
        id_list = [x[1] for x in dir_tree]

        if self.places.get_disk_state() == Places.MOUNTED:
            # bind dirs with mount point
            root = self.places.get_mount_point()
            for vd in virt_dirs:
                if vd[-1] == 1:
                    vd = (*vd[:-1], 2)
                try:
                    idx = id_list.index(vd[2])
                    dir_tree.insert(idx, (os.path.split(vd[0])[1], *vd[1:],
                                          1, os.altsep.join((root, vd[0]))))
                    id_list.insert(idx, vd[1])
                except ValueError:
                    pass
        else:
            for vd in virt_dirs:
                if vd[-1] == 1:
                    vd = (*vd[:-1], 2)
                try:
                    idx = id_list.index(vd[2])
                    dir_tree.insert(idx, (os.path.split(vd[0])[1], *vd[1:], 1, vd[0]))
                    id_list.insert(idx, vd[1])
                except ValueError:
                    pass

    def _get_dirs(self, place_id):
        """
        Returns directory tree for current place
        :param place_id:
        :return: list of tuples (Dir name, DirID, ParentID, isVirtual, Full path of dir)
        """
        dirs = []
        dir_tree = self.dbu.dir_tree_select(dir_id=0, level=0, place_id=place_id)

        if self.places.get_disk_state() == Places.MOUNTED:
            # bind dirs with mount point
            root = self.places.get_mount_point()
            for rr in dir_tree:
                dirs.append((os.path.split(rr[0])[1], *rr[1:len(rr)-1],
                             0, os.altsep.join((root, rr[0]))))
        else:
            for rr in dir_tree:
                print('** ', rr)
                dirs.append((os.path.split(rr[0])[1], *rr[1:len(rr)-1], 0, rr[0]))
        return dirs
