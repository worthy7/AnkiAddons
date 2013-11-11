# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of Vocabulary - to the "Kanji Vocab" field from cards in anki
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




# Kanji variables are set here
# Kanji Deck location, wrap it in triples
kanjiDeckSearchTerm = "deck:'Everything::0 Kanji'"
# Kanji fields:
kanjiCardVocabField = 'My Anki Vocab'
kanjiCardKanjiField = 'Expression'


# Vocab variables are set here and selected from the browser if using the menu
# Vocab fields to read from:
vocabDeckSearchTerm = "mid:1372805886784" 
vocabCardJapanese = 'Dictionary Form'
vocabCardEnglish = 'Dictionary Definition'
# These fields will also be used to update the kanji cards as new vocab is added

# Field to call event on lost focus
expField = 'Dictionary Form'
			
# Vocab gets indexed into here
vocabIndex = defaultdict(list)
kanjiCardsIndex = dict()

# Initialize all the kanji cards into a hash.
def indexKanji():
	# get cards
	nids = mw.col.findCards(kanjiDeckSearchTerm)
	# for each card NID
	for n in nids:
		# array[kanji] = nid
		note = mw.col.getCard(n).note()
		# put the IDS into an array, perhaps can do the cards directly?
		kanjiCardsIndex[extractKanji(note[kanjiCardKanjiField])[0]] = n
	print len(kanjiCardsIndex)
	return



# nid will be the vocab from the browser or the one selected card
def addKanjiWordsVocab_bulk(nid):
	mw.checkpoint("Add vocab to kanji cards")
	try:
		mw.progress.start()
		# For each seleccted card
		
		
		# now for each kanji card
		for id in kanjiCardsIndex:
			# look up card from the kanji hash array
			
			# get the kanji note
			kanjiNote = mw.col.getCard(kanjiCardsIndex[id]).note()
			
			# do the note and handle the results
			if False == doNote(kanjiNote):
				return flag
		
		return True
	
	except KeyError, e:
		
		mw.hDialog = hDialog = QMessageBox()
		hDialog.setText("Please make sure that these fields exist" + e)
		hDialog.exec_()

	finally:
		mw.progress.finish()
		mw.reset()
		return False
	
# This will happen on every 'add card'
def addKanjiWordsVocab_onFocusLost(flag, note, fidx):
			 
	try:
	
	   # If event not coming from src field then cancel
		if fidx != note._fmap[expField][0]:
			return flag
		
		if vocabCardEnglish not in note or vocabCardJapanese not in note:
			return flag
		
		
		# extract kanji from the vocabCardJapanese field
		kanjiz = extractKanji(note[vocabCardJapanese])
		
		# for each kanji in the word
		for k in kanjiz:
			# look up card from the kanji hash array
			# if it doesn't exist then continue with next kanjiz
			if k not in kanjiCardsIndex:
				continue
			# get the kanji note
			kanjiNote = mw.col.getCard(kanjiCardsIndex[k]).note()
			
			# do the note and handle the results
			if False == doNote(kanjiNote):
				return flag
		
		return True
	except None, e:
		raise e
		return flag
	
	
def doNote(note):
	# this is a kanji note
	separator = '<br>'
	try:
		# extract the 1 kanji
		theKanji = extractKanji(note[kanjiCardKanjiField])[0]
		
		# get vocab cards using this kanji
		searchTerm = vocabDeckSearchTerm + " '" + vocabCardJapanese + ':' + """*""" + theKanji + """*'""" 
		nids = mw.col.findNotes(searchTerm)
			
		vocabs = []
		for nid in nids :
			# create string using the japanese and english vocabCardJapanese vocabCardEnglish
			vocabNote = mw.col.getNote(nid)
			vocabs.append(vocabNote[vocabCardJapanese] + " <br> " + vocabNote[vocabCardEnglish])
			
		outstr = separator.join(vocabs)
		outstr = outstr.replace(theKanji, "_")
		
		
		# append string to the kanjiCardVocabField field
		note[kanjiCardVocabField] = outstr
		# flush the kanji note
		note.flush()
		return True
	except None, e:
		raise e
		return False

##########################################################################


def extractKanji(exp):
	# Get only the kanji
	words = re.findall(ur'[\u4e00-\u9fbf]', exp)
	return words


##########################################################################

	
def lookupVocab(wordsTxt):
	# first get only the kanji
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
		
		
addHook('profileLoaded', indexKanji)
# Maybe change this to 'add card'
addHook('editFocusLost', addKanjiWordsVocab_onFocusLost)
