#!/usr/bin/python
#-*- coding: utf-8 -*-
# Description: Looks for example sentences in the Tatoeba Corpus, matches by sense and shortest
# Author: Ian Worthington
# License:     GPL

# --- initialize kanji database ---

from aqt import mw
import os
import re

import csv
from anki.utils import stripHTML
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
import sqlite3
from anki.hooks import addHook
import time
import codecs



EList = collections.namedtuple('exampleList',['qjap', 'ejap', 'eng'])

# file containing the Tatoeba corpus sentences





#cursor for database stuff
#cursor = None

expField  = "Dictionary Form"
dstField = "Tatoeba Examples"

MAX = 3


this_dir, this_filename = os.path.split(__file__)
databasePath = os.path.join(this_dir, "tatoebaExamples.db")
examplesPath = os.path.join(this_dir, "japanese_examples.utf")


def createExamplesDatabase():
    
    
    if os.path.exists(databasePath):
        #comment this line to force a remake
        return
        os.remove(databasePath)
    
    conn = sqlite3.connect(databasePath)
    cursor = conn.cursor()

    
    cursor.execute('PRAGMA encoding = "UTF-8";')
    

    #both examples in this table
    cursor.execute("""CREATE TABLE examples (JID INT PRIMARY KEY, jSentence ntext, furigana ntext, eSentence ntext)
           """)
        
    
    #create word table
    cursor.execute("""CREATE TABLE wordLinks
          (jap_Sentence_ID INT , 
           keyword_offset INT, 
           keyword_length INT, 
           keyword TEXT, 
           entry_id INT, 
           sense INT)""")
    
    
    #BOTH SENTENCES
    #japSentence, engSentence, JapID, engID
    reg = re.compile('A:(.*)\t(.*)#ID=.*_(.*)')
    kanjiReg = re.compile(ur'[\u4e00-\u9fbf]')
    inarray = []
    with codecs.open(examplesPath, encoding='utf-8') as input_file:
        content = input_file.readlines()
        
    
    lineNum = 0
    maxLineNum = (len(content))/2
    for num in range(lineNum, maxLineNum):
        i, jLine = content[num*2:(num*2)+2]
        print str(num) + '/' + str(maxLineNum)
        #get rid of that newline
        jLine = jLine.rstrip('\n')
        i = i.rstrip('\n')
        fields  = reg.findall(i)[0]
        
        furiganaSentence = fields[0]
        
        #for each match of (akjhfkajsdhfkj .... P    {
        #dictionary word (kana) {how it appears in sentence}
        #霓､�ｺ郢ｧ�ｽ邵ｺ蜷ｶ��{邵ｺ蜷ｶ�急
        
        if int(num) == 13:
            print 'HELLLLOO'
        
        #keep track of last replace
        lastIndex = 0
        
        for m in jLine.split(' ')[1:]:
            #0 is always just B so ignore it.
            dictPart = re.findall('(.*?)[\\(|\\{|\n|\\[]', m)
            if dictPart == []:
                dictPart = m
            else:
                dictPart = dictPart[0]
                
            
            #get what is the version in the original sentence {}
            sentencePart = re.findall('\{(.*?)\}', m)
            if sentencePart == []:
                sentencePart = dictPart
            else:
                sentencePart = sentencePart[0]
            
                
            #if there's no kanji then there's no problem
            if kanjiReg.findall(unicode(sentencePart)) == []:
                continue
            
            ###########REALLY we could look up the SENSE in a dictionary to get the reading.
            #if there is a kata version then use it
            kataPart = re.findall('\((.*?)\)', m)
            if kataPart == []:
                #use mecab to get the sentence part
                #kataPart = 'test'
                furi = mecab.reading(sentencePart)
                #furi = sentencePart+'[BASASS]'
            else:
                furi = sentencePart+'['+kataPart[0]+']'
            
            
            ##This is complicated to avoid duplicates same word replacements
            #find last index
             
            lastIndex = furiganaSentence.rfind(']')
            if lastIndex == -1:
                lastIndex = 0
                
            #then cut out a chunk of string which will be replaced
            chunk = furiganaSentence[lastIndex:]
            furiganaSentence = furiganaSentence[0:lastIndex] + chunk.replace(sentencePart, unicode(furi), 1)
            
            #find where we are going to do the replace
            
            
        addIn = (fields[0], fields[1], fields[2], furiganaSentence )
        inarray.append(addIn)
        
        
    cursor.executemany("INSERT OR IGNORE INTO examples (jSentence,  eSentence, JID, furigana) VALUES (?, ?, ?, ?);", inarray)
    
    
    #WORD - SENTENCE LINKS

    with open('sweet.csv', 'rb') as input_file:
        reader = csv.reader(input_file, delimiter="\t")
        wordSenLinks2db = [(unicode(i[0]), unicode(i[1]), unicode(i[2]), unicode(i[3]), unicode(i[4]), unicode(i[5])) for i in reader]

    cursor.executemany("INSERT INTO wordLinks (jap_Sentence_ID, keyword_offset, keyword_length, keyword, entry_id, sense) VALUES (?, ?, ?, ?, ?, ?);", wordSenLinks2db)
        

    
    conn.commit()
    print 'Made DB' 
    print [x for x in cursor.execute('select * from wordLinks LIMIT 5')]
    print [x for x in cursor.execute('select * from examples LIMIT 5')]
    conn.close
    

def howManyExamples(expression):

    
    results = cursor.execute('SELECT * FROM wordLinks WHERE keyword = (?)', [expression])
    
    number = len(results.fetchall())
    #connection.close()
    
    #print number
    return number



def getResults(expression):
    results = cursor.execute('''Select * from (SELECT 
                            E.jSentence,
                            E.eSentence,
                            WL.keyword_offset, 
                            WL.keyword_length,
                            WL.sense,
                            LENGTH(E.jSentence),
                            E.furigana
                            FROM examples AS E 
                                JOIN wordLinks as WL ON E.JID=WL.jap_Sentence_ID  
                                WHERE WL.keyword=(?)
                                ORDER BY LENGTH(E.jSentence) DESC) 
                                GROUP by sense
                            ''', [expression])
    
#     resultsList = results.fetchall()
#     print len(resultsList)
#     for i in resultsList:
#         print '--------'
#         print 'jsen:' + unicode(i[0])
#         print 'esen:' + unicode(i[1])
#         print 'offset:' + unicode(i[2])
#         print 'len:' + unicode(i[3])
#         print 'sense:' + unicode(i[4])
#         print 'senLen:' + unicode(i[5])
    return results
    
    
def getResultsTest(expression):
        results = cursor.execute('''Select * from (SELECT 
                            E.jSentence,
                            E.eSentence,
                            WL.keyword_offset, 
                            WL.keyword_length,
                            WL.sense,
                            LENGTH(E.jSentence),
                            WL.entry_id,
                            jap_Sentence_ID,
                            E.furigana
                            FROM examples AS E 
                            JOIN wordLinks as WL ON E.JID=WL.jap_Sentence_ID  
                            WHERE WL.keyword=(?)
                            GROUP BY jap_Sentence_ID
                            ORDER BY LENGTH(E.jSentence) DESC)
                            ''', [expression])
        
        resultsList = results.fetchall()
        actualResults = dict()
        

        for i in resultsList:
            actualResults[unicode(i[4]) + unicode(i[6])] = i
            print '--ORIGINAL------'
            print 'jsen:' + unicode(i[0])
            print 'esen:' + unicode(i[1])
            print 'offset:' + unicode(i[2])
            print 'len:' + unicode(i[3])
            print 'sense:' + unicode(i[4])
            print 'senLen:' + unicode(i[5])
            print 'entryId:' + unicode(i[6])
            print 'sentenceId:' + unicode(i[7])
            print 'furigana:' + unicode(i[8])
            
        for i in actualResults.itervalues():
            
            print '----REMOVEDDUPE----'
            print 'jsen:' + unicode(i[0])
            print 'esen:' + unicode(i[1])
            print 'offset:' + unicode(i[2])
            print 'len:' + unicode(i[3])
            print 'sense:' + unicode(i[4])
            print 'senLen:' + unicode(i[5])
            print 'entryId:' + unicode(i[6])
            print 'sentenceId:' + unicode(i[7])
            print 'furigana:' + unicode(i[8])
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
        print 'furigana:' + unicode(i[6])
        
        #English can be added
        examples_eng.append(i[1])
        
        #get a reading version of jap sentence for answer
        japAnswer = i[6]
        
        expressionForm = i[0][(i[2]+1):(i[2]+i[3]+1)]
        
        #this replaces the word we want with the underline
        
        ##originally we got this separate but now we're chaging to using the pre-furiversion below
        #for original sentence make sure to search the reading version of the term
        #expression_reading = mecab.reading(expressionForm)
        
        #find the expression form within the furi verison and try to grab furigana after it
        
        
        #find what we need to replace: either the expression alone, or including the furigana or the expression from mecab
        mecabReading = re.escape( mecab.reading(expressionForm))
        finderRE = re.compile( '(' + 
                                         expressionForm + '\[.*?\]' + 
                                         '|' + expressionForm +
                                         '|' +  mecabReading + ')')
        replaceThis = re.findall(finderRE, japAnswer)
        replaceThis = replaceThis[0]
        #first try to replace using the reading version
        replacedJapAnswer = japAnswer.replace(replaceThis, '<span class=focusword>'+ replaceThis +'</span>')
        exampleQ = japAnswer.replace(replaceThis ,'<span class=focusword>_____</span>')
        
        #if it failed to replace using reading version then just replace the normal
#         if replacedJapAnswer == japAnswer:
#             replacedJapAnswer = japAnswer.replace(expressionForm ,'<span class=focusword>'+expressionForm +'</span>')
        exampleJ = replacedJapAnswer        
                
        #add jap and question
        examples_question.append(exampleQ)
        examples_jap.append(exampleJ)
        
        print unicode(examples_question[0])
        print unicode(examples_jap[0])
        print unicode(examples_eng[0])

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
        #connection = sqlite3.connect(databasePath)
        global cursor
        #cursor = connection.cursor()
        
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
    #connection = sqlite3.connect(databasePath)
    global cursor
    #cursor = connection.cursor()
    
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
    from reading import mecab
    createExamplesDatabase()
    #do tests
    #Connect to DB
#     os.remove(databasePath)
# 
#     global cursor
#     global connection
#     connection = sqlite3.Connection(databasePath)
#     cursor = connection.cursor()
#     
#     createExamplesDatabase()
    
    #connect to database
    connection = sqlite3.connect(databasePath)
    cursor = connection.cursor()

    ##How many
    print howManyExamples(unicode('ご飯'))
    #     ##
    find_examples(unicode('ご飯'))
    test = unicode('ご飯')
    start_time = time.time()
    getResultsTest(test)
    print '----#################-----'
    getResults(test)
    print time.time() - start_time, "seconds"
    
    cursor.close()


    print 

else:
    from japanese.reading import mecab
    createExamplesDatabase()
    
    
    connection = sqlite3.Connection(databasePath)
    cursor = connection.cursor()

    
    addHook('editFocusLost', add_examples_focusLost)
    #make menu item
    addHook("browser.setupMenus", setupMenu)
