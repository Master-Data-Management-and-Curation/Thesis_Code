# This is the main file to run

import sys
from PyQt5.QtWidgets import QApplication

from gui import gui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = gui.Main()
    window.show()
    sys.exit(app.exec_())
