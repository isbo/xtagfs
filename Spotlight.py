#!/usr/bin/python

#   XTagFS
#   Copyright (C) 2007, Imran Patel <imran@cs.ucsb.edu>
#   This program is distributed under the terms of the GNU GPL
#   See the file COPYING.

import os
import re
from sets import Set

class SpotlightQuery:
    def __init__(self, rootDir=None, tagDelimiter=None):
        self.tagDelimiter = tagDelimiter
        self.rootDir = rootDir
        self.fcRegex = re.compile("kMDItemFinderComment\ \=\ \"(.*?)\"")

    def execute(self):
        entries = {}

        # build the query string 
        fileQueryStr = "mdfind \"kMDItemFinderComment == '*'\""
        if self.rootDir: 
            fileQueryStr += "  -onlyin " + self.rootDir

        tagQueryStr = "mdls -name 'kMDItemFinderComment' '"
        # get all files with tags
        for filename in os.popen(fileQueryStr).xreadlines():
            file = filename.strip()
            # get all tags for each file
            result = os.popen(tagQueryStr + file + "'").read()
            match = self.fcRegex.search(result)
            if not match:
                continue
            comments = match.group(1) 
            if not comments.strip():
                continue
            tags = Set(comments.split(self.tagDelimiter))
            entries[file] = tags

        return entries

if __name__ == '__main__':
    from sys import argv

    query = SpotlightQuery()
    entries = query.execute()
    for i, j in entries.iteritems():
        print i,  j       
