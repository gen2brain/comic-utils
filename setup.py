#!/usr/bin/env python

import os
import sys
import glob
from distutils.core import setup

setup(name = "comic-utils",
        version = "0.1",
        description = "Comic Utils",
        author = "Milan Nikolic",
        author_email = "gen2brain@gmail.com",
        license = "GNU GPLv3",
        url = "http://code.google.com/p/comic-utils/",
        download_url = "http://volti.googlecode.com/files/%s-%s.tar.gz " % ("comic-utils", "0.1"),
        packages = ["comicutils"],
        package_dir = {"comicutils": "src"},
        scripts = ["comic-convert", "comic-thumbnails"],
        requires = ["Image", "PngImagePlugin"],
        platforms = ["Linux", "Windows"]
        )
