# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of extra stories to "Story damage"

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
DATA_PATH = os.path.join(this_dir, "kanjidamage.txt") 

#story data goes here
kanjiIndex = dict()
					


def readStories():
	with open(DATA_PATH, 'r') as f:
		content = f.read().splitlines()
		#sys.stderr.write(content[0] + "\n")
	for line in content:
		fieldhash = dict(zip(('keyword', 'num', 'useful', 'kanji', 'onr', 'kunr', 'engmeaning', 'kun2', 'eng2meaning', 'mnem', 'compound', 'write', 'tags'),
							line.split('\t')))
		kanjiIndex[fieldhash['kanji'].decode('utf8')] = fieldhash
	
##########################################################################

def addKDStories(nids):
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
	
	compoundMeaning = addinfofuncts.getKeyFromList("Select field to write to", "Write compound information to:", fields)
	if (compoundMeaning is None):
		return 
	
	Mnemonic = addinfofuncts.getKeyFromList("Select field to write to", "Write Mnemonic to:", fields)
	if (Mnemonic is None):
		return 
	
	EngMeaning = addinfofuncts.getKeyFromList("Select field to write to", "Write English meanings to:", fields)
	if (EngMeaning  is None):
		return 
	
	mw.checkpoint("Add KD Stories")
	mw.progress.start()
	#For each seleccted card
	for nid in nids:
		note = mw.col.getNote(nid)
		srcTxt = mw.col.media.strip(note[expField])
		if not srcTxt.strip():
			continue
		
		#Add the data to the dst field
		
		kanjizz = extractKanji(note[expField])
		if kanjiIndex.get(kanjizz):
			if kanjiIndex[kanjizz]['compound']:
				note[compoundMeaning] = kanjiIndex[kanjizz]['compound'].decode('utf8')
			else:
				note[compoundMeaning] = ""
				
				
			if kanjiIndex[kanjizz]['eng2meaning']:
				note[Mnemonic] = kanjiIndex[kanjizz]['eng2meaning'].decode('utf8')
			else:
				note[Mnemonic] = ""
				
				
			if kanjiIndex[kanjizz]['engmeaning']:
				note[EngMeaning] = kanjiIndex[kanjizz]['engmeaning'].decode('utf8')
			else:
				note[EngMeaning] = ""
			note.flush()
	mw.progress.finish()
	mw.reset()
	
	
	

       
def extractKanji(exp):
	#get only the kanji
	words = re.findall(ur'[\u4e00-\u9fbf]',exp)
	return words[0]

	

