# -*- coding: utf-8 -*-


#anki/python stuff
from aqt import mw
from aqt.utils import showCritical, showInfo, showWarning, tooltip
from anki.utils import stripHTML
from anki.hooks import addHook, wrap

from PyQt4.QtCore import *
from PyQt4 import *
from PyQt4.QtGui import *
import csv
import os
import sys
import sqlite3
import re
import cPickle as pickle
import codecs



try:
    import japaneseDict
    from ShortNSweetJSentences import SNSJsentences
except:
    pass
#from japaneseexamples import japanese_examples

this_dir, this_filename = os.path.split(__file__)
databasePath = os.path.join(this_dir, "edict.db") 
edictPicklePath = os.path.join(this_dir, "edict.pickle")
edictPath = os.path.join(this_dir, "edict_freq.txt") 
ignorePath = os.path.join(this_dir, "ignoredList.txt")
elementsPicklePath = os.path.join(this_dir, "elements.pickle")

edictPath2 = os.path.join(this_dir, "edict-freq-20081002") 
edictPicklePath2 = os.path.join(this_dir, "edict2.pickle")


use2 = True
if use2:
    edictPath = os.path.join(this_dir, "edict-freq-20081002") 
    edictPicklePath = os.path.join(this_dir, "edict2.pickle")
    

class WordSuggestor(QtGui.QWidget):
    
    def __init__(self):
        super(WordSuggestor, self).__init__()
        self.initUI()
        
        self.edict = dict()
        #kanjiCards
        self.knownKanjiCardIDs = []
        
        #ignored words
        self.ignoredWords = dict()
        
        #list using kanji as keys
        self.knownKanjis = dict()
        
        #wordCards
        self.knownWordCardIDs = []
        
        #normal list to use and exclude from database searches (words as keys)
        self.knownWords = dict()
        
        
        
        #Do initial search
        #self.onSearch()
        #self.load()
        
    def initUI(self):
        
        #Create elements
        self.optionsLabel = QtGui.QLabel('Search for cards as you do with the card browser')
        self.optionsLabel.setAlignment(Qt.AlignCenter)
        
        self.kanjiCardsLabel = QtGui.QLabel('Kanji Cards Search:')
        self.kanjiCardsSearch = QtGui.QLineEdit('Note:"Japanese (Kanji)"')
        self.kanjiCardsLabel.setAlignment(Qt.AlignCenter)
        
        self.kanjiCardsFieldLabel = QtGui.QLabel('Select Field: ')
        self.kanjiCardsFieldLabel.setAlignment(Qt.AlignCenter)
        self.kanjiCardsFieldSelector = QtGui.QComboBox()
        
        #self.kanjiCardsResultsLabel = QtGui.QLabel('Found: ')
        self.kanjiCardsButton = QtGui.QPushButton('Get cards!')
        self.kanjiCardsResultsNumberLabel = QtGui.QLabel('0')
        
        
        self.WordCardsLabel = QtGui.QLabel('Word Cards Search:')
        self.WordCardsLabel.setAlignment(Qt.AlignCenter)
        self.WordCardsSearch = QtGui.QLineEdit('Note:"Japanese (Vocab)"')
        
        #self.WordCardsResultsLabel = QtGui.QLabel('Found: ')
        self.WordCardsButton = QtGui.QPushButton('Get cards!')
        self.WordCardsResultsNumberLabel = QtGui.QLabel('0')
        
        self.WordCardsFieldLabel = QtGui.QLabel('Select Field: ')
        self.WordCardsFieldLabel.setAlignment(Qt.AlignCenter)
        self.WordCardsFieldSelector = QtGui.QComboBox()
        
        
        self.resultsList = QtGui.QListWidget()
        
        self.ignoreButton = QtGui.QPushButton('Ignore Selected')
        self.searchButton = QtGui.QPushButton('Search!')

        
        #Define layout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.setSpacing(10)
        grid.setColumnStretch(3, 1)
        
        #set size
        grid.setColumnMinimumWidth(3, 300)
        
        
        #Add elements
        grid.addWidget(self.optionsLabel, 1, 0, 1, 2)
        
        grid.addWidget(self.kanjiCardsLabel, 2, 0, 1, 2)
        grid.addWidget(self.kanjiCardsSearch, 3, 0, 1, 2)
        grid.addWidget(self.kanjiCardsButton, 4, 0, 1, 1)
        grid.addWidget(self.kanjiCardsResultsNumberLabel, 4, 1, 1, 2)
        grid.addWidget(self.kanjiCardsFieldSelector, 5, 1, 1, 1)
        grid.addWidget(self.kanjiCardsFieldLabel, 5, 0, 1, 1)
        
        grid.addWidget(self.WordCardsLabel, 6, 0, 1, 2)
        grid.addWidget(self.WordCardsSearch, 7, 0, 1, 2)
        grid.addWidget(self.WordCardsButton, 8, 0, 1, 1)
        grid.addWidget(self.WordCardsResultsNumberLabel, 8, 1, 1, 2)
        grid.addWidget(self.WordCardsFieldSelector, 9, 1, 1, 1)
        grid.addWidget(self.WordCardsFieldLabel, 9, 0, 1, 1)
        
        
             
        grid.addWidget(self.resultsList, 1, 3, 10, 4)
        
        lastRow = grid.rowCount ()
        
        grid.addWidget(self.searchButton, lastRow, 0, 1, 2)
        
        grid.addWidget(self.ignoreButton, lastRow, 3, 1, 1)
        
        
        #Connect everything
        #on focus lost, get fields for the combo boxes
        #self.kanjiCardsSearch.editingFinished.connect(self.onKanjiFieldChange)
        #self.WordCardsSearch.editingFinished.connect(self.onVocabFieldChange)
        
        
        self.kanjiCardsButton.clicked.connect(self.onKanjiFieldChange)
        self.WordCardsButton.clicked.connect(self.onVocabFieldChange)
        
        
        self.searchButton.clicked.connect(self.onSearch)
        self.ignoreButton.clicked.connect(self.onIgnore)
        
        
        #load pickle for some elements
        self.loadElementsPickle()
        
        
        #set title, and show
        self.setWindowTitle( 'Simple Japanese Word Suggester' )
        self.show()
    
    
    def loadElementsPickle(self):
        #if pickle exists
         if os.path.exists(elementsPicklePath):
            loadedPickle = pickle.load(open( elementsPicklePath, "rb" ))
            
            self.kanjiCardsSearch.setText(loadedPickle["kanjiSearchText"])
            self.WordCardsSearch.setText(loadedPickle["wordSearchText"])
            
            #then do a search
            self.getKanjiCardFields()
            self.getWordCardFields()
            
            #search comboboxes for index
            kanjiFIndex = self.kanjiCardsFieldSelector.findText(loadedPickle["kanjiSelectedFieldText"])
            wordFIndex = self.WordCardsFieldSelector.findText(loadedPickle["kanjiSelectedFieldText"])
            
            if kanjiFIndex < 0:
                kanjiFIndex = 0
            if wordFIndex < 0:
                wordFIndex = 0
                
            #might cause an error if field doesnt exist anymore (get index return 0?)
            self.kanjiCardsFieldSelector.setCurrentIndex(kanjiFIndex)
            
            self.WordCardsFieldSelector.setCurrentIndex(wordFIndex)
        
           
            
    def saveElementsPickle(self):
        
            
        savePickle = dict()
        savePickle = {
            "kanjiSearchText": self.kanjiCardsSearch.text(),
            "kanjiSelectedFieldText": self.kanjiCardsFieldSelector.currentText(),
            "wordSearchText": self.WordCardsSearch.text(),
            "wordSelectedFieldIndex": self.WordCardsFieldSelector.currentText()
                    }
        pickle.dump(savePickle, open(elementsPicklePath, 'wb'))
            
      
    def getKanjiList(self):
        #TEST
        
        if __name__ == '__main__':
            self.knownKanjis[unicode('鬯')] = 0.5
            self.knownKanjis[unicode('隶')] = 0.5
            
            self.kanjiCardsResultsNumberLabel.setText(str(len(self.knownKanjis)))
            return
        #########
                
        
        #get cards from anki
        kanjiField = self.kanjiCardsFieldSelector.currentText()
        
        
        for cardid in self.knownKanjiCardIDs:
            try:
                card = mw.col.getCard(cardid)
                note = card.note()
                #get first kanji in that field
                
                kanji = re.findall(ur'[\u4e00-\u9fbf]', unicode(note[kanjiField]))
                if not kanji:
                    continue
                else:
                    kanji = kanji[0]
                #possible problem if kanji is already in this list? what do? for now overwrite
                self.addKnownKanji(kanji, card.ivl/27)
                #########################WHAT VALUE
            except KeyError:
                continue
        
    def addKnownKanji(self, kanji, value):
        if kanji in self.knownKanjis:
            self.knownKanjis[kanji] = max(self.knownKanjis[kanji], value)
        else:
            self.knownKanjis[kanji] = float(value)
        
        
    def getWordList(self):
        #TEST
        
        if __name__ == '__main__':
            self.knownWords[unicode('髯')] = 0.5
            self.knownWords[unicode('髫')] = 0.5
            
            self.WordCardsResultsNumberLabel.setText(str(len(self.knownKanjis)))
            return
        #########
        
        #goto anki etc
        #ids = mw.col.findCards(self.WordCardsSearch.text())
        #get cards from anki
        WordField = self.WordCardsFieldSelector.currentText()
        
        
        for cardid in self.knownWordCardIDs:
            try:
                card = mw.col.getCard(cardid)
                note = card.note()

                
                #get bit before the reading, if there is any. Else get the whole field                
                word = re.findall(ur'(.*)\[.*', unicode(note[WordField]))
                if word:
                    continue
                else:
                    word = unicode(note[WordField])

                    #strio html
                    word = stripHTML(word)
                #just set boolean, we're only checking to see if the word exists
                self.knownWords[word] = True
                
                
                #extract the kanji from word
                kanjiz = self.getKanji(word)
                for k in kanjiz:
                    self.addKnownKanji(k, card.ivl/27)
                
            except KeyError:
                continue
        
        
        return
        
    def getKanjiCardFields(self):
        #populate combo box with fields available
        
        #TEST
        if __name__ == '__main__':
            self.kanjiCardsFieldSelector.clear()
            self.kanjiCardsFieldSelector.addItems(['1',' 2', '3', '4'])
            #update number of results
            self.kanjiCardsResultsNumberLabel.setText('4')
            return
        
        
        #get anki cards
        ids = mw.col.findCards(self.kanjiCardsSearch.text())
        
        #update number of results
        self.kanjiCardsResultsNumberLabel.setText(str(len(ids)))
        
        
        #if no results return
        if len(ids) == 0:
            return
        
        #save ID's for later, for now just get the fields
        self.knownKanjiCardIDs = ids
        
        

        kanjifields = []
        
        #get fields from first card
        card = mw.col.getCard(ids[0])
        note = card.note()
        for (name, dontcarevalue) in note.items():
            if name not in kanjifields:
                kanjifields.append(name)
                
        #set combo box
        self.kanjiCardsFieldSelector.clear()
        self.kanjiCardsFieldSelector.addItems(kanjifields)
        
    def onKanjiFieldChange(self):
        self.getKanjiCardFields()
        return
    
    def getWordCardFields(self):
        #TEST
        if __name__ == '__main__':
            self.WordCardsFieldSelector.clear()
            self.WordCardsFieldSelector.addItems(['a',' b', 'c', 'd'])
            #update number of results
            self.WordCardsResultsNumberLabel.setText('4')
            return
        
        #get anki cards
        ids = mw.col.findCards(self.WordCardsSearch.text())
        
        
        #update number of results
        self.WordCardsResultsNumberLabel.setText(str(len(ids)))
        
        
        #if no results return
        if len(ids) == 0:
            return
        
        #save ID's for later, for now just get the fields
        self.knownWordCardIDs = ids
        
        
        
        Wordfields = []
        
        #get fields from first card
        card = mw.col.getCard(ids[0])
        note = card.note()
        for (name, dontcarevalue) in note.items():
            if name not in Wordfields:
                Wordfields.append(name)
                
        #set combo box
        self.WordCardsFieldSelector.clear()
        self.WordCardsFieldSelector.addItems(Wordfields)
        
        
    def onVocabFieldChange(self):
        self.getWordCardFields()
        
        return
    
    def onIgnore(self):
        try:
            #set ignore flag
            ignoreWord = self.resultsList.currentItem().word
            self.resultsList.takeItem(self.resultsList.currentRow())
            self.ignoredWords[ignoreWord] = True
            #open file and append the word
            
            with codecs.open(ignorePath, 'a', 'UTF-8') as ignoreFile:
                print "ADDING TO IGNORE"
                print ignoreWord
                ignoreFile.write(ignoreWord+'\n')
                
        except AttributeError:
            pass    
        #load word into ignored list
        #refresh the search/remove from list
        return
    
    def loadIgnoredWords(self):
        #open file
        if os.path.exists(ignorePath):
            with codecs.open(ignorePath, 'r', 'UTF-8') as ignoreFile:
                ignoreFromFile = ignoreFile.read().splitlines()
                
            for w in ignoreFromFile:
                self.ignoredWords[w] = True
                
            print "Ignored Words:"
        
        
    def onSearch(self):
        #search and populate the list
        self.getKanjiList()
        self.getWordList()
        self.loadIgnoredWords()
        #self.save()
        #self.save()
        
        
        
        print self.knownKanjis
        
        print self.knownWords
        
        
        #load dict
        self.loadPickleDictionary()
        
        
        #these are unicode
        dontShowWords = self.knownWords.keys()
        
        dontShowWords += self.ignoredWords.keys()
        
        #merge ignored words and known word dicts
        
        
        #dontShowWords 
        
        #results = self.cursor.execute('SELECT * FROM dict WHERE kanji NOT IN ignoreWords').fetchall()
        
        
        
        #get dict and update values, then sort and return results
        
        #get initial results excluding known words and ignore words 
        results = []
        resultKeys = self.edict.viewkeys() - (self.knownWords.viewkeys() | self.ignoredWords.viewkeys())
        
        
        #and have kanji in the knownKanjis list
        
        count = 0
        l = len(resultKeys)
        for r in resultKeys:
#         entry = {'reading':reading, 
#         'meaning':meaning, 
#         'pFlag':popular, 
#         'kanjis':kanjis, 
#         'percentOfTotal':percentOfTotal} 
#             print str(count) + '/' + str(l) 
#             count += 1

            try:
                kanjiMod = self.knownKanjis[self.edict[r]['kanjis'][0]]
            except KeyError:
                kanjiMod = 0.5
            self.edict[r]['sortValue'] =self.edict[r]['percentOfTotal']*kanjiMod
         
        #sort dict again
        ##slow implementation apparently?
        #sorted(results, key=results.get)
        ##faster more confusing implementation?
        from operator import itemgetter
        sorted_results = sorted(resultKeys, key=lambda k: self.edict[k]['sortValue'], reverse=True)
        
        
        #clear list
        self.resultsList.clear()
        
        #display results
        
        #placeholder funtion
        
        self.populateListFromPickle(sorted_results[0:100])
        
        #save the search elements
        self.saveElementsPickle()
        
        return
        
        
    def populateListFromPickle(self, results):
        
        
        #entry = {'reading':reading, 'meaning':meaning, 'pFlag':popular, 'kanjis':kanjis, 'percentOfTotal':percentOfTotal}
                
        for i in results:
            #item = QListWidgetItem(unicode(str(self.edict[i]['sortValue']) + '::' + i + '[' + self.edict[i]['reading'] + ']: ' + self.edict[i]['meaning']))
            item = QListWidgetItem(unicode(i + '[' + self.edict[i]['reading'] + ']: ' + self.edict[i]['meaning']))
            item.word = unicode(i)
            self.resultsList.addItem(item)
            
        return
    
        
    def onSearchDB(self):
        #search and populate the list
        self.getWordList()
        self.getKanjiList()
        self.loadIgnoredWords()
        #self.save()
        #self.save()
        print self.knownKanjis
        
        print self.knownWords
        #connect
        
        self.connection = sqlite3.Connection(databasePath)
        self.cursor = self.connection.cursor()
        
        #these are unicode
        ignoreWords = self.knownWords.keys()
        
        #these are srt so convert them
        #ignoreWords += [entry.decode('UTF-8') for entry in  self.ignoredWords.keys()]
        
        ignoreWords += self.ignoredWords.keys()
        
        ignoreWordsTupled = [(entry,) for entry in  ignoreWords]
        #insert ignore words into an ignore table
        self.cursor.execute('CREATE TEMP TABLE ignoreWords (word)')
#         for ent in ignoreWords:
#             self.cursor.execute('INSERT INTO ignoreWords (word) VALUES (?)', [ent])
        self.cursor.executemany('INSERT INTO ignoreWords (word) VALUES (?)', ignoreWordsTupled)
        
        #some sql string formatting
        #sql="SELECT * FROM dict WHERE kanji NOT IN ({seq}) LIMIT 20".format(seq=','.join(['?']*len(ignoreWords)))
        
        #results = self.cursor.execute(sql, ignoreWords ).fetchall()
        results = self.cursor.execute('SELECT * FROM dict WHERE kanji NOT IN ignoreWords').fetchall()
        
        #search DB for top 20 words that are not in ignore and not in knownwords
        
        #and have kanji in the knownKanjis list
        #close
        self.cursor.close()
        
        #then sort the results using RANDOM FUNCTION
        
        #clear list
        self.resultsList.clear()
        
        #display results
        
        #placeholder funtion
        
        self.populateListFromDb(results[0:20])
        return
    
    def populateListFromDb(self, results):
        
        for i in results:
            item = QListWidgetItem(unicode(i[0] + '[' + i[1] + ']: ' + i[2]))
            item.word = unicode(i[0])
            self.resultsList.addItem(item)
            
        return
    
    def createDictionaryDatabase(self):
        
        self.connection = conn = sqlite3.connect(databasePath)
        self.cursor = self.connection.cursor()
            
        
        self.cursor.execute('PRAGMA encoding = "UTF-8";')
        
        self.cursor.execute('CREATE TABLE dict (kanji TEXT, kana TEXT, entry TEXT, p INT, kanjis TEXT , ignore INT)')
        
        def file_len(fname):
            with open(fname) as f:
                for i, l in enumerate(f):
                    pass
            return i + 1
        
        filelength = str( file_len(edictPath))
        
        
        db_input = []
        with open(edictPath, 'rb') as input_file:
            reader = csv.reader(input_file, delimiter="\t")
#             0[cumulative occurrences]
#             1\t[instance occurrences]
#             2\t[instance percentage of total]
#             3\t[cumulative percentage of total]
#             4\t[terms and definitions delimited by pipes]
            count = 0
            into_db = []
            for i in reader:
                print str(count) + ' / ' + filelength
                count = count + 1
                #detect if kanji and save them
                firstfield = i[4].split('|')[0]
                kanjis = []
                kanjis = re.findall(ur'[\u4e00-\u9fbf]', unicode(firstfield))
                if len(kanjis) == 0:
                    continue
                
                #count number of meanings, if more than 2 get from external
                meaningsCount = re.findall(firstfield, i[4])
                if len(meaningsCount) > 1:
                    #get best meaning
                    bestResult = self.getBestMeaning(unicode(firstfield))
                    #(expression, unicode(), glossary, conjugations, source, count)
                    if not bestResult:
                        print 'Couldnt match ' + firstfield
                        continue
                    expression = unicode(bestResult[0])
                    reading = unicode(bestResult[1])
                    meaning = unicode(bestResult[2])
                else:
                    expression = unicode(firstfield)
                    reading = unicode(i[4].split('|')[1])
                    meaning = unicode(','.join(i[4].split('|')[2::]))
                    
                    
                    
                popular = re.findall(ur'\(P\)', i[4])
                if popular:
                    popular = 1
                else:
                    popular = 0
                    
                into_db.append((expression, reading , meaning, popular, unicode(' '.join(kanjis)) , '0'))         
            print into_db[0::20]    
            self.cursor.executemany("INSERT INTO dict (kanji , kana , entry , p , kanjis , ignore ) VALUES (?, ?, ?, ?, ?, ?);", into_db)
            self.connection.commit()
            self.connection.close()
            #db_input.append((unicode(i[0]), ))    
    
    def getKanji(self, inputString):
        return re.findall(ur'[\u4e00-\u9fbf]', unicode(inputString))
    
    
    def createDictionaryPickle(self):
        def file_len(fname):
            with open(fname) as f:
                for i, l in enumerate(f):
                    pass
            return i + 1
        
        filelength = str( file_len(edictPath))
        
        edictDict = dict()
        with open(edictPath, 'rb') as input_file:
            reader = csv.reader(input_file, delimiter="\t")
#             0[cumulative occurrences]
#             1\t[instance occurrences]
#             2\t[instance percentage of total]
#             3\t[cumulative percentage of total]
#             4\t[terms and definitions delimited by pipes]
            count = 0
            
            for i in reader:
                
                
                percentOfTotal = i[2]
                print str(count) + ' / ' + filelength
                count = count + 1
                #detect if kanji and save them
                firstfield = i[4].split('|')[0]
                kanjis = []
                kanjis = re.findall(ur'[\u4e00-\u9fbf]', unicode(firstfield))
                if len(kanjis) == 0:
                    continue
                
                #count number of meanings, if more than 2 get from external
                meaningsCount = re.findall(firstfield, i[4])
                if len(meaningsCount) > 1:
                    #get best meaning
                    bestResult = self.getBestMeaning(unicode(firstfield))
                    #(expression, unicode(), glossary, conjugations, source, count)
                    if not bestResult:
                        print 'Couldnt match ' + firstfield
                        continue
                    
                    expression = unicode(bestResult[0])
                    reading = unicode(bestResult[1])
                    meaning = unicode(bestResult[2])
                else:
                    expression = unicode(firstfield)
                    reading = unicode(i[4].split('|')[1])
                    meaning = unicode(','.join(i[4].split('|')[2::]))
                    
                    
                popular = re.findall(ur'\(P\)', i[4])
                if popular:
                    popular = 1
                else:
                    popular = 0
                    
                    #{'one': 1, 'two': 2, 'three': 3}
                #percentOfTotal, expression, reading , meaning, popular, kanjis[])
                entry = {'reading':reading, 'meaning':meaning, 'pFlag':popular, 'kanjis':kanjis, 'percentOfTotal':float(percentOfTotal)}
                edictDict[expression] = entry
            pickle.dump(edictDict, open( edictPicklePath, "wb" ), -1)
        
    def createDictionaryPickle2(self):
        def file_len(fname):
            with open(fname) as f:
                for i, l in enumerate(f):
                    pass
            return i + 1
        
        filelength = str( file_len(edictPath2))
        
        edictDict = dict()
        with open(edictPath2, 'rb') as input_file:
            reader = csv.reader(input_file, delimiter="/")
# あがり目 [あがりめ] /(n) (1) eyes slanted upward/(2) rising tendency/###50/
# あきたこまち /(n) Akitakomachi (variety of rice)/###3290/


            count = 0
            
            for i in reader:
                
                percentOfTotal = i[len(i)-2][3:len(i[len(i)-2])] #maybe -2
                
                
                print str(count) + ' / ' + filelength
                count = count + 1
                
                #detect if kanji and save them
                firstfield = i[0]
                kanjis = []
                kanjis = re.findall(ur'[\u4e00-\u9fbf]', unicode(firstfield))
                
                #disable this to enable all word, not just kanji words
                if len(kanjis) == 0:
                    continue
                
                #strip readings
                expression = re.findall(ur'(.*)\[.*', unicode(firstfield))[0]
                
                #skip dupes
                if expression in edictDict:
                    if edictDict[expression]['pFlag']:
                        continue
                
                
                
                #if there is a reading get it, else its the expression
                reading = re.findall(ur'.*\[(.*)\]', unicode(firstfield))[0]
                if not reading:
                    reading = expression
                meaning = unicode(','.join(i[1::len(i)-1])) #maybe more minus.....
                    
                    
                popular = re.findall(ur'\(P\)', meaning)
                if popular:
                    popular = 1
                else:
                    popular = 0
                    
                    #{'one': 1, 'two': 2, 'three': 3}
                #percentOfTotal, expression, reading , meaning, popular, kanjis[])
                entry = {'reading':reading, 'meaning':meaning, 'pFlag':popular, 'kanjis':kanjis, 'percentOfTotal':float(percentOfTotal)}
                edictDict[expression] = entry
            pickle.dump(edictDict, open( edictPicklePath2, "wb" ), -1)
        
        
    
    def getBestMeaning(self, word):
        language = japaneseDict.initLanguage()
        
        results, length = language.wordSearch(word, 100, False)
        if not results:
            return
        
        #cheeky get num of results from tanaka
        for i in range(0,len(results)):
            results[i] = results[i] +  (unicode(SNSJsentences.howManyExamples(results[i][0])),)
        
        #build unique dict
        resultsByKey = dict()
        for r in results:
            resultsByKey[r[0]+' '+ r[1] +' '+ r[2]+' '+ r[3]+' '+ r[4] + ' ' +r[5] ] = r

        #WTF no sorting????????
        
        #(expression, unicode(), glossary, conjugations, source, count)
        if results:
            return results[0]
    
    
    def loadPickleDictionary(self):
        
        #########
#         os.remove(databasePath)
#         self.createDictionaryDatabase()
        #########
        global use2
            
        if not os.path.exists(edictPicklePath) and os.path.exists(edictPath):
            #if no pickle, but there is an edict file, read from EDICT, and create the database
            print 'Making dictionary...'
            if use2 == True:
                self.createDictionaryPickle2()
            else:
                self.createDictionaryPickle()
            print 'Dictionary = Finished!'
        print 'Loading dict'
        self.edict = pickle.load(open( edictPicklePath, "rb" ))
        print 'Done!'
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = WordSuggestor()
    sys.exit(app.exec_())

def setupMenu(mw):
    
    #menuconf = QAction("AwesomeTTS", mw)
    a = QAction( 'JWord Suggester', mw )
    mw.connect(a, SIGNAL("triggered()"), lambda e=mw: onSuggester(e))
    mw.form.menuEdit.addSeparator()
    mw.form.menuTools.addAction( a )
    
def onSuggester(window):
   window.ws = WordSuggestor()


if __name__ == '__main__':
    main()
else:
    setupMenu(mw)
