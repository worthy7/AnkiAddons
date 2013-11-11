# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of extra stories to "Story 1" and "Story 2"


from PyQt4.QtGui import *
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

import addKanjiWordsVocab

def getKeyFromList(titleText, labelText, strings):
        
    d = QInputDialog()
    d.setComboBoxItems(strings)
    d.setWindowTitle(titleText)
    d.setLabelText(labelText)
    d.setOption(QInputDialog.UseListViewForComboBoxItems)
       
    
    if d.exec_()==1:
        return d.textValue()
    
def setupMenu(browser):
    
    browser.form.menuEdit.addSeparator()
    
    a = QAction("Add this Vocab to Kanji Cards", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onAddKanjiVocab(e))
    browser.form.menuEdit.addAction(a)
        
def onAddKanjiVocab(browser):
    addKanjiWordsVocab.addKanjiWordsVocab_bulk(browser.selectedNotes())
    
addHook("browser.setupMenus", setupMenu)



    
       