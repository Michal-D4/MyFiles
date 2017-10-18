import sqlite3
import unittest
from unittest.mock import Mock, patch, call

from controller import my_controller
from controller.places import Places
# from controller.my_qt_model import MyListModel
# from model.db_utils import *


class TestMyController(unittest.TestCase):
    def setUp(self):
        app = Mock()
        self.controller = my_controller.MyController(app)

    def tearDown(self):
        pass

    @patch('controller.my_controller.os.walk')
    def test_yield_files(self, mock_os_walk):
        mock_os_walk.return_value = [('1', ('2', '3'), ('4.txt', '5.chm', '7.doc')),
                                     ('2', ('8', '9'), ('10.txt', '6.com'))]
        aa = my_controller.yield_files('root', 'txt, .chm,  jpg')
        bb = tuple(aa)
        test_data = ('1\\4.txt', '1\\5.chm', '2\\10.txt')
        self.assertTupleEqual(bb, test_data)

    @patch('controller.my_controller.os.walk')
    def test_yield_files_no_extensions(self, mock_os_walk):
        mock_os_walk.return_value = [('1', ('2', '3'), ('4.txt', '5.chm', '7.doc')),
                                     ('2', ('8', '9'), ('10.txt', '6.com'))]
        aa = my_controller.yield_files('root', '')
        bb = tuple(aa)
        test_data = ('1\\4.txt', '1\\5.chm', '1\\7.doc', '2\\10.txt', '2\\6.com')
        self.assertTupleEqual(bb, test_data)

    def test_on_change_data_cb_places(self):
        data = (1, 'data')

        mock_cb_places = Mock(spec_set=Places)
        self.controller.cb_places = mock_cb_places

        self.controller.on_change_data('cb_places', data)
        mock_cb_places.about_change_place.assert_called_once_with(data)

    @patch('controller.my_controller.create_db', autospec=True)
    @patch('controller.my_controller.sqlite3', spec_set=sqlite3)
    @patch.object(my_controller.MyController, '_populate_all_widgets')
    def test_on_open_db_create(self, mock_populate, mock_sqlite3, mock_create_db):

        self.controller.on_open_db('my file', True)

        mock_sqlite3.connect.assert_called_with('my file', detect_types=3)
        mock_create_db.create_all_objects.assert_called_once()
        mock_populate.assert_called_once()

    @patch('controller.my_controller.create_db', autospec=True)
    @patch('controller.my_controller.sqlite3', spec_set=sqlite3)
    @patch.object(my_controller.MyController, '_populate_all_widgets')
    def test_on_open_db_connect(self, mock_populate, mock_sqlite3, mock_create_db):

        self.controller.on_open_db('my file', False)

        mock_sqlite3.connect.assert_called_with('my file', detect_types=3)
        mock_create_db.create_all_objects.assert_not_called()
        mock_populate.assert_called_once()

    @patch.object(my_controller.MyController, '_populate_comment_field')
    @patch.object(my_controller.MyController, '_populate_file_list')
    @patch.object(my_controller.MyController, '_populate_author_list')
    @patch.object(my_controller.MyController, '_populate_tag_list')
    @patch.object(my_controller.MyController, '_populate_ext_list')
    @patch.object(my_controller.MyController, '_populate_directory_tree')
    @patch.object(my_controller.MyController, '_populate_all_widgets')
    def test_on_populate_view(self, mock_populate_all_widgets,
                              mock_populate_directory_tree,
                              mock_populate_ext_list,
                              mock_populate_tag_list,
                              mock_populate_author_list,
                              mock_populate_file_list,
                              mock_populate_comment_field):

        mock_cb_places = Mock(spec_set=Places)
        self.controller.cb_places = mock_cb_places

        self.controller.on_populate_view('nothing')

        mock_populate_all_widgets.assert_not_called()
        mock_populate_directory_tree.assert_not_called()
        mock_populate_ext_list.assert_not_called()
        mock_populate_tag_list.assert_not_called()
        mock_populate_author_list.assert_not_called()
        mock_populate_file_list.assert_not_called()
        mock_populate_comment_field.assert_not_called()
        mock_cb_places.populate_cb_places.assert_not_called()

        self.controller.on_populate_view('all')
        mock_populate_all_widgets.assert_called_once()

        self.controller.on_populate_view('dirTree')
        mock_populate_directory_tree.assert_called_once()

        self.controller.on_populate_view('extList')
        mock_populate_ext_list.assert_called_once()

        self.controller.on_populate_view('tagsList')
        mock_populate_tag_list.assert_called_once()

        self.controller.on_populate_view('authorsList')
        mock_populate_author_list.assert_called_once()

        self.controller.on_populate_view('filesList')
        mock_populate_file_list.assert_called_once()

        self.controller.on_populate_view('commentField')
        mock_populate_comment_field.assert_called_once()

        self.controller.on_populate_view('cb_places')
        mock_cb_places.populate_cb_places.assert_called_once()

    # _ask_rename_or_new - contains QMessageBox() only - nothing to test
    # def test_ask_rename_or_new(self):
    #     pass

    @patch('controller.my_controller.Places')
    @patch.object(my_controller.MyController, '_populate_comment_field')
    @patch.object(my_controller.MyController, '_populate_file_list')
    @patch.object(my_controller.MyController, '_populate_author_list')
    @patch.object(my_controller.MyController, '_populate_tag_list')
    @patch.object(my_controller.MyController, '_populate_ext_list')
    @patch.object(my_controller.MyController, '_populate_directory_tree')
    def test_populate_all_widgets(self, mock_populate_directory_tree,
                                  mock_populate_ext_list,
                                  mock_populate_tag_list,
                                  mock_populate_author_list,
                                  mock_populate_file_list,
                                  mock_populate_comment_field,
                                  mock_places):
        mock_cb_places = Mock(spec_set=Places)
        mock_places.return_value = mock_cb_places

        self.controller._populate_all_widgets()

        mock_populate_directory_tree.assert_called_once()
        mock_populate_file_list.assert_called_once()
        mock_populate_comment_field.assert_called_once()
        mock_populate_ext_list.assert_called_once()
        mock_populate_tag_list.assert_called_once()
        mock_populate_author_list.assert_called_once()
        mock_cb_places.populate_cb_places.assert_called_once()

    @patch.object(my_controller.MyController, '_read_from_file')
    @patch.object(my_controller.MyController, '_scan_file_system')
    @patch('controller.my_controller.LoadDBData', autospec=True)
    def test_on_scan_files(self, mock_LoadDBData, mock_scan_file_system,
                           mock_read_from_file):

        mock_cb_places = Mock(spec_set=Places)
        self.controller.cb_places = mock_cb_places

        mock_cb_places.is_place_available.side_effect = (True, False)

        mock_scan_file_system.return_value = '_scan_file_system'

        mock_read_from_file.return_value = '_read_from_file'

        mock_ld = Mock()
        mock_LoadDBData.return_value = mock_ld

        self.controller._populate_directory_tree = Mock()

        self.controller.on_scan_files()
        mock_scan_file_system.assert_called_once()
        mock_read_from_file.assert_not_called()
        mock_ld.load_data.assert_called_with('_scan_file_system')

        self.controller.on_scan_files()
        mock_read_from_file.assert_called_once()
        mock_ld.load_data.assert_called_with('_read_from_file')

        pass

    @patch.object(my_controller.MyController, '_get_selected_extensions')
    @patch('controller.my_controller.QFileDialog')
    @patch('controller.my_controller.QInputDialog')
    @patch('controller.my_controller.yield_files')
    def test_scan_file_system(self, mock_yield_files, mock_QInputDialog, mock_QFileDialog,
                              mock_get_selected_extensions):

        mock_QInputDialog.getText.side_effect = (('pdf', False), ('pdf', True), ('pdf', True))
        mock_QFileDialog().getExistingDirectory.side_effect = ('', 'root')
        mock_yield_files.return_value = ('file_list',)

        res = self.controller._scan_file_system()  # QInputDialog => Cancel
        mock_get_selected_extensions.assert_has_calls([call._get_selected_extensions(), ])
        mock_QFileDialog.getExistingDirectory.assert_not_called()
        self.assertEqual(res, ())

        res = self.controller._scan_file_system()  # QInputDialog => Ok, root = ''
        mock_QFileDialog().getExistingDirectory.assert_called_once()
        self.assertEqual(res, ())

        res = self.controller._scan_file_system()  # QInputDialog => Ok, root = 'root'
        mock_yield_files.assert_called_once_with('root', 'pdf')
        self.assertEqual(res, ('file_list',))

    def test_read_from_file(self):
        pass