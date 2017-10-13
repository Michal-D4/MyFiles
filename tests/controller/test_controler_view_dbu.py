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

    def test_add_extension(self):
        '''
        check called_with for
        1) dbu.select_other
        2) dbu.insert_other
        3) model.appendData
        4) model.createIndex
        5) extList.setCurrentIndex
        '''
        self.controller.dbu = Mock()

        mock_select_other = Mock()
        self.controller.dbu.select_other.return_value = mock_select_other
        mock_select_other.fetchone.return_value = (0,)

        self.controller.dbu.insert_other.return_value = 1

        mock_model = Mock()
        self.mock_view.extList.model.return_value = mock_model
        mock_model.rowCount.return_value = 1
        mock_model.createIndex.return_value = 'created index'

        self.controller.add_extension('pdf')
        self.controller.dbu.select_other.assert_called_with('HAS_EXT', ('pdf',))
        self.controller.dbu.insert_other.assert_called_with('EXT', {'ext': 'pdf'})
        mock_model.appendData.assert_called_with(('pdf', 1))
        mock_model.createIndex.assert_called_with(0, 0, 0)
        self.mock_view.extList.setCurrentIndex.assert_called_with('created index')

    def test_allowed_removal(self):
        mock_select_other = Mock()
        self.mock_dbu.select_other.return_value = mock_select_other
        mock_select_other.fetchone.return_value = ()    # allowed if not exist

        res = self.controller.allowed_removal('allowed')
        self.assertEqual(res, True)

        mock_select_other.fetchone.return_value = (1,)  # not allowed == exist

        res = self.controller.allowed_removal('not allowed')
        self.assertEqual(res, False)

    def test_remove_extension(self):
        mock_ext_list = Mock()
        self.controller.view.extList = mock_ext_list

        mock_mod = Mock(spec_set=MyListModel)
        mock_mod.data.return_value = 1
        mock_ext_list.model.return_value = mock_mod

        mock_index = Mock()
        mock_index.row.return_value = 1
        mock_ext_list.currentIndex.return_value = mock_index

        self.controller.allowed_removal = Mock()
        self.controller.allowed_removal.return_value = True

        self.controller.remove_extension()
        self.mock_dbu.delete_other.assert_called_with('EXT', (1,))
        mock_mod.removeRows.assert_called_with(1)
        mock_ext_list.setCurrentIndex.assert_called_with(mock_index)

    def test_populate_cb_places ( self ):
        self.mock_dbu.select_other.return_value = ((1, 2, 3), (4, 5, 6))

        self.controller.populate_cb_places()
        self.mock_view.cb_places.addItems.assert_called_once()

    def test_on_change_data(self):
        mock_add_place = Mock()
        self.controller.add_place = mock_add_place

        self.controller.on_change_data('cb_places', 'data')
        mock_add_place.assert_called_once()

    def test_add_place(self):
        mock_ask_rename_or_new = Mock()
        mock_ask_rename_or_new.side_effect = (0, 1, 2, 3)
        self.controller.ask_rename_or_new = mock_ask_rename_or_new

        self.controller.rename_place = Mock()  # addItems is also called here

        self.controller.add_place((1, 'data'))
        self.mock_dbu.insert_other.assert_called_with('PLACES', (1, 'data', 'data'))

        self.controller.add_place((1, 'data'))

        self.controller.add_place((1, 'data'))

        self.controller.add_place((0, 'data'))
        self.mock_view.cb_places.addItems.assert_called_once()

    def test_rename_place(self):
        self.controller.places = [(1, 'a', 'a')]
        self.controller.curr_place = (1, 'a', 'a')

        self.controller.rename_place((1, 'data'))
        self.mock_view.cb_places.addItems.assert_called_once()
        self.mock_dbu.update_other.assert_called_with('PLACES', ('data', 0))

    def test_populate_ext_list(self):
        self.mock_dbu.select_other.return_value = [('e1', 1), ('e2', 2)]

        mock_model_class = Mock()
        my_controller.MyListModel = mock_model_class
        mock_model_obj = Mock(spec_set=MyListModel)
        mock_model_class.return_value = mock_model_obj

        self.controller.populate_ext_list()
        self.mock_dbu.select_other.assert_called_once_with('EXT')
        # mock_model_obj.append_row.assert_called_with((1, 'e1')) # only last call tested
        mock_model_obj.append_row.assert_called_with((2, 'e2'))
        self.mock_view.extList.setModel.assert_called_once()



