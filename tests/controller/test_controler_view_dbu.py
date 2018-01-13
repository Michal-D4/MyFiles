import unittest

from unittest.mock import MagicMock, Mock
from unittest.mock import patch, call
from controller.table_model import TableModel
from controller.tree_model import TreeModel
from controller import my_controller
from model.utilities import DBUtils


class TestMyControllerViewDbu(unittest.TestCase):
    def setUp(self):
        app = Mock()
        self.controller = my_controller.MyController(app)

        self.mock_view = Mock()
        self.controller.ui = self.mock_view

        self.mock_dbu = Mock(spec_set=DBUtils)
        self.controller._dbu = self.mock_dbu

    def tearDown(self):
        # self.connection.close()
        pass

    @patch('controller.my_controller.TreeModel', spec_set=TreeModel)
    def test__populate_ext_list(self, mock_model):
        rv = [(101, 'e1', 1), (102, 'e2', 2),
              (103, 'e3', 1), (104, 'e4', 0),
              (1, 'g1', 0), (2, 'g2', 0)]
        self.mock_dbu.select_other.return_value = rv

        self.controller._populate_ext_list()

        self.mock_dbu.select_other.assert_called_once_with('EXT')
        mock_model.assert_called_once_with(rv)
        mock_model.return_value.setHeaderData.assert_called_with(0, 1, "Extensions")
        self.mock_view.extList.setModel.assert_called_once()

    @patch('controller.my_controller.TableModel', spec_set=TableModel)
    def test__populate_tag_list(self, mock_model):
        self.mock_dbu.select_other.return_value = (('tag 1', 1), ('tag 2', 2))

        self.controller._populate_tag_list()
        self.mock_dbu.select_other.assert_called_once_with('TAGS')
        count = mock_model.return_value.append_row.call_count
        self.assertEqual(count, 2, msg='append_row must be called 2 times, but not')
        mock_model.return_value.append_row.assert_called_with('tag 2', 2)

    @patch('controller.my_controller.TableModel', spec_set=TableModel)
    def test__populate_author_list(self, mock_model):
        self.mock_dbu.select_other.return_value = (('author 1', 1), ('author 2', 2))

        self.controller._populate_author_list()
        self.mock_dbu.select_other.assert_called_once_with('AUTHORS')
        count = mock_model.return_value.append_row.call_count
        self.assertEqual(count, 2, msg='append_row must be called 2 times, but not')
        mock_model.return_value.append_row.assert_called_with('author 2', 2)

    @patch('controller.my_controller.TableModel', spec_set=TableModel)
    def test__populate_file_list(self, mock_model):
        pass

    def test__populate_comment_field(self):
        pass

    @patch.object(my_controller.MyController, '_get_dirs')
    @patch.object(my_controller.MyController, '_populate_file_list')
    @patch('controller.my_controller.TreeModel', spec_set=TreeModel)
    def test__populate_directory_tree(self, mock_model, mock_file_list, mock_get_dirs):

        mock_get_dirs.return_value = []

        self.controller._populate_directory_tree()
        mock_get_dirs.assert_called_once_with(0)
        mock_model.assert_called_once()
        self.mock_view.dirTree.setModel.assert_called_once_with(mock_model.return_value)

    @patch('controller.my_controller.TreeModel', spec_set=TreeModel)
    def test__get_selected_extensions(self, mock_model):
        self.mock_view.extList.selectedIndexes.side_effect = ((1, 2), ())

        self.mock_view.extList.model.return_value = mock_model
        mock_model.data.side_effect = ('item1', 'item2')

        res = self.controller.get_selected_items()
        self.assertEqual(res, 'item1, item2', msg='Selected item1 and item2')

        res = self.controller.get_selected_items()
        self.assertEqual(res, '', msg='No selection. But returns!!!')
