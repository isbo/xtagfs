#   XTagFS
#   Copyright (C) 2007, Imran Patel <imran@cs.ucsb.edu>
#   This program is distributed under the terms of the GNU GPL
#   See the file COPYING.

import sqlite3
from sets import Set
import os
import logging

DBG = False

# XXX: Re-write this module using an ORM like SQLObject/SQLAlchemy?
class TagDB:
    def __init__(self, dbPath = ':memory:'):
        # XXX: file-based DB
        try:
            con = sqlite3.connect(dbPath, check_same_thread = False)
            self.cursor = con.cursor()
        except sqlite3.Error, e:
            logging.critical("Error opening TagDB: %s" % e)
        # create DB tables
        # Tags: id <-> name
        self.cursor.execute("create table Tags(tagId integer not null primary key \
                autoincrement, tagName text not null unique)")
        # Items: id <-> name
        self.cursor.execute("create table Items(itemId integer not null primary \
                key autoincrement, itemName text not null unique)")
        # Map: itemId <-> tagId
        self.cursor.execute("create table TagItemMap(itemId integer not null, \
                tagId integer not null, primary key (itemId, tagId))")

    def addItems(self, items):
        allTags = Set()
        # add to Items table
        for item, tags in items.iteritems():
            try:
                self.cursor.execute("insert into Items(itemId, itemName) \
                        values (?, ?)", (None, item))
            except sqlite3.Error, e:
                logging.error("Error Item table insert: %s" % e)
            allTags = allTags.union(tags)

        # add to Tags table
        for tag in allTags:
            try:                
                self.cursor.execute("insert into Tags(tagId, tagName) \
                        values (?, ?)", (None, tag))
            except sqlite3.Error, e:
                logging.error("Error Tag table insert: %s" % e)

        # add to mapping table
        for item, tags in items.iteritems():
            for tag in tags:
                # XXX: re-write query?
                try:
                    self.cursor.execute("insert into TagItemMap(itemId, tagId) \
                            select itemId, tagId from items, tags where \
                            itemName = '%s' and tagName = '%s'" % (item, tag))
                except sqlite3.Error, e:
                    logging.error("Error Map table insert: %s" % e)

    def getAssociatedTags(self, tags = None, itemTable = 'Items'):
        if tags:
            sqlWhere = " WHERE t.tagName NOT IN " + repr(tuple(tags))   
        else:
            sqlWhere = ""
        sql = "SELECT t.tagName, count(*) AS count FROM %s tmp \
                INNER JOIN TagItemMap ti ON tmp.itemId = ti.itemId \
                INNER JOIN Tags t ON ti.tagId = t.tagId %s \
                GROUP BY t.tagName ORDER BY count DESC" % (itemTable, sqlWhere)
        try:
            cur = self.cursor.execute(sql)
        except sqlite3.Error, e:
            logging.error("Error finding associated tags: %s" % e)
            return None
        resTags = []
        for r in cur:
            resTags.append(r[0])
        #resTags = sorted(resTags, key=resTags.__getitem__, reverse=True)
        return resTags

    # find items tagged with "tags"
    def getItemsWithAllTags(self, tags, resTable = None):
        if not tags:
            return False
        # XXX: return results in a list
        if not resTable:
            return False
        numTags = len(tags)
        sqlCreate = "CREATE TEMP TABLE %s AS " % resTable
        sqlSelect = "SELECT ti%d.itemID as itemId, i.itemName as itemName" \
                        %  (numTags - 1) 
        sqlFrom = " FROM "
        sqlWhere = " WHERE "
        sqlJoins = ""
        for i in xrange(numTags): 
            if i == 0:
                sqlFrom += " Tags t0 "
                sqlWhere += " t0.tagName = '%s'" % tags[0]
                sqlJoins += " INNER JOIN TagItemMap ti0 \
                        ON t0.tagId = ti0.tagId "
            else:
                sqlFrom += " CROSS JOIN Tags t%d" % i
                sqlWhere += " AND t%d.tagName = '%s'" % (i, tags[i])
                sqlJoins += " INNER JOIN TagItemMap ti%d ON ti%d.itemId = \
                        ti%d.itemId AND ti%d.tagId = t%d.tagId " \
                        % (i, i - 1, i, i, i)
        sqlJoins += " INNER JOIN Items i ON ti%d.itemId = i.itemId " \
                %  (numTags - 1)
        sql = sqlCreate + sqlSelect + sqlFrom + sqlJoins + sqlWhere
        try:
            self.cursor.execute(sql)
        except sqlite3.Error, e:
            logging.error("Error finding Items with all tags: %s" % e)
            return False
        return True
    
    # get items that are tagged "only/exclusively/exactly" with "tags"
    def getItemsWithOnlyTags(self, tags, itemTable = None):
        if not tags:
            return None
        if not itemTable:
            return None
        sql = "SELECT itemname from %s EXCEPT \
                SELECT i.itemName FROM %s i \
                INNER JOIN TagItemMap ti ON i.itemId = ti.itemId \
                INNER JOIN Tags t ON ti.tagId = t.tagId WHERE \
                t.tagName NOT IN %s" % (itemTable, itemTable, repr(tuple(tags)))
        try:
            cur = self.cursor.execute(sql)
        except sqlite3.Error, e:
            logging.error("Error finding Items with exact tags: %s" % e)
            return None
        items = []
        for r in cur:
            items.append(r[0])
        return items 

    def getTagsItems(self, tags = None):
        # get tagged items
        # XXX: caching
        if tags: 
            itemTable = 'TaggedItems'
            res = self.getItemsWithAllTags(tags, itemTable) 
            if not res:
                return None
        else: 
            itemTable = 'Items'
        resItems = self.getItemsWithOnlyTags(tags, itemTable) 

        # get "associated" tags
        resTags = self.getAssociatedTags(tags, itemTable)

        # XXX: cache this table
        if tags:
            try:
                self.cursor.execute("DROP TABLE %s" % itemTable)
            except sqlite3.Error, e:
                logging.error("Error dropping result item table: %s" % e)

        return resTags, resItems

    # for debugging...
    def printAllItems(self):
        cur = self.cursor.execute("select i.itemId, i.itemName, t.tagId, \
                t.tagName from TagItemMap ti, Tags t, Items i \
                where i.itemId=ti.itemId and t.tagId=ti.tagId")
        for r in cur:
            print r

if __name__ == '__main__':
    from sys import argv 
    from spotlight import SpotlightQuery

    tagDB = TagDB()
    query = SpotlightQuery()
    entries = query.execute()
    tagDB.addItems(entries)
    tagDB.printAllItems()
    tags, items = tagDB.getTagsItems(['music', 'iTunes'])
    print tags
    print items
