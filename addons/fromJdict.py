# -*- coding: utf-8 -*-

#add definition from yomi dictionary
#file should be imported and used.

from aqt import mw
from yomi_base.lang import japanese
from anki.hooks import addHook
from HTMLParser import HTMLParser
from anki.utils import stripHTML, isWin, isMac
from japaneseexamples import japanese_examples
from PyQt4.QtCore import *
from PyQt4.QtGui import *

expField = 'Expression'

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
    
    
#get user to select from a list
def getKeyFromList(titleText, labelText, strings):
        
    d = QInputDialog()
    d.setComboBoxItems(strings)
    d.setWindowTitle(titleText)
    d.setLabelText(labelText)
    d.setOption(QInputDialog.UseListViewForComboBoxItems)
    
    if d.exec_()==1:
        return d.textValue()
        
def getMeaning(word):
    language = japanese.initLanguage()
    
    results, length = language.wordSearch(word, 100, False)
    if not results:
        return
    
    #cheeky get num of results from tanaka
    for i in range(0,len(results)):
        results[i] = results[i] +  (unicode(japanese_examples.howManyExamples(results[i][0])),)
    
    #build unique dict
    resultsByKey = dict()
    for r in results:
        resultsByKey[r[0]+' '+ r[1] +' '+ r[2]+' '+ r[3]+' '+ r[4] + ' ' +r[5] ] = r
       
    
    #(expression, unicode(), glossary, conjugations, source, count)
    if len(results) > 2:
        resultText = getKeyFromList("JDict", "Multiple results found, please select one!", [(r[0]+' '+ r[1] +' '+ r[2]+' '+ r[3]+' '+ r[4] + ' ' +r[5]) for r in results])
        if resultText == None:
            return results[0]
        return resultsByKey[resultText]
        #return getKeyFromList("JDict", "Multiple results found, please select one!", [[(r[2], r) for r in results],[( r) for r in results]])
    if results:
        return results[0]

def bulkAddJDefs(nids):
        
    mw.checkpoint("Add JDefs")
    mw.progress.start()
    
    #For each seleccted card
    for nid in nids:
        note = mw.col.getNote(nid)
        
        #If the card has blank fields...
        if (note[expField] == "" or 
        note['Dictionary Definition'] != "" or
        note['DictionaryForm'] != ""):
            continue 
		
        #do the note
        if True == doNote(note):
            note.flush()
            
    #save
    mw.progress.finish()
    mw.reset()        
        
def onFocusLost(flag, note, fidx):
    
    #Set source and dst fields
    srcFields = [expField]
    dstFields = ["Dictionary Definition"]
    src = None
    dst = None
    
    #Find the fields
    # have src and dst fields?
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        for f in srcFields:
            if name == f:
                src = f
                srcIdx = c
        for f in dstFields:
            if name == f:
                dst = f
                
    #If they don't exist then cancel
    if not src or not dst:
        return flag
        
    #If event not coming from src field then cancel
    if fidx != srcIdx:
        return flag
        
    #do the note and handle the results
    
    if False == doNote(note):
        return flag
    return True
    
    
def doNote(note):
    try:
        #If field check fails cancel
        if not "Dictionary Definition" in note or \
            not 'DictionaryForm' in note or \
            not "Dictionary Definition" in note or \
            not 'DictionaryForm' in note:
            return False
        
        
        #Strip out any annoying HTML
        srcTxt = stripHTML(note[expField])
        
    
        #get list of results and cancel if none
        results = getMeaning(srcTxt)
        reading = ''
        if not results:
            return False
        
        
        #Insert results
        if results[1]:
            reading = "[" + results[1] + "]"
        
        if note["Dictionary Definition"] != results[2] \
        or (note['DictionaryForm'] != results[0] + reading):
            
            note["Dictionary Definition"] = results[2]
            note['DictionaryForm'] = results[0] + reading
            
            #return True for a refresh
            return True
        
        #if no changed were made, return false so no refresh happens
        return False
    except KeyError:
        return False

def setupMenu(browser):
    a = QAction("Add JDefinitions", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onAddJDefs(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)
    
        
def onAddJDefs(browser):
    bulkAddJDefs(browser.selectedNotes())

addHook("browser.setupMenus", setupMenu)


addHook('editFocusLost', onFocusLost)