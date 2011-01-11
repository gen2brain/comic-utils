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
import urllib

REC_RE = re.compile("\d+|\D+")
CB_RE = re.compile(r'^.*\.(cbr|cbz)$', re.IGNORECASE)
FRONT_RE = re.compile('(cover|front)', re.IGNORECASE)
IMG_RE = re.compile(r'^.*\.(jpg|jpeg|jpe|png|gif|bmp|tif|tiff)\s*$', re.IGNORECASE)

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
    """Returns file path uri"""
    return "%s%s" % ('file://', urllib.quote(filepath, safe="%/:=&?~+!$,;'@()*"))

def uri_to_file(filepath):
    """File uri to file path """
    return "%s" % urllib.unquote(filepath).replace('file://', '')

def get_comics(path_args, opts, size=None):
    comics = []

    def get_file_info(fullpath):
        filename = os.path.basename(fullpath)
        basename, fileext = os.path.splitext(filename)
        filedir = os.path.dirname(fullpath)
        filetype = get_mime_type(fullpath)
        filesize = os.path.getsize(fullpath)
        filemtime = os.path.getmtime(fullpath)
        fileuri = get_file_uri(fullpath)
        return (filename, basename, fileext, filedir, fullpath, filetype, filesize, filemtime, fileuri)

    alphanumeric_sort(path_args)
    for path in path_args:
        path = os.path.realpath(path)

        if os.path.isfile(path):
            fullpath = os.path.realpath(path)
            filename = os.path.basename(fullpath)
            filesize = os.path.getsize(fullpath)
            if CB_RE.match(filename):
                if size is None:
                    comics.append(get_file_info(fullpath))
                else:
                    if filesize > size * (1024*1024):
                        comics.append(get_file_info(fullpath))

        elif os.path.isdir(path):
            if opts.recursive:
                for dirpath, dirnames, filenames in os.walk(path):
                    alphanumeric_sort(filenames)
                    for filename in filenames:
                        if CB_RE.match(filename):
                            fullpath = os.path.join(dirpath, filename)
                            filesize = os.path.getsize(fullpath)
                            if size is None:
                                comics.append(get_file_info(fullpath))
                            else:
                                if filesize > size * (1024*1024):
                                    comics.append(get_file_info(fullpath))
            else:
                filenames = os.listdir(path)
                alphanumeric_sort(filenames)
                for filename in filenames:
                    fullpath = os.path.join(path, filename)
                    if os.path.isfile(fullpath) and CB_RE.match(filename):
                        filesize = os.path.getsize(fullpath)
                        if size is None:
                            comics.append(get_file_info(fullpath))
                        else:
                            if filesize > size * (1024*1024):
                                comics.append(get_file_info(fullpath))

    return comics

def get_images(dir):
    images = []
    try:
        for dirpath, dirnames, filenames in os.walk(dir):
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
