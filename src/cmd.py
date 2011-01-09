import os
import sys

APPS = {}
BINDIR = os.path.join(sys.path[0], 'bin')

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

for cmd in ['rar', 'mogrify', 'convert', 'identify', 'ppmtobmp']:
    if os.name == 'nt':
        command = os.path.join(BINDIR, cmd)
        if os.path.isfile("%s.exe" % command):
            APPS[cmd] = command
        else:
            sys.stderr.write("Could not find '%s' executable\n" % command)
            sys.exit(1)
    else:
        command = which(cmd)
        if command:
            APPS[cmd] = command
        else:
            sys.stderr.write("Could not find '%s' executable\n" % cmd)
            sys.exit(1)
