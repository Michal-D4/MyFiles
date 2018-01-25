# run_app.py

import sys

from PyQt5.QtWidgets import QApplication

from controller.my_controller import MyController
from view.main_flow import MainFlow
from view.my_db_choice import MyDBChoice


def main():
    app = QApplication(sys.argv)
    dlg = MyDBChoice()
    main_window = MainFlow(open_dialog=dlg)

    _controller = MyController(main_window)
    main_window.scan_files_signal.connect(_controller.on_scan_files)

    # when data changed on any widget
    main_window.change_data_signal.connect(_controller.on_change_data)

    # signal from open_dialog=dlg
    main_window.open_dialog.open_DB_signal.connect(_controller.on_open_db)

    main_window.first_open_data_base()

    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
