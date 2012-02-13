#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Author: Milan Nikolic <gen2brain@gmail.com>
# Some functions borrowed from great Comix reader http://comix.sourceforge.net/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re
import zipfile
import tempfile
import urllib
import math
import ctypes as ct
from ctypes.util import find_library
import subprocess
from subprocess import Popen, PIPE
from stat import ST_SIZE, ST_MTIME

if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    startupinfo = None

try:
    from PyQt4.QtCore import SIGNAL
except ImportError, err:
    pass

try:
    from debug import log
    from cmd import APPS
except ImportError:
    sys.stderr.write("Can't import comicutils module\r\nExiting...\r\n")
    sys.exit(1)

class GStringData(ct.Structure):
   _fields_ = [("str", ct.c_char_p),
               ("len", ct.c_ulong),
               ("allocated_len", ct.c_ulong)]

lib_path = find_library("glib-2.0")
GStringDataPointer = ct.POINTER(GStringData)

REC_RE = re.compile("\d+|\D+")
CB_RE = re.compile(r'^.*\.(cbr|cbz)$', re.IGNORECASE)
FRONT_RE = re.compile('(cover|front)', re.IGNORECASE)
IMG_RE = re.compile(r'^.*\.(jpg|jpeg|jpe|png|gif|bmp|tif|tiff)\s*$', re.IGNORECASE)

def djb_hash(s):
    """Returns the value of DJB's hash function for the given 8-bit string."""
    h = 5381
    for c in s:
        h = (((h << 5) + h) ^ ord(c)) & 0xffffffff
    return h

def g_str_hash(key):
    """Returns glib g_string_hash"""
    dll = ct.CDLL(lib_path)
    dll.g_string_new.argtypes = [ct.c_char_p]
    dll.g_string_new.restype = GStringDataPointer
    dll.g_string_hash.argtypes = [GStringDataPointer]
    dll.g_string_hash.restype = ct.c_uint
    string = dll.g_string_new(key)
    return dll.g_string_hash(string)

def get_mime_type(filepath):
    """Returns mime type of archive file"""
    try:
        if os.path.isfile(filepath):
            if not os.access(filepath, os.R_OK):
                return None
            if zipfile.is_zipfile(filepath):
                return 'ZIP'
            fd = open(filepath, 'rb')
            magic = fd.read(4)
            fd.close()
            if magic == 'Rar!':
                return 'RAR'
    except Exception:
        sys.stderr.write('Error reading %s\n' % (filepath))
    return None

def get_file_uri(filepath):
    """Returns file path uri"""
    return "%s%s" % ('file://', urllib.quote(filepath, safe="%/:=&?~+!$,;'@()*"))

def uri_to_file(filepath):
    """Convert file uri to file path """
    return "%s" % urllib.unquote(filepath).replace('file://', '')

def get_comics(path_args, opts, size=None):
    """Returns list of comic archives for given path arguments"""
    comics = []

    def get_file_info(fullpath):
        filename = os.path.basename(fullpath)
        basename, fileext = os.path.splitext(filename)
        filedir = os.path.dirname(fullpath)
        fileuri = get_file_uri(fullpath)
        filetype = get_mime_type(fullpath)
        st = os.stat(fullpath)
        filesize = st[ST_SIZE]
        filemtime = st[ST_MTIME]
        return (filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri)

    def is_size(filesize, size):
        if size is not None:
            if filesize > size * (1024*1024):
                return True
        else:
            return True
        return False

    alphanumeric_sort(path_args)
    for path in path_args:
        path = os.path.realpath(path)

        if os.path.isfile(path):
            filepath = path
            filename = os.path.basename(filepath)
            if CB_RE.match(filename):
                filesize = os.path.getsize(filepath)
                if is_size(filesize, size):
                    comics.append(get_file_info(filepath))

        elif os.path.isdir(path):
            if opts['recursive']:
                for dirpath, dirnames, filenames in os.walk(path):
                    alphanumeric_sort(filenames)
                    for filename in filenames:
                        if CB_RE.match(filename):
                            filepath = os.path.join(dirpath, filename)
                            filesize = os.path.getsize(filepath)
                            if is_size(filesize, size):
                                comics.append(get_file_info(filepath))
            else:
                filenames = os.listdir(path)
                alphanumeric_sort(filenames)
                for filename in filenames:
                    filepath = os.path.join(path, filename)
                    if os.path.isfile(filepath) and CB_RE.match(filename):
                        filesize = os.path.getsize(filepath)
                        if is_size(filesize, size):
                            comics.append(get_file_info(filepath))

    return comics

def get_images(dirname):
    """Returns list of images within archive"""
    images = []
    try:
        for dirpath, dirnames, filenames in os.walk(dirname):
            alphanumeric_sort(filenames)
            cover = guess_cover(filenames)
            for filename in filenames:
                if IMG_RE.match(filename):
                    basename, fileext = os.path.splitext(filename)
                    fullpath = os.path.join(dirpath, filename)
                    images.append((filename, fullpath, basename, fileext, cover))
        return images
    except Exception, err:
        sys.stderr.write('Error: %s\n' % str(err))
        return None

def guess_cover(files):
    """Returns the filename within <files> that is the most likely to be
    the cover of an archive.
    """
    alphanumeric_sort(files)
    images = filter(IMG_RE.search, files)
    candidates = filter(FRONT_RE.search, images)
    candidates = [c for c in candidates if not 'back' in c.lower()]
    if candidates:
        return candidates[0]
    if images:
        return images[0]
    return None

def alphanumeric_sort(filenames):
    """Do an in-place alphanumeric sort of the strings in <filenames>,
    such that for an example "1.jpg", "2.jpg", "10.jpg" is a sorted
    ordering.
    """
    def _format_substring(s):
        if s.isdigit():
            return int(s)
        return s.lower()
    filenames.sort(key=lambda s: map(_format_substring, REC_RE.findall(s)))

def filesizeformat(bytes, precision=2):
    """Returns a humanized string for a given amount of bytes"""
    bytes = int(bytes)
    if bytes is 0:
        return '0B'
    mlog = math.floor(math.log(bytes, 1024))
    return "%.*f%s" % (
        precision,
        bytes / math.pow(1024, mlog),
        ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
        [int(mlog)]
    )

def unpack_archive(fullpath, filetype, filename):
    if filetype == 'ZIP':
        try:
            tempdir = tempfile.mkdtemp(filename)
            zip = zipfile.ZipFile(fullpath, 'r')
            zip.extractall(tempdir)
            return tempdir
        except Exception, err:
            log.Warn('Error extracting %s file %s: %s' % (
                filetype, fullpath, str(err)))
    elif filetype == 'RAR':
        try:
            tempdir = tempfile.mkdtemp(filename)
            p = Popen([APPS['rar'], 'x', fullpath, tempdir],
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    shell=False, startupinfo=startupinfo)
            out = p.communicate()
            if out[1] != '':
                log.Warn('Error extracting %s file %s: %s' % (
                    filetype, fullpath, out[1]))
            else:
                return tempdir
        except Exception, err:
            log.Warn('Error extracting %s file %s: %s' % (
                filetype, fullpath, str(err)))
    return None

def pack_archive(tempdir, filetype, filepath):
    try:
        cwd = os.getcwd()
        os.chdir(tempdir)
    except IOError:
        pass
    basename = os.path.basename(filepath)
    if filetype == 'ZIP':
        try:
            zip = zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED)
            for dirpath, dirnames, filenames in os.walk(tempdir):
                for filename in filenames:
                    relpath = os.path.relpath(os.path.join(dirpath, filename))
                    zip.write(relpath)
            zip.close()
            os.chdir(cwd)
            return True
        except Exception, err:
            log.Warn('Error packing %s file %s: %s' % (
                filetype, basename, str(err)))
    elif filetype == 'RAR':
        try:
            p = Popen([APPS['rar'], 'a', '-r', filepath, '*'],
                    stdin=PIPE, stdout=PIPE, stderr=PIPE,
                    shell=False, startupinfo=startupinfo)
            out = p.communicate()
            if out[1] != '':
                log.Warn('Error packing %s file %s: %s' % (
                    filetype, basename, out[1]))
            else:
                os.chdir(cwd)
                return True
        except Exception, err:
            log.Warn('Error packing %s file %s: %s' % (
                filetype, basename, str(err)))
    return False

def image_color(fullpath):
    p = Popen([APPS['identify'], '-format', '%[colorspace]', fullpath],
            stdin=PIPE, stdout=PIPE, stderr=PIPE,
            shell=False, startupinfo=startupinfo)
    stdout, stderr = p.communicate()
    if stderr != '':
        log.Warn('Error identifying file %s: %s\n' % (fullpath, stderr.strip()))
        return False
    return stdout.strip()

def image_scale(fullpath, opts):
    command = [APPS['mogrify'], '-quality', str(opts['quality']),
            '-scale', str(opts['scale']), fullpath]
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
            shell=False, startupinfo=startupinfo)
    out = p.communicate()
    if out[1] != '':
        log.Warn('Error converting file %s: %s' % (fullpath, out[1]))
        return False
    return True

def image_level(fullpath, opts):
    command = [APPS['mogrify'], '-level', str(opts['level']), fullpath]
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
            shell=False, startupinfo=startupinfo)
    out = p.communicate()
    if out[1] != '':
        log.Warn('Error converting file %s: %s' % (fullpath, out[1]))
        return False
    return True

def image_bmp(image, opts):
    filename, fullpath, basename, fileext, cover = image
    if opts['cover'] and filename == cover:
        depth, colors = 8, 256
    elif opts['bmp-8']:
        depth, colors = 8, 256
    elif opts['bmp-4']:
        depth, colors = 4, 16

    command = [APPS['convert'], fullpath, '+matte',
            '-depth', str(depth),
            '-colors', str(colors),
            'ppm:-']
    try:
        convert = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                shell=False, startupinfo=startupinfo)
        bmp = Popen([APPS['ppmtobmp'], '-bpp', str(depth)],
                stdin=convert.stdout, stdout=PIPE, stderr=PIPE,
                shell=False, startupinfo=startupinfo)
        stdout, stderr = bmp.communicate()
        if len(stdout) > 0:
            newpath = os.path.join(
                    os.path.dirname(fullpath), '%s.bmp' % basename)
            newfile = open(newpath, 'wb')
            newfile.write(stdout)
            newfile.close()
            if fileext.lower() != '.bmp':
                os.unlink(fullpath)
        return True
    except OSError:
        return False

def image_jpeg(image, opts):
    filename, fullpath, basename, fileext, cover = image
    newpath = os.path.join(
            os.path.dirname(fullpath), '%s.jpg' % basename)
    command = [APPS['convert'], fullpath, newpath]
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
            shell=False, startupinfo=startupinfo)
    out = p.communicate()
    if out[1] != '':
        log.Warn('Error converting file %s: %s' % (fullpath, out[1]))
        return False
    if fileext.lower() != '.jpg':
        os.unlink(fullpath)
    return True

def image_png(image, opts):
    filename, fullpath, basename, fileext, cover = image
    newpath = os.path.join(
            os.path.dirname(fullpath), '%s.png' % basename)
    command = [APPS['convert'], fullpath, newpath]
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
            shell=False, startupinfo=startupinfo)
    out = p.communicate()
    if out[1] != '':
        log.Warn('Error converting file %s: %s' % (fullpath, out[1]))
        return False
    if fileext.lower() != '.png':
        os.unlink(fullpath)
    return True

def convert_images(tempdir, opts, parent=None, row=None):
    exclude = [] if not opts['exclude'] else opts['exclude']
    images = get_images(tempdir)
    filenum = 0
    maxrecords = len(images)
    
    def progress_update(filenum):
        percent = float(filenum) / float(maxrecords) * 100
        if opts['verbose']:
            sys.stderr.write('Converting images [%d%%]\r' % int(percent))
        if parent:
            if row is not None:
                rowcount = parent.model.rowCount()
                prefix = "File %d of %d -" % (row+1, rowcount)
            else:
                prefix = ""
            parent.progressBar.emit(SIGNAL("valueChanged(int)"), percent)
            parent.emit(SIGNAL("show_message(PyQt_PyObject)"), "%s Converting images [%d%%]" % (prefix, int(percent)))

    try:
        for image in images:
            filename, fullpath, basename, fileext, cover = image

            if opts['scale'] != '100%' or opts['quality'] != '0':
                image_scale(fullpath, opts)

            if bool(opts['level']):
                if image_color(fullpath) != 'RGB':
                    image_level(fullpath, opts)

            if str(filenum) in exclude:
                progress_update(filenum)
                filenum += 1
                continue
            if opts['nocover'] and filename == cover:
                progress_update(filenum)
                filenum += 1
                continue
            if opts['norgb'] and image_color(fullpath) == 'RGB':
                progress_update(filenum)
                filenum += 1
                continue

            if opts['bmp-4'] or opts['bmp-8']:
                image_bmp(image, opts)
            elif opts['jpeg']:
                image_jpeg(image, opts)
            elif opts['png']:
                image_png(image, opts)

            progress_update(filenum)
            filenum += 1
        return True
    except Exception, err:
        log.Warn('Error converting file %s: %s' % (tempdir, str(err)))
    return False
