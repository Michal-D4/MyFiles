

class DirTree():

    def _add_group_folder(self):
        """
        group of real folders - organise for better vision
        """
        folder_name = '<Group name>'
        new_name, ok_ = QInputDialog.getText(self.ui.dirTree,
                                             'Input folder name', '',
                                             QLineEdit.Normal, folder_name)
        print('--> _add_group_folder', new_name, ok_)
        if ok_:
            curr_idx = self.ui.dirTree.currentIndex()
            idx_list = self._curr_selected_dirs(curr_idx)
            
            d_dat = self.ui.dirTree.model().data(curr_idx, Qt.UserRole)
            new_parent = (new_name, d_dat.parent_id, self._cb_places.get_curr_place().id_, 3)
            new_parent_id = self._dbu.insert_other('DIR', new_parent)
            self.ui.dirTree.model().create_new_parent(curr_idx, (new_parent_id, *new_parent), idx_list)
    
    def _curr_selected_dirs(self, curr_idx):
        if not self.ui.dirTree.selectionModel().isSelected(curr_idx):
            self.ui.dirTree.selectionModel().select(curr_idx, QItemSelectionModel.SelectCurrent)
        selected_indexes = self.ui.dirTree.selectionModel().selectedRows()
        
        idx_list = []
        for idx in selected_indexes:
            idx_list.append(QPersistentModelIndex(idx))
        
        return idx_list

    def _create_virtual_child(self):
        folder_name = 'New folder'
        new_name, ok_ = QInputDialog.getText(self.ui.dirTree,
                                             'Input folder name', '',
                                             QLineEdit.Normal, folder_name)
        if ok_:
            cur_idx = self.ui.dirTree.currentIndex()
            self._create_virtual_folder(new_name, cur_idx)

    def _create_virtual(self):
        folder_name = 'New folder'
        new_name, ok_ = QInputDialog.getText(self.ui.dirTree,
                                             'Input folder name', '',
                                             QLineEdit.Normal, folder_name)
        if ok_:
            cur_idx = self.ui.dirTree.currentIndex()
            parent = self.ui.dirTree.model().parent(cur_idx)
            self._create_virtual_folder(new_name, parent)

    def _create_virtual_folder(self, folder_name, parent):
        if parent.isValid():
            parent_id = self.ui.dirTree.model().data(parent, role=Qt.UserRole).dir_id
        else:
            parent_id = 0
        place_id = self._cb_places.get_curr_place().id_
        dir_id = self._dbu.insert_other('DIR', (folder_name, parent_id, place_id, 2))

        item = EditTreeItem((folder_name, ), (dir_id, parent_id, 2, folder_name))

        self.ui.dirTree.model().append_child(item, parent)

    def _delete_virtual(self):
        cur_idx = self.ui.dirTree.currentIndex()
        parent = self.ui.dirTree.model().parent(cur_idx)
        parent_id = 0 if not parent.isValid() else \
                    self.ui.dirTree.model().data(parent, role=Qt.UserRole).dir_id
        dir_id = self.ui.dirTree.model().data(cur_idx, role=Qt.UserRole).dir_id
        print('--> _delete_virtual: parent_id {}, dir_id {}'.format(parent_id, dir_id))

        if self._exist_in_virt_dirs(dir_id, parent_id):
            self._dbu.delete_other('FROM_VIRT_DIRS', (parent_id, dir_id))
            self.ui.dirTree.model().remove_row(cur_idx)
            print('***     exist')
        else:
            self._dbu.delete_other('VIRT_FROM_DIRS', (dir_id,))
            self._dbu.delete_other('VIRT_DIR_ID', (dir_id,))
            self.ui.dirTree.model().remove_all_copies(cur_idx)         
            print('*** not exist')

    def _exist_in_virt_dirs(self, dir_id, parent_id):
        return self._dbu.select_other('EXIST_IN_VIRT_DIRS', (dir_id, parent_id)).fetchone()

    def _is_parent_virtual(self, index):
        parent = self.ui.dirTree.model().parent(index)
        return self.ui.dirTree.model().is_virtual(parent)

    def _rename_folder(self):
        cur_idx = self.ui.dirTree.currentIndex()
        u_data = self.ui.dirTree.model().data(cur_idx, role=Qt.UserRole)
        folder_name = u_data.path
        new_name, ok_ = QInputDialog.getText(self.ui.dirTree,
                                             'Input new folder name', '',
                                             QLineEdit.Normal, folder_name)
        if ok_:
            self._dbu.update_other('DIR_NAME', (new_name, u_data.dir_id))
            self.ui.dirTree.model().update_folder_name(cur_idx, new_name)

    def _is_virtual_dir(self):
        cur_idx = self.ui.dirTree.currentIndex()
        return self.ui.dirTree.model().is_virtual(cur_idx)

    def _populate_directory_tree(self):
        # TODO - do not correctly restore when reopen from toolbar button
        print('====> _populate_directory_tree')
        dirs = self._get_dirs(self._cb_places.get_curr_place().id_)
        self._insert_virt_dirs(dirs)

        for dir_ in dirs:
            print(dir_)

        model = EditTreeModel()
        model.set_alt_font(Shared['AppFont'])

        model.set_model_data(dirs)

        model.setHeaderData(0, Qt.Horizontal, ("Directories",))
        self.ui.dirTree.setModel(model)

        self.ui.dirTree.selectionModel().currentRowChanged.connect(self._cur_dir_changed)
        cur_dir_idx = self._restore_path()

        # TODO remove _restore_file_list and below from this method
        self._restore_file_list(cur_dir_idx)

        if dirs:
            if self._cb_places.get_disk_state() & (Places.NOT_DEFINED | Places.NOT_MOUNTED):
                show_message('Files are in an inaccessible place')
            self._resize_columns()

    def _cur_dir_changed(self, curr_idx):
        """
        currentRowChanged in dirTree
        :param curr_idx:
        :return: None
        """
        if curr_idx.isValid():
            MyController._save_path(curr_idx)
            dir_idx = self.ui.dirTree.model().data(curr_idx, Qt.UserRole)
            print('--> _cur_dir_changed', self.ui.dirTree.model().rowCount(curr_idx), dir_idx)
            if self.ui.dirTree.model().is_virtual(curr_idx):
                self._populate_virtual(dir_idx.dir_id)
            else:
                self._populate_file_list(dir_idx)

    @staticmethod
    def _save_path(index):
        path = MyController.full_tree_path(index)

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

    def _restore_path(self):
        """
        restore expand state and current index of dirTree
        :return: current index
        """
        print('--> _restore_path: same_db=', self.same_db)
        model = self.ui.dirTree.model()
        parent = QModelIndex()
        if self.same_db:
            settings = QSettings()
            aux = settings.value('TREE_SEL_IDX', [0])
            for id_ in aux:
                if parent.isValid():
                    if not self.ui.dirTree.isExpanded(parent):
                        self.ui.dirTree.setExpanded(parent, True)
                idx = model.index(int(id_), 0, parent)
                self.ui.dirTree.setCurrentIndex(idx)
                parent = idx

        if parent.isValid():
            print('   parent.isValid')
            return parent

        idx = model.index(0, 0, QModelIndex())
        print('   idx.isValid', idx.isValid())

        self.ui.dirTree.setCurrentIndex(idx)
        return idx

    def _del_empty_dirs(self):
        self._dbu.delete_other('EMPTY_DIRS', ())
        self._populate_directory_tree()

    def _rescan_dir(self):
        idx = self.ui.dirTree.currentIndex()
        dir_ = self.ui.dirTree.model().data(idx, Qt.UserRole)
        ext_ = self._get_selected_ext()
        ext_item, ok_pressed = QInputDialog.getText(self.ui.extList, "Input extensions",
                                                    'Input extensions (* - all)',
                                                    QLineEdit.Normal, ext_)
        if ok_pressed:
            self._load_files(dir_.path, ext_item.strip())

