# controller/places.py

import socket
import psutil
import ctypes
import os
from collections import namedtuple

from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import QSettings, QVariant


class Places:
    NOT_REMOVAL, NOT_DEFINED, MOUNTED, NOT_MOUNTED = (1, 2, 4, 8)

    CurrPlace = namedtuple('curr_place', 'view_idx db_row disk_state')

    def __init__(self, parent):
        self.controller = parent
        self._view = parent.get_places_view()
        self._dbu = parent.get_db_utils()
        self._places = []           # list of (PlaceId, Place, Title)
        self._curr_place = Places.CurrPlace(-1, (0, '', ''), Places.NOT_DEFINED)
        self._mount_point = ''

    def get_curr_place(self):
        return self._curr_place

    def get_mount_point(self):
        return self._mount_point

    def get_disk_state(self):
        return self._curr_place.disk_state

    def get_state(self, place_id):
        id = [place[0] for place in self._places].index(place_id)
        place = self._places[id][1]
        return self._state(place)

    def _check_disk_state(self):
        """
        Set NOT_DEFINED, NOT_REMOVAL, MOUNTED, NOT_MOUNTED state of disk
        Has side effect - saves mount point in self._mount_point
        :return: None
        """
        idx = self._view.currentIndex()
        place_info = self._places[idx][1]
        self._curr_place = self._curr_place._replace(disk_state=self._state(place_info))

    def _state(self, place_name):
        if not place_name:  # impossible to check if mounted
            self._mount_point = ''
            return self.NOT_DEFINED
        loc = socket.gethostname()
        if place_name == loc:  # always mounted
            self._mount_point = ''
            return self.NOT_REMOVAL
        self._mount_point = Places._get_mount_point(place_name)
        if self._mount_point:  # mount point exists
            return self.MOUNTED
        return self.NOT_MOUNTED

    @staticmethod
    def is_removable(device):
        """
        :param device:  Disk letter / mount point
        :return: bool
        """
        parts = psutil.disk_partitions()
        removable = next(x.opts for x in parts if x.device == device)
        return removable == 'rw,removable'

    def populate_cb_places(self):
        self._view.blockSignals(True)
        self._view.clear()
        plc = self._dbu.select_other('PLACES').fetchall()
        self._places = plc
        if self._places:
            self._view.addItems((x[2] for x in self._places))

            idx = self._restore_setting()
            self._restored_idx(idx)

        self._view.blockSignals(False)

    def _set_host_place(self):
        loc = socket.gethostname()
        try:
            idx = next(i for i in range(0, len(self._places)) if self._places[i][1] == loc)
        except StopIteration:
            idx = -1
        if idx >= 0:
            self._curr_place = Places.CurrPlace._make((idx, self._places[idx], Places.NOT_REMOVAL))
            self._view.setCurrentIndex(idx)
        else:
            self._curr_place = Places.CurrPlace._make((0, self._places[0], Places.NOT_DEFINED))

    def _restore_setting(self):
        settings = QSettings()
        cur_idx = settings.value('Place/Idx', -1)
        return cur_idx

    def _restored_idx(self, cur_idx):
        if (not cur_idx == -1) & (cur_idx < len(self._places)):
            self._curr_place = Places.CurrPlace._make((cur_idx, self._places[cur_idx], self.NOT_DEFINED))
            self._view.setCurrentIndex(self._curr_place.view_idx)
            self._check_disk_state()
        else:
            self._set_host_place()

    def about_change_place(self):
        """
        :param data: tuple (index in view, current text in view)
        :return: None
        """
        prev_id = self._curr_place.view_idx
        idx = self._view.currentIndex()
        place_title = self._view.currentText()
        if idx >= len(self._places):
            self._add_place((idx, place_title))
        else:
            self._change_place((idx, place_title))
        if prev_id != self._curr_place.view_idx:
            self.controller.on_change_data('dirTree')

    def update_place_name(self, root):
        """
        Update only if 1) info is missing (NOT_DEFINED)
        and if 2) the place is not registered yet in data base
        :param root: any path, used only "volume letter"/"mount point"
        :return: True / False
        """
        self._check_disk_state()
        if self._curr_place.disk_state == self.NOT_DEFINED:
            place_name, state = self.get_place_name(root)

            if self._is_not_registered_place(place_name):
                self._dbu.update_other('PLACE', (place_name, self._curr_place.db_row[0]))
                self._curr_place = self._curr_place._replace(db_row=(self._curr_place.db_row[0],
                                                                     place_name,
                                                                     self._curr_place.db_row[2]),
                                                             disk_state=state)
                self._places[self._curr_place.view_idx] = self._curr_place.db_row
                return True

        return False

    def get_place_name(self, root):
        """
        :param root: any path, used only volume - mount point
        :return: place_name, state
        """
        disk = psutil.os.path._getvolumepathname(root)

        if self.is_removable(disk):
            place_name, state = (self._get_vol_name(disk), self.MOUNTED)    # disk label
        else:
            place_name, state = (socket.gethostname(), self.NOT_REMOVAL)    # computer name
        return place_name, state

    def _is_not_registered_place(self, place_name):
        """
        Check if exists in DB
        :param place_name: "name of computer" or "label of USB"
        :return: bool
        """
        res = self._dbu.select_other('IS_EXIST', (place_name,)).fetchone()
        return res is None

    def get_place_by_name(self, place_name):
        return self._dbu.select_other('IS_EXIST', (place_name,)).fetchone()

    def _change_place(self, data):
        """
        Check if selected place is available
        Ask for confirmation for switch to unavailable place/storage
        Save current item in self.curr_place if confirmed or available
        :param data: (current index in combobox, text of current item - Title)
        :return: None
        """
        self._check_disk_state()
        if self._curr_place.disk_state == self.NOT_MOUNTED:
            res = self._ask_switch_to_unavailable_storage(data)
            if res == 0:                # Ok button
                self._curr_place = Places.CurrPlace(view_idx=data[0],
                                                    db_row=self._places[data[0]],
                                                    disk_state=self.NOT_MOUNTED)
                self._save_setting()
            elif res == 1:              # Remove button
                self._remove_current_place()
            else:                       # Cancel - return to prev.place
                self._view.blockSignals(True)
                self._view.setCurrentIndex(self._curr_place.view_idx)
                self._view.blockSignals(False)
        else:                           # switches to new place silently
            self._curr_place = Places.CurrPlace(view_idx=data[0],
                                                db_row=self._places[data[0]],
                                                disk_state=self.get_disk_state())
            self._save_setting()

    def _save_setting(self):
        settings = QSettings()
        settings.setValue('Place/Idx', QVariant(self._curr_place.view_idx))

    def _remove_current_place(self):
        idx = self._view.currentIndex()
        if self._not_in_dirs(self._places[idx][0]):
            self._view.blockSignals(True)
            self._view.removeItem(idx)
            self._dbu.delete_other('PLACES', (self._places[idx][0],))
            self._view.setCurrentIndex(self._curr_place.view_idx)
            self._view.blockSignals(False)

    def _not_in_dirs(self, place_id):
        """
        Check if there is reference from Dirs table to place_id
        :param place_id: PlaceId from DB
        :return: bool
        """
        res = self._dbu.select_other('PLACE_IN_DIRS', (place_id,)).fetchone()
        return res is None

    def _add_place(self, data):
        """
        :param data: (index in combobox, current text in combobox)
        :return: None
        """
        res = self._ask_rename_or_new()
        if res == 0:                # add new
            self._add_new(data)
        elif res == 1:              # rename
            self._rename_place((self._curr_place.view_idx, data[1]))
        else:                       # cancel
            self._view.blockSignals(True)
            self._view.removeItem(self._view.currentIndex())
            self._view.setCurrentIndex(self._curr_place.view_idx)
            self._view.blockSignals(False)

    def _add_new(self, data):
        """
        :param data: (index in combobox, current text in combobox)
        :return: None
        """
        jj = self._dbu.insert_other('PLACES', ('', data[1]))
        self._curr_place = Places.CurrPlace(view_idx=self._view.currentIndex(),
                                            db_row=(jj, '', data[1]),
                                            disk_state=self.NOT_DEFINED)
        self._places.append(self._curr_place.db_row)
        root = QFileDialog.getExistingDirectory(parent=self._view,
                                                caption='Select root folder')
        if root:
            self.update_place_name(root)

    def _rename_place(self, data):
        """
        :param data: (index in combobox, current text in combobox)
        :return: None
        """
        self._curr_place = self._curr_place._replace(db_row=(self._curr_place.db_row[0],
                                                             self._curr_place.db_row[1],
                                                             data[1]))
        self._places[self._curr_place.view_idx] = self._curr_place.db_row

        self._view.blockSignals(True)

        self._view.clear()

        self._view.addItems((x[2] for x in self._places))

        self._view.setCurrentIndex(self._curr_place.view_idx)
        self._view.setCurrentText(data[1])

        self._view.blockSignals(False)

        self._dbu.update_other('PLACE_TITLE', (data[1], self._curr_place.db_row[0]))

    @staticmethod
    def _ask_rename_or_new():
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.addButton('Add new', QMessageBox.ActionRole)
        box.addButton('Rename', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    @staticmethod
    def _ask_switch_to_unavailable_storage(data):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setText('The storage {} is not available'.format(data[1]))
        box.addButton('Ok', QMessageBox.AcceptRole)
        box.addButton('Remove', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    @staticmethod
    def _get_mount_point(place_name):
        """
        Get mount point for removal place
        :param place_name: "computer name" or "USB label"
        :return: mount_point
        """
        parts = psutil.disk_partitions()
        removables = (x.mountpoint for x in parts if x.opts == 'rw,removable')

        for mount_point in removables:
            if place_name == Places._get_vol_name(mount_point):
                return mount_point.split(os.sep)[0]
        return ''

    @staticmethod
    def _get_vol_name(mount_point):
        """
        Only for windows
        :param mount_point:
        :return: volume label
        """
        if os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            volume_name_buffer = ctypes.create_unicode_buffer(1024)
            if kernel32.GetVolumeInformationW(ctypes.c_wchar_p(mount_point),
                                              volume_name_buffer,
                                              ctypes.sizeof(volume_name_buffer),
                                              None, None, None, None, 0) > 0:
                return volume_name_buffer.value
            return ''
        else:
            return ''
