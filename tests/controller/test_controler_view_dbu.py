import unittest

from model.db_utils import *
from unittest.mock import MagicMock, Mock
from unittest.mock import patch, call
from controller.my_qt_model import TreeModel, MyListModel
from controller import my_controller
from model.db_utils import DBUtils


class TestMyControllerViewDbu(unittest.TestCase):
    def setUp(self):
        app = Mock()
        self.controller = my_controller.MyController(app)

        self.mock_view = Mock()
        self.controller.view = self.mock_view

        self.mock_dbu = Mock(spec_set=DBUtils)
        self.controller.dbu = self.mock_dbu

    def tearDown(self):
        # self.connection.close()
        pass

    def test_populate_cb_places ( self ):
        self.mock_dbu.select_other.return_value = ((1, 2, 3), (4, 5, 6))

        self.controller._populate_cb_places()
        self.mock_dbu.select_other.assert_called_once_with('PLACES')
        self.mock_view.cb_places.addItems.assert_called_once()
        self.mock_view.cb_places.clear.assert_has_calls([call.cb_places.clear(), ])
        self.assertEqual(self.mock_view.cb_places.blockSignals.mock_calls,
                         [call.cb_places.blockSignals(True),
                          call.cb_places.blockSignals(False)])

    @patch.object(my_controller.MyController, '_rename_place')
    @patch.object(my_controller.MyController, '_ask_rename_or_new')
    def test_add_place(self, mock_ask_rename_or_new, mock_rename_place):

        mock_ask_rename_or_new.side_effect = (0, 1, 2, 3)

        print('|-> test_add_place 1')
        self.controller._add_place((1, 'data'))
        self.mock_dbu.insert_other.assert_called_once_with('PLACES', (1, 'data', 'data'))

        print('|-> test_add_place 2')
        self.controller._add_place((1, 'data'))
        mock_rename_place.assert_called_once_with((1, 'data'))

        print('|-> test_add_place 3')
        self.controller._add_place((1, 'data'))
        self.mock_view.cb_places.removeItem.assert_called_once()

    def test_rename_place(self):
        self.controller.places = [(0, 'a', 'a')]
        self.controller.curr_place = (0, 'a', 'a')

        self.controller._rename_place((1, 'data'))
        self.mock_view.cb_places.removeItem.assert_called_once()
        self.mock_dbu.update_other.assert_called_with('PLACES', ('data', 0))

    def test_populate_ext_list(self):
        self.mock_dbu.select_other.return_value = [('e1', 1), ('e2', 2)]

        mock_model_class = Mock()
        my_controller.MyListModel = mock_model_class
        mock_model_obj = Mock(spec_set=MyListModel)
        mock_model_class.return_value = mock_model_obj

        self.controller._populate_ext_list()
        self.mock_dbu.select_other.assert_called_once_with('EXT')
        # mock_model_obj.append_row.assert_called_with((1, 'e1')) # only last call tested
        mock_model_obj.append_row.assert_called_with((2, 'e2'))
        self.mock_view.extList.setModel.assert_called_once()

    @patch.object(my_controller.MyController, '_ask_switch_to_unavailable_storage')
    @patch.object(my_controller.MyController, '_is_place_available')
    def test_change_place ( self, mock_is_place_available,
                            mock_ask_switch_to_unavailable_storage ):
        self.controller.places = [(0, 'in', 'out'),]
        self.controller.curr_place = (0, 'in', 'out')

        mock_is_place_available.side_effect = (True, False, False)
        mock_ask_switch_to_unavailable_storage.side_effect = (0, 1)

        self.controller._change_place((0, 'data'))
        mock_is_place_available.assert_called_once()
        mock_ask_switch_to_unavailable_storage.assert_not_called()

        self.controller._change_place((0, 'data'))
        mock_ask_switch_to_unavailable_storage.assert_called_once()

        self.controller._change_place((0, 'data'))
        self.mock_view.cb_places.setCurrentIndex.assert_called_once_with(0)

    def test_populate_tag_list(self):
        pass

    def test_populate_author_list(self):
        pass

    def test_populate_file_list(self):
        pass

    def test_populate_comment_field(self):
        pass

    @patch('controller.my_controller.TreeModel', spec_set=TreeModel)
    def test_populate_directory_tree(self, mock_model):
        mock_model.return_value = 'model'

        self.controller._populate_directory_tree()
        self.mock_dbu.dir_tree_select.assert_called_once_with(dir_id=0, level=0)
        mock_model.assert_called_once()
        self.mock_view.dirTree.setModel.assert_called_once_with('model')



