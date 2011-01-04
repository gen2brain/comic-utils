Comic Utils
===========

Author: Milan Nikolic 
License: GPL-3

Introduction
============

This is a simple tool for editing [comic book archives](http://en.wikipedia.org/wiki/Comic_Book_Archive_file) .
Included are scripts that I use daily to rescale/convert images in archives, convert cbr to cbz and to create thumbnails by [freedesktop](http://www.freedesktop.org/wiki/) standards to be used in file managers.
Only cbr and cbz archives are supported.

Note: Windows users can download zip package from downloads. Package doesn't contain rar.exe, you must copy that file to comic-utils/bin/rar.exe. File can be found on http://www.rarlab.com or if you already have winrar installed you can find it in Program Files.

Using
=====

#### comic-convert

    Usage: comic-convert <options> <file or dir>

    Options:
      -h, --help                show this help message and exit
      -s <arg>, --scale=<arg>   image geometry (default 100%)
      -q <arg>, --quality=<arg> image quality (default 80, used with -s)
      -o <arg>, --outdir=<arg>  output directory (default is _converted in proccesed directory)
      -m <arg>, --size=<arg>    process only files larger then size (in MB)
      -b, --bmp-4               convert images to 4bit BMP
      -c, --cover               convert cover to 8bit instead of 4bit (used with -b)
      -B, --bmp-8               convert images to 8bit BMP
      -e <arg>, --exclude=<arg> list of exclude files (0,2,13)
      -r, --rar                 convert archive to rar
      -z, --zip                 convert archive to zip
      -v, --verbose             verbose (default)
      -Q, --quiet               quiet

Examples:

    comic-convert --scale 1200 --size 60 /mnt/media/comics/BradBarron/

This example will rescale images to 1200px for all comic archive files in directory with size larger then 60MB. You can also use percents for --scale, for example 80%.

    comic-convert --bmp-4 --cover --zip /mnt/media/comics/BradBarron/Brad_Barron_01 - Neljudi.cbr

This example will convert all images except comicbook cover to 4bit BMP image, cover will be 8bit BMP in 256 colors. Also, archive is converted to zip format so you get as a result .cbz file in _converted directory.

[BMP](http://en.wikipedia.org/wiki/BMP_file_format) format is lossless format, for black&white pages very good choice, zip and rar can compress him very well, archive size can be smaller 2-3x and will be readable by comic readers.


#### comic-thumbnails

    Usage: comic-thumbnails <options> <file or dir>

    Options:
      -h, --help                show this help message and exit
      -s <arg>, --size=<arg>    thumbnail size (default 512)
      -o <arg>, --outdir=<arg>  output directory (default is ~/thumbnails/normal)
      -q <arg>, --quality=<arg> quality filter, 0 = NEAREST (default), 1 = BILINEAR, 2 = BICUBIC, 3 = ANTIALIAS
      -f, --force               overwrite
      -t <arg>, --type=<arg>    type, 0 = freedesktop (default), 1 = normal

Examples:

    comic-thumbnails --quality=3 --force /mnt/media/comics

This example will generate thumbnails by freedesktop standards in ~/.thumbnails/normal directory for whole comics collection.
Thumbnails will be 512px but since Gnome nautilus doesn't care about large directory we put those in normal so we can have nice and large thumbnails when we zoom in. Once comic-utils are installed you can make symlink like this.

    ln -s /usr/bin/comics-thumbnails ~/.gnome2/nautilus-scripts/comics-thumbnails

And have script available on right click in nautilus. Down side to this is that after thumbnails are created you have to reload nautilus, it's not possible to do that from script.
For XFCE Thunar file manager you can create [custom action](http://thunar.xfce.org/plugins.html#thunar-uca) .

    comic-thumbnails -t 1 -o /tmp/thumbs

This example will create thumbnails with "normal" name, means archivename.png in /tmp/thumbs directory.
