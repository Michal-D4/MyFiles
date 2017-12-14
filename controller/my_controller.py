# controller/my_controller.py

import sqlite3
import os
import webbrowser
from collections import namedtuple

from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QMessageBox, QFontDialog
from PyQt5.QtCore import Qt, QModelIndex, QItemSelectionModel

from controller.my_qt_model import TreeModel, TableModel
from controller.places import Places
from model.db_utils import DBUtils, PLUS_EXT_ID
from model.utils import create_db
from model.file_info import FileInfo, LoadFiles
from model.helpers import *
from view.item_edit import ItemEdit
from view.sel_opt import SelOpt

DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES


class MyController():

    FOLDER, FAVORITE, ADVANCE = (1, 2, 4)

    def __init__(self, view):
        self._connection = None
        self.view = view.ui_main
        self.file_list_source = MyController.FOLDER
        self._dbu = DBUtils()
        self._cb_places = Places(self)
        self._opt = SelOpt(self)
        self._on_data_methods = self.set_on_data_methods()

    def set_on_data_methods(self):
        return {'cb_places': self._cb_places.about_change_place,
                'dirTree': self._populate_directory_tree,
                'Edit key words': self._edit_key_words,
                'Edit authors': self._edit_authors,
                'Edit title': self._edit_title,
                'Edit date': self._edit_date,
                'Edit comment': self._edit_comment,
                'Delete': self._delete_file,
                'Add to favorites': self._add_file_to_favorites,
                'File_doubleClicked': self._double_click_file,
                'Open': self._open_file,
                'Open folder': self._open_folder,
                'advanced_file_list': self._advanced_file_list,
                'get_sel_files': self.get_sel_files,
                'Favorites': self._favorite_file_list,
                'Author Remove unused': self._author_remove_unused,
                'Tag Remove unused': self._tag_remove_unused,
                'Ext Remove unused': self._ext_remove_unused,
                'Ext Create group': self._ext_create_group,
                'Dirs Update tree': self._dir_update,
                'change_font': self._change_font,
                'Tag Scan in names': self._scan_for_tags
                }

    def get_places_view(self):
        return self.view.cb_places

    def get_db_utils(self):
        return self._dbu

    def get_place_instance(self):
        return self._cb_places

    @staticmethod
    def _yield_files(root, extensions):
        """
        generator of file list
        :param root: root directory
        :param extensions: list of extensions
        :return: generator
        """
        for dir_name, _, file_names in os.walk(root):
            if extensions:
                ext_ = tuple(x.strip('. ') for x in extensions.split(','))
                for filename in file_names:
                    if get_file_extension(filename) in ext_:
                        yield os.path.join(dir_name, filename)
            else:
                for filename in file_names:
                    yield os.path.join(dir_name, filename)

    def on_open_db(self, file_name, create):
        if create:
            self._connection = sqlite3.connect(file_name, check_same_thread=False,
                                               detect_types=DETECT_TYPES)
            create_db.create_all_objects(self._connection)
        else:
            if os.path.isfile(file_name):
                self._connection = sqlite3.connect(file_name, check_same_thread=False,
                                                   detect_types=DETECT_TYPES)
            else:
                MyController.show_message("Data base does not exist")
                return

        self._dbu.set_connection(self._connection)
        self._populate_all_widgets()

    def on_change_data(self, action):
        '''
        run methods for change_data_signal
        :param action:
        :return:
        '''
        self._on_data_methods[action]()

    def _scan_for_tags(self):
        # todo scan tags in file names, titles and comments
        ext_idx = MyController._selected_db_indexes(self.view.extList)
        all_id = self._collect_all_ext(ext_idx)

        files = self._dbu.select_other2('FILE_NAME+TITLE',
                                        ','.join([str(i) for i in all_id])).fetchall()
        print('|--> _scan_for_tags', files)
        sel_tag = self.get_selected_items(self.view.tagsList)
        print('|--> _scan_for_tags', ','.join([str(i) for i in all_id]), sel_tag)

    def _change_font(self):
        font, ok_ = QFontDialog.getFont(self.view.dirTree.font(), self.view.dirTree)
        if ok_:
            self.view.dirTree.setFont(font)
            self.view.extList.setFont(font)
            self.view.filesList.setFont(font)
            self.view.tagsList.setFont(font)
            self.view.authorsList.setFont(font)
            self.view.commentField.setFont(font)

    def _author_remove_unused(self):
        self._dbu.delete_other('UNUSED_AUTHORS', ())
        self._populate_author_list()

    def _tag_remove_unused(self):
        self._dbu.delete_other('UNUSED_TAGS', ())
        self._populate_tag_list()

    def _ext_remove_unused(self):
        self._dbu.delete_other('UNUSED_EXT', ())
        self._dbu.delete_other('UNUSED_EXT_GROUP', ())
        self._populate_ext_list()

    def _ext_create_group(self):
        ids = self._selected_db_indexes(self.view.extList)
        print('|--> ext_create_group', ids)
        if ids:
            group_name, ok_pressed = QInputDialog.getText(self.view.extList,
                                                          'Input group name',
                                                          '', QLineEdit.Normal,
                                                          '')
            if ok_pressed:
                gr_id = self._dbu.insert_other('EXT_GROUP', (group_name,))
                all_id = self._collect_all_ext(ids)

                for id_ in all_id:
                    self._dbu.update_other('EXT_GROUP', (gr_id, id_))

                self._dbu.delete_other('UNUSED_EXT_GROUP', ())

                self._populate_ext_list()

    @staticmethod
    def _selected_db_indexes(view):
        sel_model_idx = view.selectedIndexes()
        model = view.model()
        ids = []
        for idx in sel_model_idx:
            ids.append(model.data(idx, Qt.UserRole)[0])
        return ids

    def _collect_all_ext(self, ids):
        all_id = set()
        for id_ in ids:
            if id_ < PLUS_EXT_ID:
                curr = self._dbu.select_other('EXT_ID_IN_GROUP', (id_,))
                for idd in curr:
                    all_id.add(idd[0])
            else:
                all_id.add(id_ - PLUS_EXT_ID)
        return all_id

    def _dir_update(self):
        self._populate_directory_tree()
        self._populate_ext_list()

    def _favorite_file_list(self):
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, 'File Date Pages Size')
        files = self._dbu.select_other('FAVORITES').fetchall()
        if files:
            self.file_list_source = MyController.FAVORITE
            self._show_files(files, model)
            self.view.statusbar.showMessage('Favorite files')
        else:
            self.view.filesList.setModel(model)
            self.view.statusbar.showMessage('No data')

    def _advanced_file_list(self):
        """
        Show files according optional conditions
        1) folder and nested sub-folders up to n-th level
        2) list of file extensions
        3) list of key words (match all/mutch any)
        4) list of authors
        5) date of file/book creation - after/before
        :return:
        """
        if self._opt.exec_():
            self.get_sel_files()

    def get_sel_files(self):
        res = self._opt.get_result()
        print('|--> get_sel_files', res)
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, 'File Date Pages Size')

        curs = self._dbu.advanced_selection(res, self._cb_places.get_curr_place()[1][0]).fetchall()
        if curs:
            self._show_files(curs, model)
            self.file_list_source = MyController.ADVANCE
        else:
            MyController.show_message("Nothing found. Change you choices.")

    def _add_file_to_favorites(self):
        f_idx = self.view.filesList.currentIndex()
        file_id, _, _, _ = self.view.filesList.model().data(f_idx, Qt.UserRole)
        self._dbu.insert_other('FAVORITES', (file_id,))

    def _delete_file(self):
        f_idx = self.view.filesList.currentIndex()
        u_data = self.view.filesList.model().data(f_idx, Qt.UserRole)
        if self.file_list_source == MyController.FAVORITE:
            self._dbu.delete_other('FAVORITES', (u_data[0],))
            self._favorite_file_list()
            return

        self._dbu.delete_other('AUTHOR_FILE_BY_FILE', (u_data[0],))
        self._dbu.delete_other('TAG_FILE_BY_FILE', (u_data[0],))
        self._dbu.delete_other('COMMENT', (u_data[2],))
        self._dbu.delete_other('FILE', (u_data[0],))
        if self.file_list_source == MyController.FOLDER:
            idx = self.view.dirTree.currentIndex()
            dir_idx = self.view.dirTree.model().data(idx, Qt.UserRole)
            self._populate_file_list(dir_idx)
        else:
            self.get_sel_files()

    def _open_folder(self):
        if self._cb_places.get_disk_state() & (Places.MOUNTED | Places.NOT_REMOVAL):
            idx = self.view.dirTree.currentIndex()
            dir_ = self.view.dirTree.model().data(idx, Qt.UserRole)
            webbrowser.open(''.join(('file://', dir_[2])))

    def _double_click_file(self):
        f_idx = self.view.filesList.currentIndex()
        file_name = self.view.filesList.model().data(f_idx)
        file_id, dir_id, _, _ = self.view.filesList.model().data(f_idx, role=Qt.UserRole)
        if f_idx.column() == 0:
            self._open_file2(dir_id, file_name)
        elif f_idx.column() == 2:
            self._update_pages(f_idx, file_id, file_name)

    def _update_pages(self, f_idx, file_id, page_number):
        if not page_number:
            page_number = 0
        pages, ok_pressed = QInputDialog.getInt(self.view.extList, 'Input page number',
                                                '', QLineEdit.Normal, page_number)
        if ok_pressed:
            self._dbu.update_other('PAGES', (pages, file_id))
            self._refresh_file_list(f_idx)

    def _open_file(self):
        f_idx = self.view.filesList.currentIndex()
        file_name = self.view.filesList.model().data(f_idx)
        _, dir_id, _, _ = self.view.filesList.model().data(f_idx, role=Qt.UserRole)
        self._open_file2(dir_id, file_name)

    def _open_file2(self, dir_id, file_name):
        if self._cb_places.get_disk_state() & (Places.MOUNTED | Places.NOT_REMOVAL):
            path = self._dbu.select_other('PATH', (dir_id,)).fetchone()
            full_file_name = os.path.join(path[0], file_name)
            if os.path.isfile(full_file_name):
                try:
                    os.startfile(full_file_name)
                except OSError:
                    pass
            else:
                MyController.show_message("Can't find file {}".format(full_file_name))

    def _edit_key_words(self):
        curr_idx = self.view.filesList.currentIndex()
        u_data = self.view.filesList.model().data(curr_idx, Qt.UserRole)

        titles = ('Enter new tags separated by commas',
                  'Select tags from list', 'Apply key words / tags')
        tag_list = self._dbu.select_other('TAGS').fetchall()
        sel_tags = self._dbu.select_other('FILE_TAGS', (u_data[0],)).fetchall()

        edit_tags = ItemEdit(titles,
                             [tag[0] for tag in tag_list],
                             [tag[0] for tag in sel_tags])

        if edit_tags.exec_():
            res = edit_tags.get_result()
            sql_list = (('TAG_FILE', 'TAG_FILES', 'TAG'),
                        ('TAGS_BY_NAME', 'TAGS', 'TAG_FILE'))
            self.save_edited_items(new_items=res, old_items=sel_tags,
                                   file_id=u_data[0], sql_list=sql_list)

            self._populate_tag_list()
            self._populate_comment_field(u_data)

    def save_edited_items(self, new_items, old_items, file_id, sql_list):
        old_words_set = set([tag[0] for tag in old_items])
        new_words_set = set([str.lstrip(item) for item in new_items.split(', ')])

        to_del = old_words_set.difference(new_words_set)
        to_del_ids = [tag[1] for tag in old_items if tag[0] in to_del]
        self.del_item_links(to_del_ids, file_id, sql_list[0])

        old_words_set.add('')
        to_add = new_words_set.difference(old_words_set)
        self.add_item_links(to_add, file_id, sql_list[1])

    def del_item_links(self, items2del, file_id, sqls):
        for item in items2del:
            self._dbu.delete_other(sqls[0], (item, file_id))
            res = self._dbu.select_other(sqls[1], (item,)).fetchone()
            if not res:
                self._dbu.delete_other(sqls[2], (item,))

    def add_item_links(self, items2add, file_id, sqls):
        add_ids = self._dbu.select_other2(sqls[0], ('","'.join(items2add),)).fetchall()
        sel_items = [item[0] for item in add_ids]
        not_in_ids = [item for item in items2add if not item in sel_items]

        for item in not_in_ids:
            item_id = self._dbu.insert_other(sqls[1], (item,))
            self._dbu.insert_other(sqls[2], (item_id, file_id))

        for item in add_ids:
            self._dbu.insert_other(sqls[2], (item[1], file_id))

    def _edit_authors(self):
        """
        model().data(curr_idx, Qt.UserRole) = (FileID, DirID, CommentID, IssueDate)
        """
        curr_idx = self.view.filesList.currentIndex()
        u_data = self.view.filesList.model().data(curr_idx, Qt.UserRole) # file_id, _, comment_id, _

        titles = ('Enter authors separated by commas',
                  'Select authors from list', 'Apply authors')
        authors = self._dbu.select_other('AUTHORS').fetchall()
        sel_authors = self._dbu.select_other('FILE_AUTHORS', (u_data[0],)).fetchall()

        edit_authors = ItemEdit(titles,
                                [tag[0] for tag in authors],
                                [tag[0] for tag in sel_authors])

        if edit_authors.exec_():
            res = edit_authors.get_result()
            sql_list = (('AUTHOR_FILE', 'AUTHOR_FILES', 'AUTHOR'),
                        ('AUTHORS_BY_NAME', 'AUTHORS', 'AUTHOR_FILE'))
            self.save_edited_items(new_items=res, old_items=sel_authors,
                                   file_id=u_data[0], sql_list=sql_list)

            self._populate_author_list()
            self._populate_comment_field(u_data)

    def _edit_comment_item(self, to_update, item_no):
        checked = self.check_existence()
        print('==-> ', to_update, checked, item_no, getattr(checked, item_no))
        data_, ok_pressed = QInputDialog.getText(self.view.extList, to_update[1],
                                                 '', QLineEdit.Normal, getattr(checked, item_no))
        print('---> ', data_)
        if ok_pressed:
            self._dbu.update_other(to_update[0], (data_, checked.comment_id))
            self._populate_comment_field(checked[:4]) # file_id, dir_id, comment_id, issue_date

    def check_existence(self):
        """
        Check if comment record already created for file
        :return: (file_id, dir_id, comment_id, issue_date, comment, book_title)
        """
        u_type = namedtuple('file_comment',
                            'file_id dir_id comment_id issue_date comment book_title')
        curr_idx = self.view.filesList.currentIndex()
        #  user_data = (file_id, dir_id, comment_id, issue_date)
        user_data = self.view.filesList.model().data(curr_idx, Qt.UserRole)
        comment = self._dbu.select_other("FILE_COMMENT", (user_data[2],)).fetchone()
        if not comment:
            comment = ('', '')
            comment_id = self._dbu.insert_other('COMMENT', comment)
            self._dbu.update_other('FILE_COMMENT', (comment_id, user_data[0]))
            self._refresh_file_list(curr_idx)   # need, to have comment_id in model
        return u_type._make(user_data + comment)

    def _refresh_file_list(self, curr_idx):
        if self.file_list_source == MyController.FAVORITE:
            self._favorite_file_list()
        elif self.file_list_source == MyController.FOLDER:
            idx = self.view.dirTree.currentIndex()
            dir_idx = self.view.dirTree.model().data(idx, Qt.UserRole)
            self._populate_file_list(dir_idx)
        else:
            self.get_sel_files()

        self.view.filesList.setCurrentIndex(curr_idx)
        f_idx = self.view.filesList.model().index(curr_idx.row(), 0)
        self.view.filesList.selectionModel().select(f_idx, QItemSelectionModel.Select)

    def _edit_date(self):
        self._edit_comment_item(('ISSUE_DATE', 'Input issue date'), 'issue_date')

    def _edit_title(self):
        self._edit_comment_item(('BOOK_TITLE', 'Input book title'), 'book_title')

    def _edit_comment(self):
        self._edit_comment_item(('COMMENT', 'Input comment'), 'comment')

    def _populate_ext_list(self):
        ext_list = self._dbu.select_other('EXT')
        model = TreeModel(ext_list)
        model.setHeaderData(0, Qt.Horizontal, "Extensions")
        self.view.extList.setModel(model)

    def _populate_tag_list(self):
        tag_list = self._dbu.select_other('TAGS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, ("Tags",))
        for tag, id_ in tag_list:
            model.append_row(tag, id_)
        self.view.tagsList.setModel(model)

    def _populate_author_list(self):
        author_list = self._dbu.select_other('AUTHORS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, "Authors")
        for author, id_ in author_list:
            model.append_row(author, id_)
        self.view.authorsList.setModel(model)

    def _populate_file_list(self, dir_idx):
        """
        :param dir_idx:
        :return:
        """
        self.file_list_source = MyController.FOLDER
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, 'File Date Pages Size')
        if dir_idx:
            files = self._dbu.select_other('FILES_CURR_DIR', (dir_idx[0],))
            self._show_files(files, model)

            self.view.statusbar.showMessage('{} ({})'.format(dir_idx[2],
                                                             model.rowCount(QModelIndex())))
        else:
            self.view.filesList.setModel(model)
            self.view.statusbar.showMessage('No data')

    def _show_files(self, files, model):
        for ff in files:
            # ff[:4] = [FileName, FileDate, Pages, Size]
            # ff[4:] = [FileID, DirID, CommentID, IssueDate]
            model.append_row(ff[:4], ff[4:])

        self.view.filesList.setModel(model)
        self.view.filesList.selectionModel().currentRowChanged.connect(self._file_changed)
        index_ = model.index(0, 0)
        self.view.filesList.setCurrentIndex(index_)
        self.view.filesList.activateWindow()

    def _file_changed(self, curr_idx, _):
        data = self.view.filesList.model().data(curr_idx, role=Qt.UserRole)
        self._populate_comment_field(data)

    def _populate_comment_field(self, data):
        file_id = data[0]
        comment_id = data[2]
        if file_id:
            assert isinstance(file_id, int), \
                "the type of file_id is {} instead of int".format(type(file_id))
            tags = self._dbu.select_other("FILE_TAGS", (file_id,)).fetchall()

            authors = self._dbu.select_other("FILE_AUTHORS", (file_id,)).fetchall()

            if comment_id:
                comment = self._dbu.select_other("FILE_COMMENT", (comment_id,)).fetchone()
            else:
                comment = ('', '')
            self.view.commentField.setText(''.join((
                '<html><body><p><a href="Edit key words">Key words</a>: {}</p>'.
                    format(', '.join([tag[0] for tag in tags])),
                '<p><a href="Edit authors">Authors</a>: {}</p>'.
                    format(', '.join([author[0] for author in authors])),
                '<p><a href="Edit date">Issue date</a>: {}</p>'.format(data[3]),
                '<p><a href="Edit title"4>Title</a>: {}</p>'.format(comment[1]),
                '<p><a href="Edit comment">Comment</a> {}</p></body></html>'.
                    format(comment[0]))))

            if not self.file_list_source == MyController.FOLDER:
                f_idx = self.view.filesList.currentIndex()
                file_id, dir_id, _, _ = self.view.filesList.model().data(f_idx, role=Qt.UserRole)
                path = self._dbu.select_other('PATH', (dir_id,)).fetchone()
                self.view.statusbar.showMessage(path[0])

    def _populate_all_widgets(self):
        self._cb_places.populate_cb_places()
        self._populate_directory_tree()
        self._populate_ext_list()
        self._populate_tag_list()
        self._populate_author_list()

    def _populate_directory_tree(self):
        dirs = self._get_dirs(self._cb_places.get_curr_place()[1][0])

        model = TreeModel(dirs)
        model.setHeaderData(0, Qt.Horizontal, ("Directories",))

        self.view.dirTree.setModel(model)
        idx = model.index(0, 0)
        self.view.dirTree.setCurrentIndex(idx)

        self._populate_file_list(model.data(idx, role=Qt.UserRole))

        self.view.dirTree.selectionModel().selectionChanged.connect(self.sel_changed)

    def _get_dirs(self, place_id):
        """
        Returns directory tree for current place
        :param place_id:
        :return: list of tuples (Dir name, DirID, ParentID, Full path of dir)
        """
        dirs = []
        dir_tree = self._dbu.dir_tree_select(dir_id=0, level=0, place_id=place_id)
        if self._cb_places.get_disk_state() == Places.NOT_REMOVAL:
            for rr in dir_tree:
                dirs.append((os.path.split(rr[1])[1], rr[0], rr[2], rr[1]))
        else:
            root = self._cb_places.get_mount_point()
            for rr in dir_tree:
                dirs.append((os.path.split(rr[1])[1], rr[0], rr[2], os.altsep.join((root, rr[1]))))
        return dirs

    def sel_changed(self, sel1, _):
        """
        Changed selection in dirTree
        :param sel1: QList<QModelIndex>
        :param sel2: QList<QModelIndex>
        :return: None
        """
        idx = sel1.indexes()
        if idx:
            # dir_idx = (DirID, ParentID, Full path)
            dir_idx = self.view.dirTree.model().data(idx[0], Qt.UserRole)
            self._populate_file_list(dir_idx)

    def on_scan_files(self):
        """
        The purpose is to fill the data base with files by means of
        1) scanning the file system for  mounted disk
        or
        2) reading from prepared file for  unmounted disk
        :return: None
        """
        if self._cb_places.get_disk_state() == Places.NOT_MOUNTED:
            _data = self._read_from_file()
        else:
            _data = self._scan_file_system()

        if _data:
            curr_place = self._cb_places.get_curr_place()
            load_files = LoadFiles(self._connection, curr_place, _data)
            load_files.start()

            thread = FileInfo(self._connection, self._cb_places)
            thread.start()

    def _scan_file_system(self):
        ext_ = self._get_selected_ext()
        ext_item, ok_pressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                    '', QLineEdit.Normal, ext_)
        if ok_pressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            if root:
                self._cb_places.update_place_name(root)
                return MyController._yield_files(root, ext_item)

        return ()       # not ok_pressed or root is empty

    def _read_from_file(self):
        file_name = QFileDialog().getOpenFileName(self.view.extList, 'Choose input file',
                                                  os.getcwd())
        with open(file_name, 'rb') as a_file:
            line = next(a_file)
            if not self._cb_places.get_curr_place()[1][1] in line:
                # do : in case of 'other place' check if place defined in the first line of file
                # 1) if not defined - possible action:
                #    a)  show message and stop action
                #    b)  ???
                # 2) if defined - possible action:
                #    a)  - switch to place in file
                #    b)  - create new place
                MyController.show_message("The file {} doesn't have data from current place!".
                                          format(file_name))
                a_file = ()
            return a_file
        return ()

    @staticmethod
    def show_message(message, message_type=QMessageBox.Critical):
        box = QMessageBox()
        box.setIcon(message_type)
        box.setText(message)
        box.addButton('Ok', QMessageBox.AcceptRole)
        box.exec_()

    @staticmethod
    def get_selected_items(view):
        idxs = view.selectedIndexes()
        if idxs:
            model = view.model()
            items_str = ', '.join(model.data(i, Qt.DisplayRole) for i in idxs)
        else:
            items_str = ''
        return items_str

    def _get_selected_ext(self):
        idxs = self.view.extList.selectedIndexes()
        res = set()
        if idxs:
            model = self.view.extList.model()
            for i in idxs:
                tt = model.data(i, Qt.UserRole)
                if tt[0] > PLUS_EXT_ID:
                    res.add(model.data(i, Qt.DisplayRole))
                else:
                    ext_ = self._dbu.select_other('EXT_IN_GROUP', (tt[0],)).fetchall()
                    res.update([ee[0] for ee in ext_])
            res = list(res)
            res.sort()
            return ', '.join(res)
        return ''
