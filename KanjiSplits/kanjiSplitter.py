# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of Heisig Keywords - to the "Keywords" field
# Adding of Heisig Numbers - to the "Heisig Number" field
#

from anki.hooks import addHook
import re
from anki.utils import stripHTML

# import the main window object (mw) from ankiqt
from aqt import mw

from PyQt4.QtCore import *
from PyQt4.QtGui import *


joinseparator = ','

# Fields used
# in					
expField = 'Expression'
# out
removedKanjiField = 'Kanji Removed '



def addKanjiSplits_bulk(nids):
    try:
        
        mw.checkpoint("Add Kanji Splits")
        
        mw.progress.start()
        # For each seleccted card
        for nid in nids:
            note = mw.col.getNote(nid)
            
            
            # do the note and handle the results
            if False == doNote(note):
                continue
           
                        
            
            # Add the data to the dst field
            if True == doNote(note):
                note.flush()
        
    except KeyError:
        
        mw.hDialog = hDialog = QMessageBox()
        hDialog.setText("Please make sure that these fields exist: 'Kanji Removed 1' ~ 'Kanji Removed 6', and 'Kanji Removed All'")
        hDialog.exec_()

    finally:
        mw.progress.finish()
        mw.reset()
        
    
def addKanjiSplits_onFocusLost(flag, note, fidx):
            
    try:
    
        
       # If event not coming from src field then cancel
        if fidx != note._fmap[expField][0]:
            return flag
        
        # do the note and handle the results
        if False == doNote(note):
            return flag
        
        return True
    except KeyError:
        return flag
    
def doNote(note):
    
    try:
        changed = 0
        # Strip out any annoying HTML
        srcTxt = stripHTML(note[expField])
        
        # add splits of 6
        kanjis = re.findall(ur'[\u4e00-\u9fbf]', srcTxt)
        
        
        note['Kanji Removed All'] = re.sub(ur'[\u4e00-\u9fbf]', '_', srcTxt)
        
        # clear all the kanji fields
        for i in range(1, 7):
            if len(kanjis) >= i:
                if (note['Kanji Removed ' + str(i)] != re.sub(kanjis[i - 1], '_', srcTxt)):
                    note['Kanji Removed ' + str(i)] = re.sub(kanjis[i - 1], '_', srcTxt)
                    changed = 1
            else:
                if (note['Kanji Removed ' + str(i)] != ''):
                    note['Kanji Removed ' + str(i)] = ''
                    changed = 1
        
    except KeyError:
        raise    
    
    if changed == 1:
        return True
    else:
        return False
    
    
def setupMenu(browser):
    a = QAction("Add Kanji Splits", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onKanjiSplits(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)
    
    
def onKanjiSplits(browser):
    addKanjiSplits_bulk(browser.selectedNotes())
    


addHook("browser.setupMenus", setupMenu)

addHook('editFocusLost', addKanjiSplits_onFocusLost)
