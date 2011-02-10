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

class ComicConvert(QMainWindow, Ui_MainWindow):

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.progressBar.hide()

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
                ["Filename",  "Filetype", "Filesize"])
        self.treeView.setModel(self.model)
        self.treeView.setSortingEnabled(True)
        self.treeView.show()

        self.opts = {}
        self.opts['size'] = None
        self.opts['recursive'] = False
        self.opts['outdir'] = None
        self.opts['bmp-4'] = False
        self.opts['bmp-8'] = False
        self.opts['jpeg'] = False
        self.opts['png'] = False
        self.opts['scale'] = '100%'
        self.opts['quality'] = '85'
        self.opts['level'] = None
        self.opts['nocover'] = False
        self.opts['norgb'] = False
        self.opts['exclude'] = []
        self.opts['rar'] = False
        self.opts['zip'] = False
        self.opts['suffix'] = ''

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
        self.comics = utils.get_comics(args, self.opts, self.opts['size'])
        for file in self.comics:
            filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri = file
            row = [filename, filetype, utils.filesizeformat(filesize)]
            self.model.appendRow([QStandardItem(item) for item in row])
            size_sum += filesize
        self.treeView.setColumnWidth(0, 420)
        self.comicStatus.setText("%d Comics\t\t%s" % (
            len(self.comics), utils.filesizeformat(size_sum)))

    def get_options(self):
        self.opts['outdir'] = str(self.opt_outdir.text())
        self.opts['suffix'] = str(self.opt_suffix.text())
        self.opts['nocover'] = self.opt_exclude_cover.isChecked()
        self.opts['norgb'] = self.opt_exclude_rgb.isChecked()
        self.opts['scale'] = str(self.opt_scale.text())
        self.opts['level'] = str(self.opt_level.text())
        self.opts['quality'] = str(self.opt_quality.value())

        if self.opt_exclude.isChecked():
            self.opts['exclude'] = str(self.opt_exclude_list.text()).split(",")
        image_format = self.image_comboBox.itemData(
                self.image_comboBox.currentIndex(), 2).toPyObject()
        if image_format:
            self.opts[str(image_format)] = True
        archive_format = self.archive_comboBox.itemData(
                self.archive_comboBox.currentIndex(), 2).toPyObject()
        if archive_format:
            self.opts[str(archive_format)] = True

    def on_opt_exclude_stateChanged(self, enabled):
        self.opt_exclude_list.setEnabled(enabled)
        self.opt_exclude_list.setFocus()

    def on_opt_recursive_stateChanged(self, enabled):
        self.opts['recursive'] = bool(enabled)
        self.refresh_treeview()

    def on_opt_size_valueChanged(self, value):
        self.opts['size'] = int(value)

    @pyqtSignature("")
    def on_convert_pushButton_clicked(self):
        self.get_options()
        self.convert_pushButton.setEnabled(False)
        self.cancel_pushButton.setEnabled(True)
        self.progressBar.show()
        self.thread = Worker(self)
        self.thread.start()

    @pyqtSignature("")
    def on_cancel_pushButton_clicked(self):
        self.convert_pushButton.setEnabled(True)
        self.cancel_pushButton.setEnabled(False)
        self.progressBar.hide()
        self.thread.terminate()

    @pyqtSignature("")
    def on_select_pushButton_clicked(self):
        dialog = QFileDialog()
        dialog.setNameFilter(self.trUtf8("Comic book archives (*.cbz *.cbr);;All files (*)"))
        dialog.setFileMode(QFileDialog.ExistingFile & QFileDialog.Directory)
        self.select_lineEdit.setText(dialog.getOpenFileName())
        self.refresh_treeview()

    @pyqtSignature("")
    def on_outdir_pushButton_clicked(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dir_name = dialog.getExistingDirectory()
        self.opt_outdir.setText(dir_name)

    @pyqtSignature("")
    def on_refresh_pushButton_clicked(self):
        self.refresh_treeview()

    @pyqtSignature("")
    def on_close_pushButton_clicked(self):
        self.close()

    @pyqtSignature("")
    def on_about_pushButton_clicked(self):
        QMessageBox.about(self, "About",
                """<b>Comic Convert</b>""")

class Worker(QThread):

    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.exiting = False

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        while not self.exiting:
            for x in range(1, 11):
                self.parent.progressStatus.setText("File %s of 10" % x)
                for a in range(1, 101):
                    self.sleep(1)
                    self.parent.progressBar.setValue(a)


def main():
    app = QApplication(sys.argv)
    cc = ComicConvert()
    cc.show()

    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        cc.close()

if __name__ == '__main__':
    main()
