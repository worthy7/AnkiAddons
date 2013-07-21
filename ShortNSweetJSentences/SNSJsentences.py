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
import re
from japanese.reading import mecab
import csv
from anki.utils import stripHTML
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
import sqlite3
from anki.hooks import addHook
import time


EList = collections.namedtuple('exampleList',['qjap', 'ejap', 'eng'])

# file containing the Tatoeba corpus sentences

#cursor for database stuff
#cursor = None

expField  = "Dictionary Form"
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
#     cursor.execute("""CREATE TABLE EngExamples (ID INT, sentence ntext)
#                """)
    
    #japanese examples go here, using Mecab as a tokenizer
#     cursor.execute("CREATE TABLE JapExamples (ID INT,  sentence ntext)")
    
    #both examples in this table
    cursor.execute("""CREATE TABLE examples (JID INT PRIMARY KEY, jSentence ntext, eSentence ntext)
           """)
        
    #links table
#     cursor.execute("""CREATE TABLE links
#               (index1 INT  SECONDARY KEY , index2  INT  SECONDARY KEY) 
#            """)
    
    #create word table
    cursor.execute("""CREATE TABLE wordLinks
          (jap_Sentence_ID INT , 
           keyword_offset INT, 
           keyword_length INT, 
           keyword TEXT, 
           entry_id INT, 
           sense INT)""")
    
    

    #ENG - JAP LINKS
#     with open('links_jpneng.csv', 'rb') as input_file:
#         reader = csv.reader(input_file, delimiter="\t")
#         engJap2db = [(i[0], i[1]) for i in reader]
#     cursor.executemany("INSERT INTO links (index1, index2) VALUES (?, ?);", engJap2db)
    
    #BOTH SENTENCES
    #japSentence, engSentence, JapID, engID
    reg = re.compile('A:(.*)\t(.*)#ID=.*_(.*)')
    inarray = []
    with open('japanese_examples.utf', 'rb') as input_file:
        content = input_file.readlines()
    for i in content[0:len(content):2]:
        fields  = reg.match(unicode(i))
        addIn = fields.group(1, 2, 3)
#         if addIn[2] in inarray and addIn[0] != inarray[addIn[2]][0]:
#             print addIn[0]
#             print addIn[1]
#             print inarray[addIn[2]][0]
#             print inarray[addIn[2]][1]
        inarray.append(addIn)
        #inarray.append((addIn))
        
        
    cursor.executemany("INSERT OR IGNORE INTO examples (jSentence, eSentence, JID) VALUES (?, ?, ?);", inarray)
    
    
    #SENTENCES
#     with open('sentences_jpeng_sorted.csv', 'rb') as input_file:
#         reader = csv.reader(input_file, delimiter="\t")
#         eng_db = []
#         jap_db = []
#         for i in reader:
#             if i[1] == 'eng':
#                 eng_db.append((i[0], unicode(i[2])))
#             elif i[1] == 'jpn':
#                 jap_db.append((i[0], unicode(i[2])))

#     cursor.executemany("INSERT INTO EngExamples (ID, sentence) VALUES (?, ?);", eng_db)
#     cursor.executemany("INSERT INTO JapExamples (ID, sentence) VALUES (?, ?);", jap_db)
    
    
    
    #WORD - SENTENCE LINKS

    with open('sweet.csv', 'rb') as input_file:
        reader = csv.reader(input_file, delimiter="\t")
        wordSenLinks2db = [(unicode(i[0]), unicode(i[1]), unicode(i[2]), unicode(i[3]), unicode(i[4]), unicode(i[5])) for i in reader]

    cursor.executemany("INSERT INTO wordLinks (jap_Sentence_ID, keyword_offset, keyword_length, keyword, entry_id, sense) VALUES (?, ?, ?, ?, ?, ?);", wordSenLinks2db)
        

    
    conn.commit()
    print 'Made DB'
#     print [x for x in cursor.execute('select * from EngExamples LIMIT 5')]
#     print [x for x in cursor.execute('select * from JapExamples LIMIT 5')]
#     print [x for x in cursor.execute('select * from links LIMIT 5')]
    print [x for x in cursor.execute('select * from wordLinks LIMIT 5')]
    print [x for x in cursor.execute('select * from examples LIMIT 5')]
    conn.close
    

def howManyExamples(expression):
    connection = sqlite3.Connection(databasePath)
    cursor = connection.cursor()
    
    results = cursor.execute('SELECT count(*) FROM wordLinks WHERE keyword = (?)', [expression])
    
    number = results.fetchone()[0]
    connection.close()
    
    print number
    return number


def getResults(expression):
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
                            ''', [expression])
        return results
    
def find_examples(expression):
    examples_question = []
    examples_eng = []        
    examples_jap = []
        
    global cursor
    
    results = getResults(expression)
    
    resultsList = results.fetchall()
    for i in resultsList:
        print '--------'
        print 'jsen:' + unicode(i[0])
        print 'esen:' + unicode(i[1])
        print 'offset:' + unicode(i[2])
        print 'len:' + unicode(i[3])
        print 'sense:' + unicode(i[4])
        print 'senLen:' + unicode(i[5])
        
        #English can be added
        examples_eng.append(i[1])
        
        #get a reading version of jap sentence for answer
        japAnswer = mecab.reading(i[0])
        
        expressionForm = i[0][(i[2]+1):(i[2]+i[3]+1)]
        #this replaces the word we want with the underline
        exampleQ = i[0].replace(expressionForm ,'<span class=focusword>_____</span>')
        
        
        #for original sentence make sure to search the reading version of the term
        expression_reading = mecab.reading(expressionForm)
        #first try to replace using the reading version
        replacedJapAnswer = japAnswer.replace(expression_reading ,'<span class=focusword>'+expression_reading +'</span>')
        
        #if it failed to replace using reading version then just replace the normal
        if replacedJapAnswer == japAnswer:
            replacedJapAnswer = japAnswer.replace(expressionForm ,'<span class=focusword>'+expressionForm +'</span>')
        exampleJ = replacedJapAnswer        
                
        #add jap and question
        examples_question.append(exampleQ)
        examples_jap.append(exampleJ)
        
        print unicode(examples_question)
        print unicode(examples_jap)
        print unicode(examples_eng)

    return EList(examples_question,examples_jap,examples_eng)
    
def doNote(note):
        changed = 0
        try:
            
            #This should be the dictionary form of the word
            srcTxt = stripHTML(note[expField])
            #strip any readings
            srcTxt = re.sub('(\[.*\])', '', srcTxt)
            
            
            #wtfdowedo
            qjapR, ajapR, engR = find_examples(srcTxt)
            if len(qjapR) <1:
                return False
            
            Examples = '<br>'.join(ajapR)
            Questions = '<br>'.join(qjapR)
            English = '<br>'.join(engR)
            
            
            if(note['Tatoeba Examples'] != Examples or
            note['Tatoeba English'] != English or
            note['Tatoeba Questions'] != Questions):
                note['Tatoeba Examples'] = Examples
                note['Tatoeba English'] = English
                note['Tatoeba Questions'] = Questions
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
        if True == doNote(note):
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
    
    #os.remove(databasePath)
    createExamplesDatabase()
    #do tests
    
    #connect to database
    connection = sqlite3.connect(databasePath)
    global cursor
    cursor = connection.cursor()
    
    ##How many
    howManyExamples(unicode('日'))
    ##
    start_time = time.time()
    getResults(unicode('冷凍庫'))
    print time.time() - start_time, "seconds"
    
    cursor.close()
else:
    print None
    
    addHook('editFocusLost', add_examples_focusLost)
    #make menu item
    addHook("browser.setupMenus", setupMenu)
