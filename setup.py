#!/usr/bin/env python

from distutils.core import setup

setup(name = "comic-utils",
        version = "0.4",
        description = "Comic Utils",
        author = "Milan Nikolic",
        author_email = "gen2brain@gmail.com",
        license = "GNU GPLv3",
        url = "https://github.com/gen2brain/comic-utils",
        packages = ["comicutils", "comicutils.ui"],
        package_dir = {"comicutils": "comicutils"},
        scripts = ["comic-convert", "comic-thumbnails"],
        requires = ["Image", "PngImagePlugin"],
        platforms = ["Linux", "Windows"]
        )
