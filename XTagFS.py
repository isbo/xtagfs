#!/usr/bin/env python

#   XTagFS
#   Copyright (C) 2007, Imran Patel <imran@cs.ucsb.edu>
#   This program is distributed under the terms of the GNU GPL
#   See the file COPYING.

import os, stat, errno
import time
import logging
import fuse
from Spotlight import SpotlightQuery
from TagDB import TagDB

DBG = False
VOLUME_NAME = 'XTagFS'
MOUNT_POINT = '/Volumes/XTagFS'
DBG_LOG = '/tmp/XTagFS.log'

# some spaghetti to make it usable without fuse-py being installed
for i in True, False:
    try:
        import fuse
        from fuse import Fuse
    except ImportError:
        if i:
            try:
                import _find_fuse_parts
            except ImportError:
                pass
        else:
            raise


if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

# This setting is optional, but it ensures that this class will keep
# working after a future API revision
fuse.fuse_python_api = (0, 2)

# File stat structures
class FileStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_size = 0
        self.st_uid = fuse.FuseGetContext()['uid']
        self.st_gid = fuse.FuseGetContext()['gid']
        self.st_atime = self.st_mtime = self.st_ctime = int(time.time())

class DirStat(FileStat):
    def __init__(self, size = 0):
        FileStat.__init__(self)
        self.st_mode = stat.S_IFDIR | 0755
        self.st_nlink = 2
        self.st_size = size

class LinkStat(FileStat):
    def __init__(self, size = 0):
        FileStat.__init__(self)
        self.st_mode = stat.S_IFLNK | 0777        
        self.st_nlink = 1
        self.st_size = size

class XTagFS(Fuse):
    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)

        # set-up logging
        if DBG:
            logLevel = logging.DEBUG
        else:
            logLevel = logging.ERROR
        logging.basicConfig(level=logLevel, 
                format='%(asctime)s %(levelname)s %(message)s',
                filename=DBG_LOG,
                filemode='w') 

        self.query = SpotlightQuery()
        self.tagDB = TagDB()
        items = self.query.execute()
        self.tagDB.addItems(items)

    def getattr(self, path):
        if DBG: logging.debug('getattr: %s' % path)
        if path.find(':') == -1: 
            st = DirStat()
        else:
            item = path[path.rfind('/') + 1:]
            item = item.replace(':', '/')
            st = LinkStat(len(item))
        return st

    def readdir(self, path, offset):
        if DBG: logging.debug('readdir: %s' % path)
        qTags = path.strip('/').split('/')
        logging.debug(qTags)
        if qTags[0] == "":
            qTags = None
        tags, items = self.tagDB.getTagsItems(qTags)
        logging.debug(tags)
        logging.debug(items)

        entries = ['.', '..']
        if tags:
            entries += [str(tag) for tag in tags] 
        if items:
            entries += [str(item.replace('/', ':')) for item in items]

        for r in entries:
            yield fuse.Direntry(r)
            
    def readlink(self, path):
        if DBG: logging.debug('readlink: %s' % path)
        item = path[path.rfind('/') + 1:]
        return item.replace(':', '/')


def main():
    usage='XTagFS: organize filesystem using "Finder Comment" tags' + Fuse.fusage
    try:
        os.mkdir(MOUNT_POINT)
    except:
        pass

    args = fuse.FuseArgs()
    args.mountpoint=MOUNT_POINT
    args.add('ping_diskarb')
    args.add('volname=' + VOLUME_NAME)
 
    server = XTagFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle',
                     fuse_args = args)
    print server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
