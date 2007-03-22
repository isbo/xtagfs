#!/usr/bin/python

#   XTagFS
#   Copyright (C) 2007, Imran Patel <imran@cs.ucsb.edu>
#   This program is distributed under the terms of the GNU GPL
#   See the file COPYING.

import os
import re
from sets import Set

class SpotlightQuery:
    def __init__(self, root = None, tagFmt = None):
        self.tagFmt = tagFmt
        self.root = root
        self.fcRegex = re.compile("kMDItemFinderComment\ \=\ \"(.*?)\"")

    def execute(self, queryTags = None):
        entries = {}

        # build the query string 
        fileQueryStr = "mdfind "
        if queryTags:
            for tag in queryTags:
                fileQueryStr += "and kMDItemFinderComment=='*" + tag + "*'" 
        else:                
            fileQueryStr += "kMDItemFinderComment!='(- )'"
        #print fileQueryStr

        # get ALL files with tags
        tagQueryStr = "mdls -name 'kMDItemFinderComment' '"
        for item in os.popen(fileQueryStr).xreadlines():
            item = item.strip()
            # get all tags for each file
            result = os.popen(tagQueryStr + item + "'").read()
            comments = self.fcRegex.search(result).group(1)
            if not comments:
                continue
            tags = Set(comments.split(" "))
            entries[item] = tags

        return entries

if __name__ == '__main__':
    from sys import argv

    if argv[1:]:
        tag = argv[1]
    else:
        tag = None

    query = SpotlightQuery()
    entries = query.execute()
    for i, j in entries.iteritems():
        print i,  j       
