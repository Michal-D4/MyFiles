import sys

from PyQt5.QtWidgets import QApplication

from view.main_flow import MainFlow
from view.my_db_choice import MyDBChoice
from controller.my_controller import MyController

sys._excepthook = sys.excepthook


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


sys.excepthook = my_exception_hook


def main():
    app = QApplication(sys.argv)
    dlg = MyDBChoice()
    my_app = MainFlow(open_dialog=dlg)

    _controller = MyController(my_app)
    my_app.scan_files_signal.connect(_controller.on_scan_files)

    # when data changed on any widget
    my_app.change_data_signal.connect(_controller.on_change_data)

    # signal from open_dialog=dlg
    my_app.open_dialog.open_DB_signal.connect(_controller.on_open_db)

    my_app.first_open_data_base()

    my_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
