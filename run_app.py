# run_app.py

import sys

from PyQt5.QtWidgets import QApplication

from controller.my_controller import MyController
from view.main_window import AppWindow
from view.db_choice import DBChoice

sys._excepthook = sys.excepthook


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = my_exception_hook


def main():
    from PyQt5.QtCore import pyqtRemoveInputHook

    pyqtRemoveInputHook()

    app = QApplication(sys.argv)
    dlg = DBChoice()
    main_window = AppWindow()

    _controller = MyController()
    main_window.scan_files_signal.connect(_controller.on_scan_files)

    # when data changed on any widget
    main_window.change_data_signal.connect(_controller.on_change_data)

    # signal from open_dialog=dlg
    main_window.open_dialog.DB_connect_signal.connect(_controller.on_db_connection)

    main_window.first_open_data_base()

    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
