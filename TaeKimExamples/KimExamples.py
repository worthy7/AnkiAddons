# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of extra stories to "Story 1" and "Story 2"

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from anki.utils import stripHTML, isWin, isMac

from japanese.reading import mecab

import os
import re

# import the main window object (mw) from ankiqt
from aqt import mw
from aqt.utils import showInfo
import sys
import codecs

import collections
EList = collections.namedtuple('exampleList',['jap', 'eng'])


# stories file path
this_dir, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(this_dir, "TaeKimExamples.txt") 

                    
#Fields used
#in
expField = 'Expression'
#out
kimSentences = 'Kim Sentences'
kimQuestions = 'Kim Questions'
kimEnglish = 'Kim English'
checkField = kimSentences

content = ""
examplesA = []

#NUMBER OF EXAMPLES TO PULL
MAX_EXAMPLES = 3

def readExamples():
    global examplesA
    if examplesA == []:
        with open(DATA_PATH, 'r') as f:
            content = f.read().splitlines()
            #sys.stderr.write(content[0] + "\n")
        f.close() 
        for line in content:
            line = line.split('\t')
            newline = []
            for b in line:
                b = stripHTML(b.decode('utf-8'))
                newline.append(b)
            fieldhash = dict(zip(('Cloze', 'Expression', 'Meaning', 'Reading', 'Notes', 'Audio'),
                                newline))
            examplesA.append(fieldhash)
    
##########################################################################

def getExamples(term):
    term = mecab.reading(term)
    answers = []
    japA = []
    engA = []
    jap = eng = None
    for item in examplesA:
        #sys.stderr.write("Item:" + item['Expression'] + "\n")
        match = (item['Reading']).find(term)
        #sys.stderr.write("Match?:" + str(match) + "\n")
        if -1 != (item['Reading']).find(term): ###IF TERM IN IN EXPRESSION##########
            #sys.stderr.write("Found:" + item['Expression'] + "\n")
            japA.append(item['Reading'])
            engA.append(item['Meaning'])
        
    japA = japA[:MAX_EXAMPLES]
    engA = engA[:MAX_EXAMPLES]
    return EList(japA, engA)

def makeQuestions(term, sentence):
    #sys.stderr.write("Trying to mecabsearch on: " +mecab.reading(term))
    #sys.stderr.write("Trying to search on: " +term)
    #sys.stderr.write("\n" + sentence)
    sentence = re.sub(re.escape(mecab.reading(term)), "<span class=focusword>___</span>", sentence)
    return re.sub(re.escape(term), "<span class=focusword>___</span>", sentence)

def makeExamples(term, sentence):
    #sys.stderr.write("Trying to search on: " +term)
    #sys.stderr.write("\n" + sentence)
    term = mecab.reading(term)
    return re.sub(re.escape(term), "<span class=focusword>"+term+"</span>", sentence)
    
def addKimExamples(nids):
    readExamples()
        
    mw.checkpoint("Add Kim Examples")
    mw.progress.start()
    #For each seleccted card
    for nid in nids:
        note = mw.col.getNote(nid)
        if (note[expField] == ""):
            continue 
		
        doNote(note)
        note.flush()
    mw.progress.finish()
    mw.reset()
    

        
def doNote(note):
    src = expField
    srcTxt = stripHTML(note[src])
    
    
    japR, engR = getExamples(srcTxt)
    
      
    Examples = makeExamples(srcTxt, ('<br>'.join(japR)))
    Questions = makeQuestions(srcTxt, ('<br>'.join(japR)))
    English = ('<br>'.join(engR))
    if note[kimSentences] != Examples \
        or note[kimQuestions] != Questions\
        or note[kimEnglish] != English:
        note[kimSentences] = Examples
        note[kimQuestions] = Questions
        note[kimEnglish] = English
        return True
    return False
    
    
def onFocusLost(flag, note, fidx):
    readExamples()
    #check if the fields exist
    dst = src = None
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        if name == expField:
            src = expField
            srcIdx = c
        if name == checkField:
            dst = checkField
            
    #if any of the fields are missing then return
    if not src or not dst:
        return flag
    
    #expression not blank
    if note[expField] == "":
        return flag
    
    # event coming from src field?
    if fidx != None and fidx != srcIdx:
        return flag
    
    if False == doNote(note):
        return flag
    return True
        

def setupMenu(browser):
    
    browser.form.menuEdit.addSeparator()
    
    kimMenu = browser.form.menuEdit.addMenu("TaeKim Sentences")
    
    a = QAction("Add Examples", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onAddKimSentences(e))
    kimMenu.addAction(a)
        
def onAddKimSentences(browser):
    addKimExamples(browser.selectedNotes())

addHook("browser.setupMenus", setupMenu)


addHook('editFocusLost', onFocusLost)

    
    

