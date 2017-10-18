import socket

from PyQt5.QtWidgets import QMessageBox


class Places:

    def __init__(self, view, dbu):
        self._view = view
        self._dbu = dbu
        self._places = []
        self._curr_place = ()
        self._mount_point = ''

    def get_curr_place(self):
        return self._curr_place

    def populate_cb_places(self):
        self._view.blockSignals(True)
        self._view.clear()
        plc = self._dbu.select_other('PLACES')
        if plc:
            self._places = list(plc)
            self._view.addItems((x[2] for x in self._places))

            loc = socket.gethostname()
            idx = next(i for i in range(0, len(self._places)) if self._places[i][1] == loc)

            self._curr_place = self._places[idx]
            self._view.setCurrentIndex(idx)

        self._view.blockSignals(False)

    def about_change_place(self, data):
        if data[0] >= len(self._places):
            self._add_place(data)
        else:
            self._change_place(data)

    def _change_place(self, data):
        """
        Check if selected place is available
        Ask for confirmation for switch to unavailable place/storage
        Save current item in self.curr_place if confirmed or available
        :param data: only first item is used, it contains current index
        :return: None
        """
        if self.is_place_available():
            self._curr_place = self._places[data[0]]
        else:
            res = self._ask_switch_to_unavailable_storage(data)
            if res == 0:                # Ok button
                self._curr_place = self._places[data[0]]
            else:                       # Cancel - return to prev.place
                self._view.blockSignals(True)
                self._view.setCurrentIndex(self._curr_place[0])
                self._view.blockSignals(False)

    def _add_place(self, data):
        res = self._ask_rename_or_new()
        if res == 0:                # add new
            self._curr_place = (data[0], data[1], data[1])
            self._places.append(self._curr_place)
            self._dbu.insert_other('PLACES', self._curr_place)
        elif res == 1:              # rename
            self._rename_place((self._curr_place[0], data[1]))
        else:                       # cancel
            self._view.blockSignals(True)
            self._view.removeItem(self._view.currentIndex())
            self._view.setCurrentIndex(self._curr_place[0])
            self._view.blockSignals(False)

    def _rename_place(self, data):
        self._view.blockSignals(True)
        self._view.removeItem(self._view.currentIndex())
        self._curr_place = (self._curr_place[0], self._curr_place[1], data[1])
        self._places[self._curr_place[0]] = self._curr_place
        self._view.setCurrentIndex(self._curr_place[0])
        self._view.setCurrentText(data[1])
        self._view.blockSignals(False)
        self._dbu.update_other('PLACES', (data[1], self._curr_place[0]))

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
        box.addButton('Ok', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    def is_place_available(self):
        """
        Has side effect - set mount point for removable device
        :return: True / False
        """
        idx = self._view.currentIndex()
        place_info = self._places[idx][1]
        loc = socket.gethostname()
        if place_info == loc:
            return True

        self._mount_point = Places._get_mount_point(place_info)
        if self._mount_point:
            return True

        return False

    @staticmethod
    def _get_mount_point(place_info):
        import psutil
        parts = psutil.disk_partitions()
        removables = (x.mountpoint for x in parts if x.opts == 'rw,removable')

        for mountpoint in removables:
            if place_info == Places._get_vol_name(mountpoint):
                print('', mountpoint)
                return mountpoint
        return ''

    @staticmethod
    def _get_vol_name(mountpoint):
        """
        Only for windows
        :param mountpoint:
        :return: volume label
        """
        import ctypes
        kernel32 = ctypes.windll.kernel32
        volume_name_buffer = ctypes.create_unicode_buffer(1024)
        file_system_name_buffer = ctypes.create_unicode_buffer(1024)
        serial_number = None
        max_component_length = None
        file_system_flags = None
        rc = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(mountpoint),
            volume_name_buffer,
            ctypes.sizeof(volume_name_buffer),
            serial_number,
            max_component_length,
            file_system_flags,
            file_system_name_buffer,
            ctypes.sizeof(file_system_name_buffer)
        )
        print('|-> _get_vol_name', volume_name_buffer.value)
        return volume_name_buffer.value

    @staticmethod
    def is_removable(device):
        return True
