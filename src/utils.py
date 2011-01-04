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
import cStringIO
import zipfile
import urllib
from subprocess import Popen, PIPE

def get_mime_type(filepath):
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
    """Return file path uri"""
    return "%s%s" % ('file://', urllib.quote(filepath, safe="%/:=&?~+!$,;'@()*"))

def uri_to_file(filepath):
    return "%s" % urllib.unquote(filepath).replace('file://', '')

def get_comics(rootpath, size=None):
    comics = []
    regex = re.compile(r'^.*\.(cbr|cbz)$', re.IGNORECASE)

    def get_file_info(fullpath):
        filename = os.path.basename(fullpath)
        basename, fileext = os.path.splitext(filename)
        head, tail = os.path.split(fullpath)
        filedir = os.path.dirname(fullpath)
        filetype = get_mime_type(fullpath)
        filesize = os.path.getsize(fullpath)
        filemtime = os.path.getmtime(fullpath)
        fileuri = get_file_uri(fullpath)
        return (filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri)

    if os.path.isfile(rootpath):
        fullpath = os.path.realpath(rootpath)
        filename = os.path.basename(fullpath)
        filesize = os.path.getsize(fullpath)
        if regex.match(filename):
            if size:
                if filesize > size * (1024*1024):
                    comics.append(get_file_info(fullpath))
            else:
                comics.append(get_file_info(fullpath))
    else:
        for dirpath, dirnames, filenames in os.walk(rootpath):
            alphanumeric_sort(filenames)
            for filename in filenames:
                if regex.match(filename):
                    fullpath = os.path.join(dirpath, filename)
                    filesize = os.path.getsize(fullpath)
                    if size:
                        if filesize > size * (1024*1024):
                            comics.append(get_file_info(fullpath))
                    else:
                        comics.append(get_file_info(fullpath))
    return comics

def guess_cover(files):
    """Returns the filename within <files> that is the most likely to be
    the cover of an archive.
    """
    alphanumeric_sort(files)
    ext_re = re.compile(r'\.(jpg|jpeg|png|gif|tif|tiff|bmp)\s*$', re.I)
    front_re = re.compile('(cover|front)', re.I)
    images = filter(ext_re.search, files)
    candidates = filter(front_re.search, images)
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
    rec = re.compile("\d+|\D+")
    filenames.sort(key=lambda s: map(_format_substring, rec.findall(s)))

def which(prog):
    """ Equivalent of unix which command """
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(prog)
    if fpath:
        if is_exe(prog):
            return prog
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            filename = os.path.join(path, prog)
            if is_exe(filename):
                return filename
    return None

class Extractor:
    """Extractor is a class for extracting different archive formats.
    This is a much simplified version of the Extractor class from Comix.
    """
    def __init__(self, src):
        """Setup the extractor with archive <src>."""
        self._src = src
        self._type = get_mime_type(src)
        self._files = []

        if self._type == 'ZIP':
            self._zfile = zipfile.ZipFile(src, 'rb')
            self._files = self._zfile.namelist()
        elif self._type == 'RAR':
            self._rar = None
            for command in ('unrar', 'rar'):
                if os.name == 'nt':
                    bindir = os.path.join(sys.path[0], 'bin')
                    cmd = os.path.join(bindir, command)
                    if os.path.isfile("%s.exe" % cmd):
                        self._rar = "%s.exe" % cmd
                else:
                    if which(command):
                        self._rar = command
            if self._rar == None:
                sys.stderr.write(
                        'Could not find the "rar" or "unrar" executable.\r\nExiting...\r\n')
                sys.exit(1)
            proc = Popen(
                    [self._rar, 'vb', src], stdout=PIPE)
            fobj = proc.stdout
            self._files = fobj.readlines()
            proc.wait()
            self._files = [name.rstrip('\n') for name in self._files]

    def get_files(self):
        """Return a list of the files in the archive."""
        return self._files

    def extract(self, chosen):
        """Extract the file <chosen> and return it as a cStringIO.StringIO
        object. The <chosen> file must be one of the files in the list
        returned by the get_files() method.
        """
        if self._type == 'ZIP':
            return cStringIO.StringIO(self._zfile.read(chosen))
        elif self._type == 'RAR':
            proc = Popen(
                    [self._rar, 'p', '-inul', '-p-', '--', self._src, chosen],
                    stdout=PIPE, stderr=PIPE)
            fobj = proc.stdout
            return cStringIO.StringIO(fobj.read())
