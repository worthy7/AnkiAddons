# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of Vocabulary - to the "Kanji Vocab" field
#

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from collections import defaultdict

import os
import re

# import the main window object (mw) from ankiqt
from aqt import mw
from aqt.utils import showInfo
import sys
import codecs

import addinfofuncts

# Vocab file path
this_dir, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(this_dir, "jlpt.tsv") 

					
#Vocab gets indexed into here
vocabIndex = defaultdict(list)
#Fields used
#in					
expField = 'Expression'
#out
vocabDstField = 'Kanji Vocab'


def readVocabfile():
	with open(DATA_PATH, 'r') as f:
		content = f.read().splitlines()
		
	for line in content:
		fieldhash = dict(zip(('exp', 'reading', 'meaning', 'grade'),
							line.split('\t')))
		#extract kanji from keyword
		kanjis = extractKanji(fieldhash['exp'].decode('utf8'))
		for kanji in kanjis:
			vocabIndex[kanji].append(fieldhash)
	


##########################################################################

def addJPVocab(nids):

	vocabIndex.clear()
	readVocabfile()
	
	
	fields = []
	
	anote=mw.col.getNote(nids[0])
	#get the fields of the first note
	for (i, f) in anote.items():
		fields.append(i)
	
	#get input/output fields from user
	src = addinfofuncts.getKeyFromList("Select field to read from", "Read relevant kanji/expression from:", fields)
	if (src is None):
		return
	
		#get input/output fields from user
	dst = addinfofuncts.getKeyFromList("Select field to write to", "Write JLPT vocabulary to:", fields)
	if (dst is None):
		return
	
	
	mw.checkpoint("Add JPVocab")
	mw.progress.start()
	#For each seleccted card
	for nid in nids:
		note = mw.col.getNote(nid)
		srcTxt = mw.col.media.strip(note[src])
		if not srcTxt.strip():
			continue
		#Add the data to the dst field
		note[dst] = lookupVocab(srcTxt)
		#if (note[dst] == ""):
		#	note[dst] = note['Story']
		note.flush()
	mw.progress.finish()
	mw.reset()
	
	
	
def extractKanji(exp):
	#first get only the kanji
	separator = ','
	#Get only the kanji
	words = re.findall(ur'[\u4e00-\u9fbf]',exp)
	return words


	
def lookupVocab(wordsTxt):
	#first get only the kanji
	separator = '<br>'
	words = extractKanji(wordsTxt)
	vocabs = []
	outstr = ""
	for w in words:
		for v in vocabIndex[w]:
			vocabs.append(v['exp'].decode('utf8') + "[" + 
					v['reading'].decode('utf8') + "] <br> " + v['meaning'])
	outstr = separator.join(vocabs)
	for k in words:
		outstr = outstr.replace(k, "_")
	return outstr
		
		

