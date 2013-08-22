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
import addinfofuncts

import kanjidamageinfo
import kanjistories
import addjpvocab
import addBestKanjiWord

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
    
    kanjiExtrasMenu = browser.form.menuEdit.addMenu("Kanji Extras")
    
    a = QAction("Add KanjiDamage info", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onKDStories(e))
    kanjiExtrasMenu.addAction(a)
    
    b = QAction("Add Extra Stories", browser)
    browser.connect(b, SIGNAL("triggered()"), lambda e=browser: onExtraStories(e))
    kanjiExtrasMenu.addAction(b)

    d = QAction("Add JLPT Vocab", browser)
    browser.connect(d, SIGNAL("triggered()"), lambda e=browser: onJPVocab(e))
    kanjiExtrasMenu.addAction(d)
    
    f = QAction("Add Common Vocab", browser)
    browser.connect(f, SIGNAL("triggered()"), lambda e=browser: onCommonVocab(e))
    kanjiExtrasMenu.addAction(f)
        
def onKDStories(browser):
    kanjidamageinfo.addKDStories(browser.selectedNotes())


def onExtraStories(browser):
    kanjistories.addExtraStories(browser.selectedNotes())

def onJPVocab(browser):
    addjpvocab.addJPVocab(browser.selectedNotes())
    
def onCommonVocab(browser):
    addBestKanjiWord.addCommonVocab(browser.selectedNotes())
    
addHook("browser.setupMenus", setupMenu)



    
       