import unittest
from unittest.mock import Mock, patch, call

import psutil
import ctypes
import socket

from controller.places import Places
from model.utilities import DBUtils
from controller.my_controller import *

from PyQt5.QtWidgets import QComboBox, QFileDialog


class TestPlaces(unittest.TestCase):
    def setUp(self):
        self.mock_controller = Mock(spec_set=MyController)
        # self.mock_view = Mock(spec_set=QComboBox)
        # self.mock_dbu = Mock(spec_set=DBUtils)
        # self.tested_places = Places(self.mock_view, self.mock_dbu)
        self.tested_places = Places(self.mock_controller)

    def tearDown(self):
        pass

    @patch.object(Places, '_change_place')
    @patch.object(Places, '_add_place')
    def test_about_change_place(self, mock_add_place, mock_change_place):
        data = (0, 'place 1')
        self.tested_places._curr_place = (0, (0, 'in', 'out'))

        # if data[0] >= len of list of places, then call _add_place
        #  now list is empty
        self.tested_places.about_change_place(data)
        mock_add_place.assert_called_once_with(data)

        self.tested_places._places.append(data)

        #  now len of list = 1 --> call _change_place
        self.tested_places.about_change_place(data)
        mock_change_place.assert_called_once_with(data)

    @patch.object(Places, '_remove_current_place')
    @patch.object(Places, '_ask_switch_to_unavailable_storage')
    @patch.object(Places, 'get_disk_state')
    def test__change_place(self, mock_disk_state,
                           mock_ask_switch_to_unavailable_storage,
                           mock_remove_current_place):
        self.tested_places._places = [(0, 'in', 'out'), ]
        self.tested_places._curr_place = (0, (0, 'in', 'out'))

        mock_disk_state.side_effect = (self.tested_places.MOUNTED,
                                       self.tested_places.NOT_MOUNTED,
                                       self.tested_places.NOT_MOUNTED,
                                       self.tested_places.NOT_MOUNTED)
        mock_ask_switch_to_unavailable_storage.side_effect = (0, 1, 2)

        self.tested_places._change_place((0, 'data'))
        mock_disk_state.assert_called_once()
        mock_ask_switch_to_unavailable_storage.assert_not_called()

        self.tested_places._change_place((0, 'data'))
        mock_ask_switch_to_unavailable_storage.assert_called_once()

        self.tested_places._change_place((0, 'data'))
        mock_remove_current_place.assert_called_once()

        self.tested_places._change_place((0, 'data'))
        self.tested_places._view.setCurrentIndex.assert_called_once_with(0)

    @patch.object(Places, '_not_in_dirs')
    def test__remove_current_place(self, mock_not_in_dirs):
        self.tested_places._places = [(0, 'in', 'out'), ]
        self.tested_places._curr_place = (0, (0, 'in', 'out'))

        self.tested_places._view.currentIndex.return_value = 0
        mock_not_in_dirs.side_effect = (False, True)

        self.tested_places._remove_current_place()
        mock_not_in_dirs.assert_called_once_with(0)
        self.tested_places._dbu.delete_other.assert_not_called()

        self.tested_places._remove_current_place()
        mock_not_in_dirs.assert_called_with(0)
        self.tested_places._dbu.delete_other.assert_called_once_with('PLACES', (0,))

    def test__rename_place(self):
        self.tested_places._places = [(0, 'a', 'a')]
        self.tested_places._curr_place = (0, (0, 'in', 'out'))

        self.tested_places._rename_place((1, 'data'))
        self.tested_places._view.addItems.assert_called_once()
        self.tested_places._dbu.update_other.assert_called_once_with('PLACES', ('data', 0))

    @patch('controller.places.socket', spec_set=socket)
    def test_populate_cb_places(self, mock_socket):
        self.tested_places._dbu.select_other.return_value = \
            [(1, 'inner name1', 3),
             (4, 'inner name2', 6)]

        mock_socket.gethostname.return_value = 'inner name2'

        self.tested_places.populate_cb_places()
        self.tested_places._dbu.select_other.assert_called_once_with('PLACES')
        self.tested_places._view.addItems.assert_called_once()
        self.tested_places._view.clear.assert_has_calls([call.cb_places.clear(), ])
        self.assertEqual(self.tested_places._view.blockSignals.mock_calls,
                         [call.blockSignals(True),
                          call.blockSignals(False)])

    @patch.object(Places, '_add_new')
    @patch.object(Places, '_ask_rename_or_new')
    def test__add_place_add_new(self, mock_ask_rename_or_new, mock__add_new):
        mock_ask_rename_or_new.return_value = 0

        self.tested_places._add_place((1, 'data'))
        mock__add_new.assert_called_once_with((1, 'data'))

    @patch.object(Places, '_rename_place')
    @patch.object(Places, '_ask_rename_or_new')
    def test__add_place_rename(self, mock_ask_rename_or_new, mock_rename_place):

        self.tested_places._curr_place = (0, (0, 'some_place', 'some_title'))

        mock_ask_rename_or_new.return_value = 1

        self.tested_places._add_place((1, 'data'))
        mock_rename_place.assert_called_once_with((0, 'data'))

    @patch.object(Places, '_ask_rename_or_new')
    def test__add_place_cancel(self, mock_ask_rename_or_new):

        self.tested_places._curr_place = (0, (0, 'some_place', 'some_title'))
        mock_ask_rename_or_new.return_value = 2

        self.tested_places._add_place((1, 'data'))
        self.tested_places._view.removeItem.assert_called_once()

    @patch.object(Places, '_get_mount_point')
    @patch('controller.places.socket', spec_set=socket)
    def test_is_disk_mounted(self, mock_socket, mock_get_mount_point):
        self.tested_places._places = [(1, 'inner name1', 3),
                                      (4, '', 6)]
        # self.tested_places._curr_place = (1, 'inner name1', 3)

        self.tested_places._view.currentIndex.side_effect = (1, 0, 0, 0)
        mock_socket.gethostname.side_effect = ('inner name1',
                                               'other_place',
                                               'other_place')
        mock_get_mount_point.side_effect = ('F:/', '')

        res = self.tested_places.get_disk_state()
        self.assertEqual(res, self.tested_places.NOT_DEFINED,
                         msg='Current place is not defined, but defined!!!')

        res = self.tested_places.get_disk_state()
        self.assertEqual(res, self.tested_places.NOT_REMOVAL,
                         msg='Current plase is not removable disk. But removal!!!')

        res = self.tested_places.get_disk_state()
        self.assertEqual(res, self.tested_places.MOUNTED,
                         msg='Removal disk is mounted. But not!!!')

        res = self.tested_places.get_disk_state()
        self.assertEqual(res, self.tested_places.NOT_MOUNTED,
                         msg='Removal disk is not mounted. But mounted!!!')

    @patch('controller.places.socket', spec_set=socket)
    def test_get_curr_place(self, mock_socket):
        self.tested_places._dbu.select_other.return_value = ((1, 'inner name1', 3),
                                                   (4, 'inner name2', 6))

        mock_socket.gethostname.return_value = 'inner name2'

        self.tested_places.populate_cb_places()

        res = self.tested_places.get_curr_place()

        self.assertEqual(res, (1, (4, 'inner name2', 6)))

    @patch('controller.places.psutil', spec_set=psutil)
    def test_is_removable(self, mock_disk_partitions):
        mock_disk_partitions.disk_partitions.return_value = [
            psutil._common.sdiskpart('device1', 'mountpoint1', 'fs1', 'rw,removable'),
            psutil._common.sdiskpart('device2', 'mountpoint2', 'fs2', 'opts2')]

        res = self.tested_places.is_removable(device='device1')
        self.assertTrue(res)

        res = self.tested_places.is_removable(device='device2')
        self.assertFalse(res)

    @patch.object(Places, '_get_vol_name')
    @patch('controller.places.psutil', spec_set=psutil)
    def test__get_mount_point(self, mock_disk_partitions, mock_get_vol_name):
        mock_disk_partitions.disk_partitions.return_value = [
            psutil._common.sdiskpart('device1', 'mountpoint1', 'fs1', 'rw,removable'),
            psutil._common.sdiskpart('device2', 'mountpoint2', 'fs2', 'opts2')]

        mock_get_vol_name.return_value = 'place1'

        res = self.tested_places._get_mount_point(place_name='place1')
        self.assertEqual(res, 'mountpoint1')

        res = self.tested_places._get_mount_point(place_name='place2')
        self.assertEqual(res, '')

        # no removable disk
        mock_disk_partitions.disk_partitions.return_value = [
            psutil._common.sdiskpart('device1', 'mountpoint1', 'fs1', 'opts1'),
            psutil._common.sdiskpart('device2', 'mountpoint2', 'fs2', 'opts2')]

        res = self.tested_places._get_mount_point(place_name='place2')
        self.assertEqual(res, '')

    @patch('controller.places.ctypes', spec_set=ctypes)
    def test__get_vol_name(self, mock_ctypes):
        mock_ctypes.windll.kernel32.GetVolumeInformationW.side_effect = (1, 0)
        mock_ctypes.create_unicode_buffer().value = 'vol_name'

        res = Places._get_vol_name('any')   # GetVolumeInformationW: RC = 1
        self.assertEqual(res, 'vol_name')

        res = Places._get_vol_name('any')   # GetVolumeInformationW: RC = 0
        self.assertEqual(res, '')

    @patch.object(Places, 'is_not_registered_place')
    @patch.object(Places, 'get_place_name')
    @patch.object(Places, 'get_disk_state')
    @patch('controller.places.psutil.os.path', spec_set=psutil.os.path)
    def test_update_disk_info( self, mock_os_pass, mock_disk_state,
                               mock__get_place_name, mock_is_not_registered_place ):
        self.tested_places._places = [(0, 'a', 'a')]
        self.tested_places._curr_place = (0, (0, 'a', 'a'))

        idx = 0
        disk_label = 'disk_label'
        root = 'F:/'

        mock_os_pass._getvolumepathname.return_value = root
        mock_disk_state.side_effect = (self.tested_places.NOT_REMOVAL,
                                       self.tested_places.NOT_DEFINED,
                                       self.tested_places.NOT_DEFINED)
        mock__get_place_name.return_value = disk_label
        mock_is_not_registered_place.side_effect = (False, True)

        res = self.tested_places.update_place_name(root)
        self.assertFalse(res,
                         msg='Disk info is already in data base, updated, but should not!!!')

        res = self.tested_places.update_place_name(root)
        self.assertFalse(res,
                         msg='Disk info is already in other place, updated, but should not!!!')

        res = self.tested_places.update_place_name(root)
        self.assertTrue(res, msg='Disk info is not updated, but SHOULD !!!')
        self.tested_places._dbu.update_other.assert_called_once_with('REMOVAL_DISK_INFO',
                                                           (disk_label, idx))

    def test_get_mount_point(self):
        res = self.tested_places.get_mount_point()
        self.assertEqual(res, '', msg='Mount point must be empty')

        self.tested_places._mount_point = 'F:/'
        res = self.tested_places.get_mount_point()
        self.assertEqual(res, 'F:/', msg='Mount point must be F:/')

    def test_check_if_exist(self):
        disk_label = 'label'

        self.tested_places._dbu.select_other().fetchone.side_effect = ('label', None)
        res = self.tested_places.is_not_registered_place(disk_label)
        self.assertFalse(res, msg='Label already in DB, but return None!!!')

        res = self.tested_places.is_not_registered_place('aaa')
        self.assertTrue(res, msg='Label is not in DB, but return !!!')

    @patch.object(Places, '_get_vol_name')
    @patch.object(Places, 'is_removable')
    @patch('controller.places.socket', spec_set=socket)
    @patch('controller.places.psutil.os.path', spec_set=psutil.os.path)
    def test__get_disk_info(self, mock_psutil_path, mock_socket,
                            mock_is_removable, mock__get_vol_name):
        mock_psutil_path._getvolumepathname.side_effect = ('F:/', 'G:/')
        mock_socket.gethostname.return_value = 'computer_name'
        mock_is_removable.side_effect = (True, False)
        mock__get_vol_name.return_value = 'Disk_label'

        res = self.tested_places.get_place_name('any')      # is_removable -> True
        self.assertEqual(res, 'Disk_label', msg='Removal disk with label, but not!!!')

        res = self.tested_places.get_place_name('any_2')    # is_removable -> False
        self.assertEqual(res, 'computer_name',
                         msg='Local hard disk - identified by computer name, but not!!!')

    def test__not_in_dirs(self):
        self.tested_places._dbu.select_other().fetchone.side_effect = (None, '')

        res = self.tested_places._not_in_dirs('placeId')
        self.assertTrue(res)

        res = self.tested_places._not_in_dirs('placeId')
        self.assertFalse(res)
