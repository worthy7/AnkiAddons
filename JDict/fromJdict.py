# -*- coding: utf-8 -*-


#anki/python stuff
from aqt import mw
from anki.hooks import addHook
from anki.utils import stripHTML
from PyQt4.QtCore import *
from PyQt4.QtGui import *


import japaneseDict
from japaneseexamples import japanese_examples


expField = 'Expression'
definitionField = 'Dictionary Definition'

#this field includes the reading
dictionaryForm = 'Dictionary Form'

    
#get user to select from a list
def getKeyFromList(titleText, labelText, strings):
        
    d = QInputDialog()
    d.setComboBoxItems(strings)
    d.setWindowTitle(titleText)
    d.setLabelText(labelText)
    d.setOption(QInputDialog.UseListViewForComboBoxItems)
    
    if d.exec_()==1:
        return d.textValue()
        
def getMeaning(word, isBulk):
    language = japaneseDict.initLanguage()
    
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
    if len(results) > 2 and not isBulk:
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
    
        #Check if we should do it
        #First check to see if the fields exist
        
        #If field check fails then cancel (does any field not exist and are all of them full?
        if not definitionField in note or \
            not dictionaryForm in note or \
            (note[definitionField] and  \
            note[dictionaryForm]):
        
            continue
        
        
        #do the note
        if True == doNote(note, 1):
            note.flush()
            
    #save
    mw.progress.finish()
    mw.reset()        
        
        
        
def onFocusLost(flag, note, fidx):
    
    
    #Check if we should do it
    #First check to see if the fields exist
    
    #If field check fails then cancel (does any field not exist and are all of them full?
    if not definitionField in note or \
        not dictionaryForm in note or \
        (note[definitionField] and  \
        note[dictionaryForm]):
        return flag
    
    
    #If event not coming from src field then cancel
    if fidx != note._fmap[expField][0]:
        return flag
        
    #do the note and handle the results
    
    if False == doNote(note):
        return flag
    return True
    
    
def doNote(note, isBulk=0):
    try:

        #Strip out any annoying HTML
        srcTxt = stripHTML(note[expField])
        
        #get list of results and cancel if none
        results = getMeaning(srcTxt, isBulk)
        reading = ''
        if not results:
            return False
        
        
        #Insert results
        if results[1]:
            reading = "[" + results[1] + "]"
        
        if note[definitionField] != results[2] \
        or (note[dictionaryForm] != results[0] + reading):
            
            note[definitionField] = results[2]
            note[dictionaryForm] = results[0] + reading
            
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