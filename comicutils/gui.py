#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import time
import shutil

try:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
except ImportError, err:
    sys.stderr.write("Error: %s%s" % (str(err), os.linesep))
    sys.exit(1)

try:
    from comicutils.ui.cc_ui import Ui_MainWindow
    from comicutils import utils
except ImportError, err:
    sys.stderr.write("Error: %s%s" % (str(err), os.linesep))
    sys.exit(1)

class ComicConvert(QMainWindow, Ui_MainWindow):

    toggle_current = pyqtSignal()
    show_message = pyqtSignal(str)
    show_progress = pyqtSignal(bool)
    item_status = pyqtSignal()

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setFixedSize(self.sizeHint())
        self.setWindowFlags((self.windowFlags() | Qt.CustomizeWindowHint) & ~Qt.WindowMaximizeButtonHint)
        self.progressBar.hide()

        self.set_opts()
        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)
        self.treeView.setSortingEnabled(True)
        self.set_columns()
        self.treeView.show()
        self.connect_signals()
        self.thread = Worker(self)

    def connect_signals(self):
        self.connect(self.opt_exclude,
                SIGNAL("stateChanged(int)"), self.on_opt_exclude_stateChanged)
        self.connect(self.opt_recursive,
                SIGNAL("stateChanged(int)"), self.on_opt_recursive_stateChanged)
        self.connect(self.opt_size,
                SIGNAL("valueChanged(int)"), self.on_opt_size_valueChanged)
        self.connect(self.select_lineEdit,
                SIGNAL("returnPressed()"), self.refresh_treeview)
        self.connect(self.progressBar,
                SIGNAL("valueChanged(int)"), self.on_progress_bar_changed)
        self.connect(self,
                SIGNAL("toggle_current(PyQt_PyObject)"), self.on_toggle_current)
        self.connect(self,
                SIGNAL("show_message(PyQt_PyObject)"), self.on_show_message)
        self.connect(self,
                SIGNAL("show_progress(PyQt_PyObject)"), self.on_show_progress)
        self.connect(self.treeView,
                SIGNAL("doubleClicked(QModelIndex)"), self.on_double_click)
        self.connect(self,
                SIGNAL("item_status(PyQt_PyObject, PyQt_PyObject)"), self.on_item_status)

    def set_opts(self):
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
        self.opts['cover'] = False
        self.opts['nocover'] = False
        self.opts['norgb'] = False
        self.opts['exclude'] = []
        self.opts['rar'] = False
        self.opts['zip'] = False
        self.opts['suffix'] = ''
        self.opts['verbose'] = False

    def set_columns(self):
        self.model.setHorizontalHeaderLabels(
                ["Filename",  "Filetype", "Filesize", "Status"])
        self.treeView.setColumnWidth(0, 460)
        self.treeView.setColumnWidth(1, 100)
        self.treeView.setColumnWidth(2, 100)
        self.treeView.setColumnWidth(3, 100)

    def refresh_treeview(self):
        self.model.clear()
        args = glob.glob(str(self.select_lineEdit.text()))
        self.comics = utils.get_comics(args, self.opts, self.opts['size'])
        for comic in self.comics:
            filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri = comic
            row = [filename, filetype, utils.filesizeformat(filesize)]
            items = []
            sitems = [QStandardItem(item) for item in row]
            for item in sitems:
                item.setData(comic)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                items.append(item)
            self.model.appendRow(items)
        self.set_columns()
        self.refresh_status()

    def refresh_status(self):
        sizesum = 0
        rowcount = self.model.rowCount()
        for row in range(rowcount):
            index = self.model.index(row, 0)
            item = self.model.itemFromIndex(index)
            comic = item.data().toPyObject()
            filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri = comic
            sizesum += filesize
        self.comicStatus.setText("comics: %d\t|\tsize: %s" % (
            rowcount, utils.filesizeformat(sizesum)))

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

    def set_enabled(self, enabled=True):
        self.convert_pushButton.setEnabled(enabled)
        self.cancel_pushButton.setEnabled(not enabled)
        self.select_pushButton.setEnabled(enabled)
        self.refresh_pushButton.setEnabled(enabled)
        self.outdir_pushButton.setEnabled(enabled)
        self.opt_recursive.setEnabled(enabled)
        self.opt_size.setEnabled(enabled)

    def on_toggle_current(self, index):
        self.treeView.selectionModel().setCurrentIndex(
                index, QItemSelectionModel.ToggleCurrent)

    def on_show_message(self, message=None):
        if not message:
            self.statusBar.clearMessage()
        else:
            self.statusBar.showMessage(message)

    def on_show_progress(self, progress=True):
        if progress:
            self.progressBar.show()
        else:
            self.progressBar.hide()

    def on_double_click(self, index):
        if self.thread.isRunning(): return
        item = self.model.itemFromIndex(index)
        self.model.removeRow(item.row())
        self.refresh_status()

    def on_item_status(self, item, status):
        self.model.setItem(item.row(), 3, QStandardItem(status))

    def on_opt_exclude_stateChanged(self, enabled):
        self.opt_exclude_list.setEnabled(enabled)
        self.opt_exclude_list.setFocus()

    def on_opt_recursive_stateChanged(self, enabled):
        self.opts['recursive'] = bool(enabled)
        self.refresh_treeview()

    def on_opt_size_valueChanged(self, value):
        self.opts['size'] = int(value)
        self.refresh_treeview()

    @pyqtSignature("")
    def on_convert_pushButton_clicked(self):
        self.get_options()
        self.set_enabled(False)
        self.thread.start()

    @pyqtSignature("")
    def on_cancel_pushButton_clicked(self):
        self.set_enabled(True)
        self.thread.stop()

    @pyqtSignature("")
    def on_select_pushButton_clicked(self):
        dialog = QFileDialog()
        ext_filter = "Comic book archives (*.cbz *.cbr);;All files (*)"
        dialog.setNameFilter(ext_filter)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        self.select_lineEdit.setText(dialog.getOpenFileName(filter=ext_filter))
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
        about = """
<p align="center">Comic Convert 0.5<br>
<a href="https://github.com/gen2brain/comic-utils">
<span style="text-decoration:underline;color:#0057ae;">https://github.com/gen2brain/comic-utils</span></a></p>

<p align="center">Author:<br>
Milan Nikolic (gen2brain@gmail.com)</p>

<p align="center">This program is released under the terms of the<br>
<a href="http://www.gnu.org/licenses/gpl-3.0.txt">
<span style="text-decoration:underline;color:#0057ae;">GNU General Public License version 3.</span></a></p>
<p align="center">Powered by:<br>
<a href="http://www.stripzona.com">
<span style="text-decoration:underline;color:#0057ae;">http://www.stripzona.com</span></a></p>"""
        QMessageBox.about(self, "About", about)

    @pyqtSignature("")
    def on_progress_bar_changed(self, value):
        self.progressBar.setValue(value)

class Worker(QThread):

    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.opts = parent.opts
        self.tmpdir = None
        self.exiting = False
        self.item = None

    def __del__(self):
        self.exiting = True
        self.wait()

    def stop(self):
        self.exiting = True
        self.show_progress(False)
        self.show_message(None)
        if self.item:
            self.item_status(self.item, "")
        if self.tmpdir:
            shutil.rmtree(self.tmpdir)
        self.terminate()

    def item_status(self, item, status):
        self.parent.emit(SIGNAL("item_status(PyQt_PyObject, PyQt_PyObject)"), item, status)

    def show_progress(self, progress):
        self.parent.emit(SIGNAL("show_progress(PyQt_PyObject)"), progress)

    def show_message(self, message, row=None):
        if row is not None:
            rowcount = self.parent.model.rowCount()
            message = "File %d of %d - %s" % (row+1, rowcount, message)
        self.parent.emit(SIGNAL("show_message(PyQt_PyObject)"), message)

    def run(self):
        self.exiting = False
        rowcount = self.parent.model.rowCount()

        while not self.exiting:
            for row in range(rowcount):
                index = self.parent.model.index(row, 0)
                item = self.parent.model.itemFromIndex(index)
                self.item = item
                self.parent.emit(SIGNAL("toggle_current(PyQt_PyObject)"), index)
                comic = item.data().toPyObject()
                filename,basename,fileext,filedir,fullpath,filetype,filesize,filemtime,fileuri = comic

                self.item_status(item, "CONVERTING...")

                if self.opts['outdir']:
                    convdir = os.path.realpath(self.opts['outdir'])
                else:
                    convdir = os.path.join(filedir, '_converted')

                if os.path.isfile(os.path.join(convdir, filename)):
                    self.show_message('Skipping, file exists in %s' % convdir, row)
                    self.item_status(item, "SKIPPED")
                    time.sleep(1)
                    continue

                self.show_message('Unpacking file %s (%sMB)...' % (
                    filename, filesize/(1024*1024)), row)
                self.item_status(item, "UNPACKING...")
                tempdir = utils.unpack_archive(fullpath, filetype, filename)
                if tempdir is not None:
                    self.tmpdir = tempdir
                    self.show_message('File %s unpacked' % filename, row)
                    self.item_status(item, "CONVERTING...")
                    self.parent.emit(SIGNAL("show_progress(PyQt_PyObject)"), True)

                    if utils.convert_images(tempdir, self.opts, self.parent, row):
                        self.parent.progressBar.emit(SIGNAL("valueChanged(int)"), 0)
                        self.parent.emit(SIGNAL("show_progress(PyQt_PyObject)"), False)
                        self.show_message('File %s converted' % filename, row)

                        if not self.opts['outdir'] and not os.path.isdir(convdir):
                            os.mkdir(convdir)

                        if self.opts['suffix']:
                            basename = basename + self.opts['suffix']
                            filename = basename + fileext

                        if self.opts['rar']:
                            filetype = 'RAR'
                            filename = '%s.cbr' % basename
                        elif self.opts['zip']:
                            filetype = 'ZIP'
                            filename = '%s.cbz' % basename

                        self.show_message('Packing %s...' % filename, row)
                        self.item_status(item, "PACKING...")
                        filepath = os.path.join(convdir, filename)
                        if utils.pack_archive(tempdir, filetype, filepath):
                            self.show_message('File %s packed.' % filepath, row)
                            shutil.rmtree(tempdir)

                        self.item_status(item, "OK")
                        self.tmpdir = None

            time.sleep(1)
            self.show_message(None)
            self.parent.set_enabled(True)
            self.exiting = True
