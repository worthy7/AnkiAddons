#!/usr/bin/python
#-*- coding: utf-8 -*-
# File: japanese_examples.py
# Description: Looks for example sentences in the Tatoeba Corpus for the current card's expression.
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
import csv
from anki.utils import stripHTML, isWin, isMac
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
import sqlite3
from anki.hooks import addHook


EList = collections.namedtuple('exampleList',['qjap', 'ejap', 'eng'])

# file containing the Tatoeba corpus sentences

#cursor for database stuff
cursor = None

expField  = "Expression"
dstField = "Tatoeba Examples"

MAX = 3


this_dir, this_filename = os.path.split(__file__)
databasePath = os.path.join(this_dir, "tatoebaExamples.db")



def createExamplesDatabase():
    
    if os.path.exists(databasePath):
        return
    #os.remove(databasePath)
    conn = sqlite3.connect(databasePath)
    cursor = conn.cursor()
    
    cursor.execute('PRAGMA encoding = "UTF-8";')
    
    
    #english examples go here
    cursor.execute("""CREATE TABLE EngExamples (ID INT, sentence ntext)
               """)
    
    #japanese examples go here, using Mecab as a tokenizer
    cursor.execute("CREATE TABLE JapExamples (ID INT,  sentence ntext)")
    
    #both examples in this table
    cursor.execute("""CREATE TABLE examples (JID INT, jSentence ntext, eSentence ntext)
           """)
        
    #links table
    cursor.execute("""CREATE TABLE links
              (index1 INT  SECONDARY KEY , index2  INT  SECONDARY KEY) 
           """)
    
    #create word table
    cursor.execute("""CREATE TABLE wordLinks
          (jap_Sentence_ID INT SECONDARY KEY , 
           keyword_offset INT, 
           keyword_length INT, 
           keyword TEXT, 
           entry_id INT, 
           sense INT)""")
    
    

    #ENG - JAP LINKS
    with open('links_jpneng.csv', 'rb') as input_file:
        reader = csv.reader(input_file, delimiter="\t")
        engJap2db = [(i[0], i[1]) for i in reader]
    cursor.executemany("INSERT INTO links (index1, index2) VALUES (?, ?);", engJap2db)
    
    #BOTH SENTENCES
    #japSentence, engSentence, JapID, engID
    reg = re.compile('A:(.*)\t(.*)#ID=.*_(.*)')
    inarray = []
    with open('japanese_examples.utf', 'rb') as input_file:
        content = input_file.readlines()
    for i in content[0:len(content):2]:
        fields  = reg.match(unicode(i))
        addIn = fields.group(1, 2, 3)
        inarray.append((addIn))

    cursor.executemany("INSERT INTO examples (jSentence, eSentence, JID) VALUES (?, ?, ?);", inarray)
    
    
    #SENTENCES
    with open('sentences_jpeng_sorted.csv', 'rb') as input_file:
        reader = csv.reader(input_file, delimiter="\t")
        eng_db = []
        jap_db = []
        for i in reader:
            if i[1] == 'eng':
                eng_db.append((i[0], unicode(i[2])))
            elif i[1] == 'jpn':
                jap_db.append((i[0], unicode(i[2])))
        #to_db = [(i[0], i[1], unicode(i[2])) for i in reader]

    cursor.executemany("INSERT INTO EngExamples (ID, sentence) VALUES (?, ?);", eng_db)
    cursor.executemany("INSERT INTO JapExamples (ID, sentence) VALUES (?, ?);", jap_db)
    
    
    
    #WORD - SENTENCE LINKS

    with open('sweet.csv', 'rb') as input_file:
        reader = csv.reader(input_file, delimiter="\t")
        wordSenLinks2db = [(unicode(i[0]), unicode(i[1]), unicode(i[2]), unicode(i[3]), unicode(i[4]), unicode(i[5])) for i in reader]

    cursor.executemany("INSERT INTO wordLinks (jap_Sentence_ID, keyword_offset, keyword_length, keyword, entry_id, sense) VALUES (?, ?, ?, ?, ?, ?);", wordSenLinks2db)
        

    
    conn.commit()
    print 'Made DB'
    print [x for x in cursor.execute('select * from EngExamples LIMIT 5')]
    print [x for x in cursor.execute('select * from JapExamples LIMIT 5')]
    print [x for x in cursor.execute('select * from links LIMIT 5')]
    print [x for x in cursor.execute('select * from wordLinks LIMIT 5')]
    print [x for x in cursor.execute('select * from examples LIMIT 5')]
    conn.close()
        
def makeExamples(self, term, sentence):
    return sentence


def makeQuestions(term, sentence):
    return sentence
    

def howManyExamples(expression):
    connection = sqlite3.Connection(databasePath)
    cursor = connection.cursor()
    
    results = cursor.execute('SELECT count(*) FROM wordLinks WHERE keyword = (?)', [expression])
    
    number = results.fetchone()[0]
    connection.close()
    
    print number
    return number
        
def find_examples(expression):
    info_question = ""
    info_answer = ""
    maxitems = MAX
    examples_question = []
    examples_eng = []        
    examples_jap = []
    examples = []
        
    global cursor
    
    results = cursor.execute('''Select * from (SELECT E.jSentence,
                            E.eSentence,
                            WL.keyword_offset, 
                            WL.keyword_length,
                            WL.sense,
                            LENGTH(E.jSentence)
                            FROM examples AS E 
                            JOIN wordLinks as WL ON E.JID=WL.jap_Sentence_ID  
                            WHERE WL.keyword=(?)
                            ORDER BY LENGTH(E.jSentence) DESC) 
                            GROUP by sense
                            ''', expression)
    
    resultsList = results.fetchall()
    for i in resultsList:
        print '--------'
        print 'jsen:' + str(i[0])
        print 'esen:' + str(i[1])
        print 'offset:' + str(i[2])
        print 'len:' + str(i[3])
        print 'sense:' + str(i[4])
        print 'senLen:' + str(i[5])
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
        examples_eng.append(engA)
        
        
        #get a reading version of jap sentence for answer
        japAnswer = mecab.reading(japA)

        exampleQ = japA.replace(expression,'<span class=focusword>_____</span>')
        
        
        #for original sentence make sure to search the reading version of the term
        expression_reading = mecab.reading(expression)
        exampleJ = japAnswer.replace(expression_reading ,'<span class=focusword>'+expression_reading +'</span>')
                
                
        #add jap and question
        examples_question.append(exampleQ)
        examples_jap.append(exampleJ)
        
        



    return EList(examples_question,examples_jap,examples_eng)
    
def doNote(note):
        changed = 0
        try:
            
            #This should be the dictionary form of the word
            srcTxt = stripHTML(note[expField])
            
            #wtfdowedo
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
            
            
            if(note['Tatoeba Examples'] != Examples or
            note['Tatoeba English'] != English or
            note['Tatoeba Questions'] != Questions or 
            note['Tatoeba Shortest'] != shortestJapanese):
                note['Tatoeba Examples'] = Examples
                note['Tatoeba English'] = English
                note['Tatoeba Questions'] = Questions
                note['Tatoeba Shortest'] = shortestJapanese
                return True
            return False
        except KeyError:
            return False
                   

def add_examples_focusLost(flag, note, fidx):
    
        #connect to database
        connection = sqlite3.connect(databasePath)
        global cursor
        cursor = connection.cursor()
        
        #If event not coming from src field then cancel
        if fidx != note._fmap[expField][0]:
            return flag      
        
        
        if False == doNote(note):
            return flag
        return True
    
        cursor.close()
    
        
def bulkAdd(browser):
    nids=browser.selectedNotes()
    
    mw.checkpoint("Bulk-add Tatoeba")
    mw.progress.start()
    
    #connect to database
    connection = sqlite3.connect(databasePath)
    global cursor
    cursor = connection.cursor()
    
    #For each seleccted card
    for nid in nids:
        note = mw.col.getNote(nid)
    
        #Check if we should do it
        #First check to see if the fields exist
        
        #If field check fails then cancel (does any field not exist and are all of them full?
        ##skip, deal with it in doNote
        
        #do the note
        if True == doNote(note, 1):
            note.flush()
            
    #save
    cursor.close()
    mw.progress.finish()
    mw.reset()        
    

def setupMenu(browser):
    a = QAction("Add Tatoeba examples", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: bulkAdd(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)
    

if __name__ == '__main__':
    
    createExamplesDatabase()
    #do tests
    
    #connect to database
    connection = sqlite3.connect(databasePath)
    global cursor
    cursor = connection.cursor()
    
    ##How many
    howManyExamples(unicode('日'))
    ##
    find_examples(unicode('日'))
    
    cursor.close()
else:
    print None
    
    #addHook('editFocusLost', add_examples_focusLost)
    #make menu item
    #addHook("browser.setupMenus", setupMenu)
