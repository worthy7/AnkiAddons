#!/usr/bin/python
#-*- coding: utf-8 -*-
# File: japanese_examples.py
# Description: Looks for example sentences in the Tanaka Corpus for the current card's expression.
# This addon was first based on Andreas Klauer's "kanji_info" plugin, and is a modified version
# of Guillaume VIRY's example sentences plugin for Anki 1.
#
# Author: Guillaume VIRY
# License:     GPL

# --- initialize kanji database ---

from aqt import mw
import os
import codecs
import cPickle
import random
import re
from japanese.reading import mecab
import sys
import gc
from anki.utils import stripHTML, isWin, isMac
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
EList = collections.namedtuple('exampleList',['qjap', 'ejap', 'eng'])

# file containing the Tanaka corpus sentences

this_dir, this_filename = os.path.split(__file__)

file = os.path.join(this_dir, "japanese_examples.utf")
file_pickle = os.path.join(this_dir, "japanese_examples.pickle")
f = codecs.open(file, 'r', 'utf8')
content = f.readlines()
f.close()

expField  = "Expression"
dstField = "Tanaka Examples"

dictionaries = ({},{})
MAX = 3

def build_dico():
    def splitter(txt):
        txt = re.compile('\s|\[|\]|\(|\{|\)|\}').split(txt)
        for i in range(0,len(txt)):
            if txt[i] == "~":
                txt[i-2] = txt[i-2] + "~"
                txt[i-1] = txt[i-1] + "~"
                txt[i] = ""
        return [x for x in txt if x]

    for i, line in enumerate(content[1::2]):
        words = set(splitter(line)[1:-1])
        for word in words:
            # Choose the appropriate dictionary; priority (0) or normal (1)
            if word.endswith("~"):
                dictionary = dictionaries[0]
                word = word[:-1]
            else:
                dictionary = dictionaries[1]

            if word in dictionary and not word.isdigit():
                dictionary[word].append(2*i)
            elif not word.isdigit():
                dictionary[word]=[]
                dictionary[word].append(2*i)

if  (os.path.exists(file_pickle) and
    os.stat(file_pickle).st_mtime > os.stat(file).st_mtime):
    f = open(file_pickle, 'rb')
    dictionaries = cPickle.load(f)
    f.close()
else:
    build_dico()
    f = open(file_pickle, 'wb')
    cPickle.dump(dictionaries, f, cPickle.HIGHEST_PROTOCOL)
    f.close()

def makeExamples(term, sentence):
    #example = example.replace(expression,'<span class=focusword>%s</span>' %expression)
    #From kims examples
    return sentence
    #return re.sub(term, "<span class=focusword>"+term+"</span>", sentence)
    #########
    #color_example = content[j+1]
    #regexp = "(?:\(*%s\)*)(?:\([^\s]+?\))*(?:\[\d+\])*\{(.+?)\}" %expression
    #match = re.compile("%s" %regexp).search(color_example)
    #if match:
    #    expression_bis = match.group(1)
    #    example = example.replace(expression_bis,'<FONT COLOR="#ff0000">%s</FONT>' %expression_bis)
    #else:
    #    example = example.replace(expression,'<FONT COLOR="#ff0000">%s</FONT>' %expression)
    #return example

def makeQuestions(term, sentence):
    #sys.stderr.write("Trying to search on: " +term)
    #sys.stderr.write("\n" + sentence)
    return sentence
    #return re.sub(term, "___", sentence)    
    

def howManyExamples(expression):
    number = 0
    for dictionary in dictionaries:
        if expression in dictionary :
            index = dictionary[expression]
            number += len(index)
        else:
            match = re.search(u"(.*?)[／/]", expression)
            if match:
                return howManyExamples(match.group(1))
        
            match = re.search(u"(.*?)[(（](.+?)[)）]", expression)
            if match:
                if match.group(1).strip():
                    return howManyExamples("%s%s" % (match.group(1), match.group(2)))    
    return number
    
def find_examples(expression):
    info_question = ""
    info_answer = ""
    maxitems = MAX
    examples_question = []
    examples_answer = []        
    examples_jap = []
    examples = []
    for dictionary in reversed(dictionaries):
        if expression in dictionary :
            index = dictionary[expression]
            
            for j in index:
                example = content[j].split("#ID=")[0][3:]
                if dictionary == dictionaries[0]:
                    example = example + " {CHECKED}"
                examples.append((expression, example))
        
            #instead of random, select shortest examples
            #index = random.sample(index, min(len(index),maxitems))
            #first get size of each sentence, then sort, then select 2 shortest
        else:
            match = re.search(u"(.*?)[／/]", expression)
            if match:
                return find_examples(match.group(1))
        
            match = re.search(u"(.*?)[(（](.+?)[)）]", expression)
            if match:
                if match.group(1).strip():
                    return find_examples("%s%s" % (match.group(1), match.group(2)))
        
        
    
    #get lengths of all sentences into a tuple list
    exampleLengthsDuple =[(e[0], e[1], len(e[1].split('\t')[0])) for e in examples]
    #sort get top MAX shortest items
    exampleLengthsDuple.sort(key=lambda tup: tup[2])
    #return the top MAX expressions and examples
    shortestExamples = [(x[0], x[1]) for x in exampleLengthsDuple[0:maxitems]]
    
    for exampleDuple in shortestExamples:
        example= exampleDuple[1]
        expression = exampleDuple[0]
        #add original example to jap array
        japA = "%s" % example.split('\t')[0]
        engA = "%s" % example.split('\t')[1]
        #English can be added
        examples_answer.append(engA)
        
        #make a replaced 
        
        
        #color_example = content[j+1]
        #regexp = "(?:\(*%s\)*)(?:\([^\s]+?\))*(?:\[\d+\])*\{(.+?)\}" %expression
        #match = re.compile("%s" %regexp).search(color_example)
        
        #get a reading version of jap sentence for answer
        japAnswer = mecab.reading(japA)
        #if match:
        #    expression_bis = match.group(1)
        #    exampleQ = japA.replace(expression_bis,'<span class=focusword>_____</span>')
        #    #for original sentence make sure to search the reading version of the term
        #    expression_bis_reading = mecab.reading(expression_bis)
        #    exampleJ = japAnswer.replace(expression_bis_reading,'<span class=focusword>'+expression_bis_reading+'</span>')
        #else:
        #    exampleQ = japA.replace(expression,'<span class=focusword>_____</span>')
        #    #for original sentence make sure to search the reading version of the term
        #    expression_reading = mecab.reading(expression)
        #    exampleJ = japAnswer.replace(expression_reading ,'<span class=focusword>'+expression_reading +'</span>')
            
        exampleQ = japA.replace(expression,'<span class=focusword>_____</span>')
        #for original sentence make sure to search the reading version of the term
        expression_reading = mecab.reading(expression)
        exampleJ = japAnswer.replace(expression_reading ,'<span class=focusword>'+expression_reading +'</span>')
                
            
            
        #add jap and question
        examples_question.append(exampleQ)
        examples_jap.append(exampleJ)
        
        



    return EList(examples_question,examples_jap,examples_answer)

    
    
    

    
def rotate_examples():
    #get id's for all the cards in the default deck or whatever
    ids = mw.col.findCards("deck:default")
    
    #for each one, simple do a get examples on each
    for id in ids:
        card = mw.col.getCard(id)
        note = card.note()
        return add_examples("doit", note, None)
    return True
        

def add_examples_fromyomichan(factId):
        #sys.stderr.write(int(factId))
        #card = mw.col.getCard(str(factId))
        ids = mw.col.findCards('nid:{0}'.format(factId))
        for id in ids:
            card = mw.col.getCard(id)
            note = card.note()
            add_examples(None, note, None)
            note["Meaning"] = "Tisdone"
        note.flush()
        return True
        
    
    
def add_examples_focusLost(flag, note, fidx):
    #check if the fields exist
    dst = src = None
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        if name == expField:
            src = expField
            srcIdx = c
        if name == dstField:
            dst = dstField
            
    if not src or not dst:
        return flag
    # dst field already filled?
    #if note[dst]:
        #return flag
    # event coming from src field?
    if fidx != srcIdx:
        return flag
        
    #expression not blank
    if note[expField] == "":
        return flag
    
    if False == doNote(note):
        return flag
    return True

    
def bulkAdd(browser):
    nids=browser.selectedNotes()

    mw.checkpoint("Bulk-add Tanaka")
    mw.progress.start()
    
    #check fields
    note = mw.col.getNote(nids[0])
    dst = src = None
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        if name == expField:
            src = expField
            srcIdx = c
        if name == dstField:
            dst = dstField
            
    if not src or not dst:
        return False
    
    for nid in nids:        
        note = mw.col.getNote(nid)
        # dst field already filled?
        #if note[dst]:
            #continue
        
        doNote(note)    
        note.flush()
    mw.progress.finish()
    #gc.collect()
    mw.reset()
    
def doNote(note):
    try:
        #srcTxt = mw.col.media.strip(note[expField])
        #if not srcTxt.strip():
        #    return flag
            
        #start mecab translator
        srcTxt = stripHTML(note[expField])
        qjapR, ajapR, engR = find_examples(srcTxt)
        if len(qjapR) <1:
            return False
        
        Examples = '<br>'.join(ajapR)
        Questions = '<br>'.join(qjapR)
        English = '<br>'.join(engR)
        shortestJapanese = ajapR[0]
        #format shortestJapanese
        shortestJapanese = stripHTML(shortestJapanese)
        shortestJapanese = re.sub('(\[.*?\])', '', shortestJapanese)
        
        
        if(note['Tanaka Examples'] != Examples or
        note['Tanaka English'] != English or
        note['Tanaka Questions'] != Questions or 
        note['Tanaka Shortest'] != shortestJapanese):
            note['Tanaka Examples'] = Examples
            note['Tanaka English'] = English
            note['Tanaka Questions'] = Questions
            note['Tanaka Shortest'] = shortestJapanese
            return True
        return False
    except KeyError:
        return False
 
def setupMenu(browser):
    a = QAction("Add Tanaka examples", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: bulkAdd(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)

    
from anki.hooks import addHook

addHook('editFocusLost', add_examples_focusLost)


#make menu item


    
addHook("browser.setupMenus", setupMenu)
