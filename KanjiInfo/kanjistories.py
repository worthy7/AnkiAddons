# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of extra stories to "Story 1" and "Story 2"

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook

import os
import re

# import the main window object (mw) from ankiqt
from aqt import mw
from aqt.utils import showInfo
import sys
import codecs
import addinfofuncts


# stories file path
this_dir, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(this_dir, "stories.txt") 

#story data goes here
kanjiIndex = dict()
                    
#Fields used
#out
story1DstField = 'Story 1'
story2DstField = 'Story 2'


def readStories():
    with open(DATA_PATH, 'r') as f:
        content = f.read().splitlines()
        #sys.stderr.write(content[0] + "\n")
    for line in content:
        fieldhash = dict(zip(('kanji', 'keyword', 'story1', 'stroke', 'heisig', 'lesson', 'on', 'story2'),
                            line.split('\t')))
        kanjiIndex[fieldhash['kanji'].decode('utf8')] = fieldhash
    
##########################################################################

def addExtraStories(nids):
    readStories()
    
    
    fields = []
    
    anote=mw.col.getNote(nids[0])
    #get the fields of the first note
    for (i, f) in anote.items():
        fields.append(i)
    
    #get input/output fields from user
    expField = addinfofuncts.getKeyFromList("Select field to read from", "Read relevant kanji/expression from:", fields)
    if (expField is None):
        return
    
    #get input/output fields from user
    story1DstField = addinfofuncts.getKeyFromList("Select field to write to", "Write extra story to:", fields)
    if (story1DstField is None):
        return
    
        #get input/output fields from user
    story2DstField = addinfofuncts.getKeyFromList("Select field to write to", "Write other extra story to:", fields)
    if (story2DstField is None):
        return
    
    mw.checkpoint("Add Extra Stories")
    mw.progress.start()
    #For each seleccted card
    for nid in nids:
        note = mw.col.getNote(nid)
        src = expField
        srcTxt = mw.col.media.strip(note[src])
        if not srcTxt.strip():
            continue
        #Add the data to the dst field
        
        kanjizz = extractKanji(note[src])
        if kanjizz not in kanjiIndex:
            continue
        if kanjiIndex[kanjizz]:
            if kanjiIndex[kanjizz]['story1']:
                note[story1DstField] = kanjiIndex[kanjizz]['story1'].decode('utf8')
            else:
                note[story1DstField] = ""
            if kanjiIndex[kanjizz]['story2']:
                note[story2DstField] = kanjiIndex[kanjizz]['story2'].decode('utf8')
            else:
                note[story2DstField] = ""
        note.flush()
    mw.progress.finish()
    mw.reset()
    
    
def extractKanji(exp):
    #get only the kanji
    words = re.findall(ur'[\u4e00-\u9fbf]',exp)
    return words[0]

    

