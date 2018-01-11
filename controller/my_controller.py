# controller/my_controller.py

import sqlite3
import os
import re
import webbrowser

from PyQt5.QtWidgets import (QInputDialog, QLineEdit, QFileDialog,
                             QFontDialog, QApplication)
from PyQt5.QtCore import (Qt, QModelIndex, QItemSelectionModel, QSettings, QDate,
                          QDateTime, QVariant, QItemSelection, QThread)

from controller.table_model import TableModel, ProxyModel2
from controller.tree_model import TreeModel
from controller.places import Places
from model.utilities import DBUtils, PLUS_EXT_ID
from model.utils import create_db
from model.file_info import FileInfo, LoadFiles
from model.helpers import *
from view.item_edit import ItemEdit
from view.sel_opt import SelOpt
from view.set_fields import SetFields
from view.input_date import DateInputDialog
from model.helpers import Fields

DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES


class MyController():
    FOLDER, FAVORITE, ADVANCE = (1, 2, 4)

    def __init__(self, view):
        self._connection = None
        self.view = view.ui

        self.fields = Fields._make(((),(),()))
        self.same_db = False
        self.thread = None
        self.obj_thread = None
        self.file_list_source = MyController.FOLDER
        self._dbu = DBUtils()
        self._cb_places = Places(self)
        self._opt = SelOpt(self)
        self._restore_font()
        self._restore_fields()

    def _on_data_methods(self):
        return {'Add to favorites': self._add_file_to_favorites,
                'Author Remove unused': self._author_remove_unused,
                'Change place': self._cb_places.about_change_place,
                'change_font': self._ask_for_change_font,
                'Copy file name': self._copy_file_name,
                'Copy full path': self._copy_full_path,
                'Delete': self._delete_file,
                'Dirs Rescan dir': self._rescan_dir,
                'Dirs Remove empty': self._del_empty_dirs,
                'dirTree': self._populate_directory_tree,  # emit from Places
                'Edit authors': self._edit_authors,
                'Edit comment': self._edit_comment,
                'Edit key words': self._edit_key_words,
                'Edit title': self._edit_title,
                'Ext Create group': self._ext_create_group,
                'Ext Remove unused': self._ext_remove_unused,
                'Favorites': self._favorite_file_list,
                'File_doubleClicked': self._double_click_file,
                'get_sel_files': self._list_of_selected_files,
                'Open folder': self._open_folder,
                'Open': self._open_file,
                'Resize columns': self._resize_columns,
                'Selection options': self._selection_options,
                'Set fields': self._set_fields,
                'Tag Remove unused': self._tag_remove_unused,
                'Tag Rename': self._tag_rename,
                'Tag Scan in names': self._scan_for_tags
                }

    def _restore_fields(self):
        settings = QSettings()
        self.fields = Fields._make(settings.value('FIELDS',
                                                  (['FileName', 'FileDate', 'Pages', 'Size'],
                                                   ['File', 'Date', 'Pages', 'Size'],
                                                   [0, 1, 2, 3])))
        self._set_file_model()
        self._resize_columns()

    def _set_fields(self):
        set_fields_dialog = SetFields(self.fields)
        if set_fields_dialog.exec_():
            self.fields = set_fields_dialog.get_result()
            settings = QSettings()
            settings.setValue('FIELDS', self.fields)
            self._restore_file_list(self.view.dirTree.currentIndex())
            self._resize_columns()

    def _tag_rename(self):
        idx = self.view.tagsList.currentIndex()
        if idx.isValid():
            tag = self.view.tagsList.model().data(idx, role=Qt.DisplayRole)
            id = self.view.tagsList.model().data(idx, role=Qt.UserRole)
            tag, ok = QInputDialog.getText(self.view.extList,
                                           'Input new name',
                                           '', QLineEdit.Normal, tag)
            if ok:
                self._dbu.update_other('UPDATE_TAG', (tag, id))
                self.view.tagsList.model().update(idx, tag, Qt.DisplayRole)

    def _copy_file_name(self):
        idx = self.view.filesList.currentIndex()
        if idx.column() == 0:
            txt = self.view.filesList.model().data(idx, role=Qt.DisplayRole)
            QApplication.clipboard().setText(txt)

    def _copy_full_path(self):
        path, _, _, _ = self._file_path()
        QApplication.clipboard().setText(path)

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
        ext_ = tuple(x.strip('. ') for x in extensions.split(','))
        for dir_name, _, file_names in os.walk(root):
            if (not extensions) | (extensions == '*'):
                for filename in file_names:
                    yield os.path.join(dir_name, filename)
            else:
                for filename in file_names:
                    if get_file_extension(filename) in ext_:
                        yield os.path.join(dir_name, filename)

    def on_open_db(self, file_name, create, the_same):
        """
        Open or Create DB
        :param file_name: full file name of DB
        :param create: bool, Create DB if True, otherwise - Open
        :param the_same: bool if the same db is opened
        :return: None
        """
        self.same_db = the_same
        if create:
            self._connection = sqlite3.connect(file_name, check_same_thread=False,
                                               detect_types=DETECT_TYPES)
            create_db.create_all_objects(self._connection)
        else:
            if os.path.isfile(file_name):
                self._connection = sqlite3.connect(file_name, check_same_thread=False,
                                                   detect_types=DETECT_TYPES)
            else:
                self._show_message("Data base does not exist")
                return

        self._dbu.set_connection(self._connection)
        self._populate_all_widgets()

    def on_change_data(self, action):
        '''
        run methods for change_data_signal
        :param action:
        :return:
        '''
        try:
            self._on_data_methods()[action]()
        except KeyError:
            self._show_message('Action "{}" not implemented'.format(action), 5000)

    def _scan_for_tags(self):
        """
        Tags are searched if files with selected EXTENSIONS
        :return:
        """
        self._show_message('Scan in files with selected extensions')
        ext_idx = MyController._selected_db_indexes(self.view.extList)
        all_id = self._collect_all_ext(ext_idx)

        sel_tag = self.get_selected_tags()
        for tag in sel_tag:
            files = self._dbu.select_other2('FILE_INFO',
                                            (','.join([str(i) for i in all_id]),
                                             tag[1])).fetchall()
            for file in files:
                if re.search(tag[0], file[0], re.IGNORECASE):
                    try:
                        self._dbu.insert_other('TAG_FILE', (tag[1], file[1]))
                    except sqlite3.IntegrityError:
                        pass

    def get_selected_tags(self):
        idxs = self.view.tagsList.selectedIndexes()
        t_ids = []
        tag_s = []
        rb = r'\b'
        if idxs:
            model = self.view.tagsList.model()
            for i in idxs:
                t_ids.append(model.data(i, Qt.UserRole))
                tag_s.append(rb + model.data(i, Qt.DisplayRole) + rb)
            return list(zip(tag_s, t_ids))
        return []

    def _ask_for_change_font(self):
        font, ok_ = QFontDialog.getFont(self.view.dirTree.font(), self.view.dirTree)
        if ok_:
            self._change_font(font)
            settings = QSettings()
            settings.setValue('FONT', font)

    def _restore_font(self):
        settings = QSettings()
        font = settings.value('FONT', None)
        if font:
            self._change_font(font)

    def _change_font(self, font):
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
        updated_dirs = self.obj_thread.get_updated_dirs()
        self._populate_directory_tree()
        self._populate_ext_list()

        self.obj_thread = FileInfo(self._connection, self._cb_places, updated_dirs)
        self._run_in_qthread(self._finish_thread)

    def _run_in_qthread(self, finish):
        self.thread = QThread()
        self.obj_thread.moveToThread(self.thread)
        self.obj_thread.finished.connect(self.thread.quit)
        self.thread.finished.connect(finish)
        self.thread.started.connect(self.obj_thread.run)
        self.thread.start()

    def _finish_thread(self):
        self._show_message('Updating of files is finished')  #

    def _favorite_file_list(self):
        model = self._set_file_model()
        files = self._dbu.select_other('FAVORITES').fetchall()
        if files:
            self.file_list_source = MyController.FAVORITE
            settings = QSettings()
            settings.setValue('FILE_LIST_SOURCE', self.file_list_source)
            self._show_files(files, model)
            self.view.statusbar.showMessage('Favorite files')
        else:
            self.view.filesList.setModel(model)
            self.view.statusbar.showMessage('No data')

    def _selection_options(self):
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
            self._list_of_selected_files()

    def _list_of_selected_files(self):
        res = self._opt.get_result()
        model = self._set_file_model()

        curs = self._dbu.advanced_selection(res, self._cb_places.get_curr_place()[1][0]).fetchall()
        if curs:
            self._show_files(curs, model)
            self.file_list_source = MyController.ADVANCE
            settings = QSettings()
            settings.setValue('FILE_LIST_SOURCE', self.file_list_source)
        else:
            self._show_message("Nothing found. Change you choices.")

    def _add_file_to_favorites(self):
        f_idx = self.view.filesList.currentIndex()
        file_id, _, _, _, _ = self.view.filesList.model().data(f_idx, Qt.UserRole)
        self._dbu.insert_other('FAVORITES', (file_id,))

    def _delete_file(self):
        f_idx = self.view.filesList.currentIndex()
        u_data = self.view.filesList.model().data(f_idx, Qt.UserRole)
        if self.file_list_source == MyController.FAVORITE:
            self._dbu.delete_other('FAVORITES', (u_data[0],))
        else:
            self._dbu.delete_other('AUTHOR_FILE_BY_FILE', (u_data[0],))
            self._dbu.delete_other('TAG_FILE_BY_FILE', (u_data[0],))
            self._dbu.delete_other('COMMENT', (u_data[2],))
            self._dbu.delete_other('FILE', (u_data[0],))

        self.view.filesList.model().delete_row(f_idx)

    def _open_folder(self):
        path, _, state, _ = self._file_path()
        if state & (Places.MOUNTED | Places.NOT_REMOVAL):
            webbrowser.open(''.join(('file://', path)))

    def _double_click_file(self):
        f_idx = self.view.filesList.currentIndex()
        column_head = self.view.filesList.model().headerData(f_idx.column(), Qt.Horizontal)
        if column_head == 'File':
            self._open_file()
        elif column_head == 'Pages':
            pages = self.view.filesList.model().data(f_idx)
            file_id, _, _, _, _ = self.view.filesList.model().data(f_idx, role=Qt.UserRole)
            self._update_pages(f_idx, file_id, pages)
        elif column_head == 'Issued':
            issue_date = self.view.filesList.model().data(f_idx)
            file_id, _, _, _, _ = self.view.filesList.model().data(f_idx, role=Qt.UserRole)
            self._update_issue_date(f_idx, file_id, issue_date)

    def _update_issue_date(self, f_idx, file_id, issue_date):
        try:
            zz = [int(t) for t in issue_date.split('-')]
            issue_date = QDate(*zz)
        except (TypeError, ValueError):
            issue_date = QDate.currentDate()

        _date, ok_ = DateInputDialog.getDate(issue_date)
        if ok_:
            self._dbu.update_other('ISSUE_DATE', (_date, file_id))
            self.view.filesList.model().update(f_idx, _date)

    def _update_pages(self, f_idx, file_id, page_number):
        if not page_number:
            page_number = 0
        pages, ok_pressed = QInputDialog.getInt(self.view.extList, 'Input page number',
                                                '', int(page_number))
        if ok_pressed:
            self._dbu.update_other('PAGES', (pages, file_id))
            self.view.filesList.model().update(f_idx, pages)

    def _open_file(self):
        path, file_name, status, file_id = self._file_path()
        if status & (Places.MOUNTED | Places.NOT_REMOVAL):
            full_file_name = os.altsep.join((path, file_name))
            if os.path.isfile(full_file_name):
                try:
                    os.startfile(full_file_name)
                    cur_date = QDateTime.currentDateTime().toString(Qt.ISODate)[:16]
                    cur_date = cur_date.replace('T', ' ')
                    self._dbu.update_other('OPEN_DATE', (cur_date, file_id))
                    model = self.view.filesList.model()
                    heads = model.get_headers()
                    if 'Opened' in heads:
                        idx = model.mapToSource(self.view.filesList.currentIndex())
                        idx_s = model.sourceModel().createIndex(idx.row(), heads.index('Opened'))
                        model.sourceModel().update(idx_s, cur_date)
                except OSError:
                    self._show_message('Can\'t open file "{}"'.format(full_file_name))
            else:
                self._show_message("Can't find file {}".format(full_file_name))
        else:
            self._show_message('File/disk is inaccessible')

    def _file_path(self):
        f_idx = self.view.filesList.currentIndex()
        file_name = self.view.filesList.model().data(f_idx)
        file_id, dir_id, _, _, _ = self.view.filesList.model().data(f_idx, role=Qt.UserRole)
        path, place_id = self._dbu.select_other('PATH', (dir_id,)).fetchone()
        state = self._cb_places.get_state(place_id)
        if state == Places.MOUNTED:
            root = self._cb_places.get_mount_point()
            path = os.altsep.join((root, path))
        return path, file_name, state, file_id

    def _edit_key_words(self):
        curr_idx = self.view.filesList.currentIndex()
        u_data = self.view.filesList.model().data(curr_idx, Qt.UserRole)

        titles = ('Enter new tags', 'Select tags from list',
                  'Apply key words / tags')
        tag_list = self._dbu.select_other('TAGS').fetchall()
        sel_tags = self._dbu.select_other('FILE_TAGS', (u_data[0],)).fetchall()

        edit_tags = ItemEdit(titles,
                             [tag[0] for tag in tag_list],
                             [tag[0] for tag in sel_tags], re_=True)

        if edit_tags.exec_():
            res = edit_tags.get_result()

            to_del, to_add = self._del_add_items(res, sel_tags)

            self._del_item_links(to_del, file_id=u_data[0],
                                 sqls=('TAG_FILE', 'TAG_FILES', 'TAG'))
            self._add_item_links(to_add, file_id=u_data[0],
                                 sqls=('TAGS_BY_NAME', 'TAGS', 'TAG_FILE'))

            self._populate_tag_list()
            self._populate_comment_field(u_data, edit=True)

    @staticmethod
    def _del_add_items(new_list, old_list):
        old_words_set = set([item[0] for item in old_list])
        new_words_set = set(new_list)

        to_del = old_words_set.difference(new_words_set)
        to_del_ids = [item[1] for item in old_list if item[0] in to_del]

        old_words_set.add('')
        to_add = new_words_set.difference(old_words_set)

        return to_del_ids, to_add

    def _del_item_links(self, items2del, file_id, sqls):
        for item in items2del:
            self._dbu.delete_other(sqls[0], (item, file_id))
            res = self._dbu.select_other(sqls[1], (item,)).fetchone()
            if not res:
                self._dbu.delete_other(sqls[2], (item,))

    def _add_item_links(self, items2add, file_id, sqls):
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
        model().data(curr_idx, Qt.UserRole) = (FileID, DirID, CommentID, ExtID, PlaceId)
        """
        curr_idx = self.view.filesList.currentIndex()
        u_data = self.view.filesList.model().data(curr_idx, Qt.UserRole)

        titles = ('Enter authors separated by commas',
                  'Select authors from list', 'Apply authors')
        authors = self._dbu.select_other('AUTHORS').fetchall()
        sel_authors = self._dbu.select_other('FILE_AUTHORS', (u_data[0],)).fetchall()

        edit_authors = ItemEdit(titles,
                                [tag[0] for tag in authors],
                                [tag[0] for tag in sel_authors])

        if edit_authors.exec_():
            res = edit_authors.get_result()

            to_del, to_add = self._del_add_items(res, sel_authors)

            self._del_item_links(to_del, file_id=u_data[0],
                                 sqls=('AUTHOR_FILE', 'AUTHOR_FILES', 'AUTHOR'))
            self._add_item_links(to_add, file_id=u_data[0],
                                 sqls=('AUTHORS_BY_NAME', 'AUTHORS', 'AUTHOR_FILE'))

            self._populate_author_list()
            self._populate_comment_field(u_data, edit=True)

    def _check_existence(self):
        """
        Check if comment record already created for file
        Note: user_data = (FileID, DirID, CommentID, ExtID, PlaceId)
        :return: (file_id, dir_id, comment_id, comment, book_title)
        """
        file_comment = namedtuple('file_comment',
                                  'file_id dir_id comment_id comment book_title')
        curr_idx = self.view.filesList.currentIndex()
        user_data = self.view.filesList.model().data(curr_idx, Qt.UserRole)
        comment = self._dbu.select_other("FILE_COMMENT", (user_data[2],)).fetchone()
        res = file_comment._make(user_data[:3] + (comment if comment else ('', '')))
        if not comment:
            comment = ('', '')
            comment_id = self._dbu.insert_other('COMMENT', comment)
            self._dbu.update_other('FILE_COMMENT', (comment_id, res.file_id))
            self.view.filesList.model().update(curr_idx,
                                               user_data[:2] + (comment_id,)
                                               + user_data[3:], Qt.UserRole)
            res = res._replace(comment_id=comment_id,
                               comment=comment[0], book_title=comment[1])
        return res

    def _restore_file_list(self, curr_dir_idx):
        if self.same_db:
            settings = QSettings()
            self.file_list_source = settings.value('FILE_LIST_SOURCE', MyController.FOLDER)
            row = settings.value('FILE_IDX', -1)
        else:
            self.file_list_source = MyController.FOLDER
            row = -1

        if self.file_list_source == MyController.FAVORITE:
            self._favorite_file_list()
        elif self.file_list_source == MyController.FOLDER:
            dir_idx = self.view.dirTree.model().data(curr_dir_idx, Qt.UserRole)
            self._populate_file_list(dir_idx)
        else:
            self._list_of_selected_files()

        if row == -1:
            idx = QModelIndex()
        else:
            idx = self.view.filesList.model().index(row, 0)

        if idx.isValid():
            self.view.filesList.setCurrentIndex(idx)
            self.view.filesList.selectionModel().select(idx, QItemSelectionModel.Select)

    def _edit_title(self):
        checked = self._check_existence()
        data_, ok_pressed = QInputDialog.getText(self.view.extList, 'Input book title',
                                                 '', QLineEdit.Normal, getattr(checked, 'book_title'))
        if ok_pressed:
            self._dbu.update_other('BOOK_TITLE', (data_, checked.comment_id))
            self._populate_comment_field(checked, edit=True)

    def _edit_comment(self):
        # self._edit_comment_item(('COMMENT', 'Input comment'), 'comment')
        #    _edit_comment_item(self, to_update, item_no):
        checked = self._check_existence()
        data_, ok_pressed = QInputDialog.getMultiLineText(self.view.extList,
                                                          'Input comment', '',
                                                          getattr(checked, 'comment'))
        if ok_pressed:
            self._dbu.update_other('COMMENT', (data_, checked.comment_id))
            self._populate_comment_field(checked, edit=True)


    def _populate_ext_list(self):
        ext_list = self._dbu.select_other('EXT')
        model = TreeModel()
        model.append_model_data(ext_list)
        model.setHeaderData(0, Qt.Horizontal, "Extensions")
        self.view.extList.setModel(model)
        self.view.extList.selectionModel().selectionChanged.connect(self._ext_sel_changed)

    def _ext_sel_changed(self, selected: QItemSelection, deselected: QItemSelection):
        """
        Selection changed for view.extList, save new selection
        :param selected: QItemSelection
        :param deselected: QItemSelection
        :return: None
        """
        model = self.view.extList.model()
        for id in selected.indexes():
            if model.rowCount(id) > 0:
                self.view.extList.setExpanded(id, True)
                sel = QItemSelection(model.index(0, 0, id),
                                     model.index(model.rowCount(id) - 1, model.columnCount(id) - 1, id))
                self.view.extList.selectionModel().select(sel, QItemSelectionModel.Select)

        for id in deselected.indexes():
            if id.parent().isValid():
                self.view.extList.selectionModel().select(id.parent(), QItemSelectionModel.Deselect)

        self._save_ext_selection()

    def _save_ext_selection(self):
        idxs = self.view.extList.selectedIndexes()
        sel = []
        for ss in idxs:
            sel.append((ss.row(), ss.parent().row()))

        settings = QSettings()
        settings.setValue('EXT_SEL_LIST', sel)

    def _populate_tag_list(self):
        tag_list = self._dbu.select_other('TAGS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, ("Tags",))
        for tag, id_ in tag_list:
            model.append_row(tag, id_)
        self.view.tagsList.setModel(model)
        self.view.tagsList.selectionModel().selectionChanged.connect(self._tag_sel_changed)

    def _tag_sel_changed(self):
        idxs = self.view.tagsList.selectedIndexes()
        sel = []
        for ss in idxs:
            sel.append((ss.row(), ss.parent().row()))

        settings = QSettings()
        settings.setValue('TAG_SEL_LIST', sel)

    def _restore_tag_selection(self):
        if self.same_db:
            settings = QSettings()
            sel = settings.value('TAG_SEL_LIST', [])
            model = self.view.tagsList.model()
            for ss in sel:
                idx = model.index(ss[0], 0, QModelIndex())
                self.view.tagsList.selectionModel().select(idx, QItemSelectionModel.Select)

    def _populate_author_list(self):
        author_list = self._dbu.select_other('AUTHORS')
        model = TableModel()
        model.setHeaderData(0, Qt.Horizontal, "Authors")
        for author, id_ in author_list:
            model.append_row(author, id_)
        self.view.authorsList.setModel(model)
        self.view.authorsList.selectionModel().selectionChanged.connect(self._author_sel_changed)

    def _author_sel_changed(self):
        idxs = self.view.authorsList.selectedIndexes()
        sel = []
        for ss in idxs:
            sel.append((ss.row(), ss.parent().row()))

        settings = QSettings()
        settings.setValue('AUTHOR_SEL_LIST', sel)

    def _restore_author_selection(self):
        if self.same_db:
            settings = QSettings()
            sel = settings.value('AUTHOR_SEL_LIST', [])
            model = self.view.authorsList.model()
            for ss in sel:
                idx = model.index(ss[0], 0, QModelIndex())
                self.view.authorsList.selectionModel().select(idx, QItemSelectionModel.Select)

    def _populate_file_list(self, dir_idx):
        """
        :param dir_idx:
        :return:
        """
        self.file_list_source = MyController.FOLDER
        settings = QSettings()
        settings.setValue('FILE_LIST_SOURCE', self.file_list_source)
        model = self._set_file_model()
        if dir_idx:
            files = self._dbu.select_other('FILES_CURR_DIR', (dir_idx[0],))
            self._show_files(files, model)

            self.view.statusbar.showMessage('{} ({})'.format(dir_idx[2],
                                                             model.rowCount(QModelIndex())))
        else:
            self.view.statusbar.showMessage('No data')

    def _set_file_model(self):
        model = TableModel(parent=self.view.filesList)
        proxy_model = ProxyModel2()
        proxy_model.setSourceModel(model)
        model.setHeaderData(0, Qt.Horizontal, getattr(self.fields, 'headers'))
        self.view.filesList.setModel(proxy_model)
        return proxy_model

    def _show_files(self, files, model):
        idx = getattr(self.fields, 'indexes')
        for ff in files:
            ff1 = [ff[i] for i in idx]
            model.append_row(tuple(ff1), ff[-5:])

        self.view.filesList.selectionModel().currentRowChanged.connect(self._cur_file_changed)
        index_ = model.index(0, 0)
        self.view.filesList.setCurrentIndex(index_)
        self.view.filesList.setFocus()

    def _cur_file_changed(self, curr_idx):
        settings = QSettings()
        settings.setValue('FILE_IDX', curr_idx.row())
        if curr_idx.isValid():
            data = self.view.filesList.model().data(curr_idx, role=Qt.UserRole)
            self._populate_comment_field(data)

    def _populate_comment_field(self, user_data, edit=False):
        file_id = user_data[0]
        comment_id = user_data[2]
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
                '<html><body><p><a href="Edit key words">Key words</a>: {}</p>'
                    .format(', '.join([tag[0] for tag in tags])),
                '<p><a href="Edit authors">Authors</a>: {}</p>'
                    .format(', '.join([author[0] for author in authors])),
                '<p><a href="Edit title"4>Title</a>: {}</p>'.format(comment[1]),
                '<p><a href="Edit comment">Comment</a> {}</p></body></html>'
                    .format(comment[0]))))

            if not self.file_list_source == MyController.FOLDER:
                f_idx = self.view.filesList.currentIndex()
                file_id, dir_id, _, _, _ = \
                    self.view.filesList.model().data(f_idx, role=Qt.UserRole)
                path = self._dbu.select_other('PATH', (dir_id,)).fetchone()
                self.view.statusbar.showMessage(path[0])

            if edit:
                self._update_commented_date(file_id)

    def _update_commented_date(self, file_id):
        self._dbu.update_other('COMMENT_DATE', (file_id,))
        model = self.view.filesList.model()
        heads = model.get_headers()
        if "Commented" in heads:
            idx = model.sourceModel().createIndex(
                self.view.filesList.currentIndex().row(), heads.index("Commented"))
            cur_date = QDate.currentDate().toString(Qt.ISODate)
            model.update(idx, cur_date)

    def _populate_all_widgets(self):
        self._cb_places.populate_cb_places()
        self._populate_ext_list()
        self._restore_ext_selection()
        self._populate_tag_list()
        self._restore_tag_selection()
        self._populate_author_list()
        self._restore_author_selection()
        self._populate_directory_tree()

    def _restore_ext_selection(self):
        if self.same_db:
            settings = QSettings()
            sel = settings.value('EXT_SEL_LIST', [])
            model = self.view.extList.model()
            for ss in sel:
                if ss[1] == -1:
                    parent = QModelIndex()
                else:
                    parent = model.index(ss[1], 0)
                    self.view.extList.setExpanded(parent, True)

                idx = model.index(ss[0], 0, parent)

                self.view.extList.selectionModel().select(idx, QItemSelectionModel.Select)

    def _populate_directory_tree(self):
        dirs = self._get_dirs(self._cb_places.get_curr_place()[1][0])

        model = TreeModel()
        model.append_model_data(dirs)

        model.setHeaderData(0, Qt.Horizontal, ("Directories",))
        self.view.dirTree.setModel(model)

        cur_dir_idx = self._restore_path()

        self._restore_file_list(cur_dir_idx)

        if len(dirs):
            if self._cb_places.get_disk_state() & (Places.NOT_DEFINED | Places.NOT_MOUNTED):
                self._show_message('Files are in an inaccessible place')

        self.view.dirTree.selectionModel().selectionChanged.connect(self._cur_dir_changed)

    def _get_dirs(self, place_id):
        """
        Returns directory tree for current place
        :param place_id:
        :return: list of tuples (Dir name, DirID, ParentID, Full path of dir)
        """
        dirs = []
        dir_tree = self._dbu.dir_tree_select(dir_id=0, level=0, place_id=place_id)

        if self._cb_places.get_disk_state() == Places.MOUNTED:
            root = self._cb_places.get_mount_point()
            for rr in dir_tree:
                dirs.append((os.path.split(rr[1])[1], rr[0], rr[2], os.altsep.join((root, rr[1]))))
        else:
            for rr in dir_tree:
                dirs.append((os.path.split(rr[1])[1], rr[0], rr[2], rr[1]))
        return dirs

    def _cur_dir_changed(self, selected):  # , unselected):
        """
        Changed selection in dirTree
        :param selected:  QItemSelection
        :return: None
        """
        idx = selected.indexes()
        if idx:  # dir_idx = (DirID, ParentID, Full path)
            MyController._save_path(idx[0])
            dir_idx = self.view.dirTree.model().data(idx[0], Qt.UserRole)
            self._populate_file_list(dir_idx)

    @staticmethod
    def _save_path(idx):
        id = idx
        aux = []
        while id.isValid():
            aux.append(id.row())
            id = id.parent()
        aux.reverse()

        settings = QSettings()
        settings.setValue('TREE_SEL_IDX', QVariant(aux))

    def _restore_path(self):
        """
        restore expand state and current index of dirTree
        :return: current index
        """
        model = self.view.dirTree.model()
        if self.same_db:
            settings = QSettings()
            aux = settings.value('TREE_SEL_IDX', [0])
            parent = QModelIndex()
            for id in aux:
                if parent.isValid():
                    if not self.view.dirTree.isExpanded(parent):
                        self.view.dirTree.setExpanded(parent, True)
                idx = model.index(int(id), 0, parent)
                self.view.dirTree.setCurrentIndex(idx)
                parent = idx
            return parent

        idx = model.index(0, 0, QModelIndex())
        self.view.dirTree.setCurrentIndex(idx)
        return idx

    def _del_empty_dirs(self):
        self._dbu.delete_other('DEL_EMPTY_DIRS', ())

    def _rescan_dir(self):
        idx = self.view.dirTree.currentIndex()
        dir_ = self.view.dirTree.model().data(idx, Qt.UserRole)
        ext_ = self._get_selected_ext()
        ext_item, ok_pressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                    'Input extensions (* - all)',
                                                    QLineEdit.Normal, ext_)
        if ok_pressed:
            files = MyController._yield_files(dir_[2], ext_item.strip())
            if files:
                self._load_files(files)

    def on_scan_files(self):
        """
        The purpose is to fill the data base with files by means of
        scanning the file system
        :return: None
        """
        if self._cb_places.get_disk_state() & \
                (Places.MOUNTED | Places.NOT_REMOVAL | Places.NOT_DEFINED):
            _data = self._scan_file_system()
            if _data:
                self._load_files(_data)
        else:
            self._show_message("Can't scan disk for files. Disk is not accessible.")

    def _load_files(self, files):
        curr_place = self._cb_places.get_curr_place()
        self.obj_thread = LoadFiles(self._connection, curr_place, files)
        self._run_in_qthread(self._dir_update)

    def _scan_file_system(self):
        ext_ = self._get_selected_ext()
        ext_item, ok_pressed = QInputDialog.getText(self.view.extList, "Input extensions",
                                                    '', QLineEdit.Normal, ext_)
        if ok_pressed:
            root = QFileDialog().getExistingDirectory(self.view.extList, 'Select root folder')
            # TODO check for valid scaning in removable disk
            if root:
                self._cb_places.update_place_name(root)
                return MyController._yield_files(root, ext_item)

        return ()  # not ok_pressed or root is empty

    def _show_message(self, message, time=3000):
        self.view.statusbar.showMessage(message, time)

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

    def _resize_columns(self):
        w = self.view.filesList.width()
        widths = self._calc_collumns_width()
        if len(widths) > 1:
            ww = w * 0.75
            sum_w = sum(widths)
            if ww > sum_w:
                widths[0] = w - sum_w
            else:
                widths[0] = w * 0.25
                for i in range(1, len(widths)):
                    widths[i] = ww / sum_w * widths[i]
            for k in range(0, len(widths)):
                self.view.filesList.setColumnWidth(k, widths[k])
        else:
            self.view.filesList.setColumnWidth(0, w)

    def _calc_collumns_width(self):
        width = [0]
        font_metrics = self.view.filesList.fontMetrics()
        heads = self.view.filesList.model().get_headers()
        if len(heads) > 1:
            for head in heads[1:]:
                ind = SetFields.Heads.index(head)
                width.append(font_metrics.boundingRect(SetFields.Masks[ind]).width())
        return width
