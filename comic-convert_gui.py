#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import glob
import signal

from PyQt4.QtGui import *
from PyQt4.QtCore import *

try:
    from comicutils.gui.cc_ui import Ui_MainWindow
    from comicutils import utils
except ImportError:
    sys.stderr.write("Can't import comicutils module\r\nExiting...\r\n")
    sys.exit(1)

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)
        self.treeView.setSortingEnabled(True)
        self.treeView.show()

        self.size = None
        self.recursive = False

        self.connect(self.opt_exclude,
                SIGNAL("stateChanged(int)"), self.on_opt_exclude_stateChanged)
        self.connect(self.opt_recursive,
                SIGNAL("stateChanged(int)"), self.on_opt_recursive_stateChanged)
        self.connect(self.opt_size,
                SIGNAL("valueChanged(int)"), self.on_opt_size_valueChanged)
        self.connect(self.select_lineEdit,
                SIGNAL("returnPressed()"), self.refresh_treeview)

    def refresh_treeview(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(
                ["Filename",  "Filetype", "Filesize"])
        args = glob.glob(str(self.select_lineEdit.text()))
        size_sum = 0
        comics = utils.get_comics(args, self, self.size)
        for file in comics:
            filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri = file
            row = [filename, filetype, utils.filesizeformat(filesize)]
            self.model.appendRow([QStandardItem(item) for item in row])
            size_sum += filesize
        self.treeView.setColumnWidth(0, 420)
        self.status.setText("%d Comics\t\t%s" % (
            len(comics), utils.filesizeformat(size_sum)))

    @pyqtSignature("")
    def on_select_pushButton_clicked(self):
        dialog = QFileDialog()
        dialog.setNameFilter(self.trUtf8("Comic book archives (*.cbz *.cbr);;All files (*)"))
        dialog.setFileMode(QFileDialog.ExistingFile & QFileDialog.Directory)
        self.select_lineEdit.setText(dialog.getOpenFileName())
        self.refresh_treeview()

    @pyqtSignature("")
    def on_output_pushButton_clicked(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dir_name = dialog.getExistingDirectory()
        self.output_lineEdit.setText(dir_name)

    @pyqtSignature("")
    def on_refresh_pushButton_clicked(self):
        self.refresh_treeview()

    @pyqtSignature("")
    def on_convert_pushButton_clicked(self):
        print "on_convert_pushButton_clicked"

    @pyqtSignature("")
    def on_about_pushButton_clicked(self):
        QMessageBox.about(self, "About",
                """<b>Comic Convert</b>""")

    def on_opt_exclude_stateChanged(self, enabled):
        self.opt_exclude_list.setEnabled(enabled)
        self.opt_exclude_list.setFocus()

    def on_opt_recursive_stateChanged(self, enabled):
        self.recursive = bool(enabled)
        self.refresh_treeview()

    def on_opt_size_valueChanged(self, value):
        self.size = int(value)

    def quit(self):
        self.close()

def main():
    app = QApplication(sys.argv)
    cc = MainWindow()
    cc.show()

    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        cc.quit()

if __name__ == '__main__':
    main()
