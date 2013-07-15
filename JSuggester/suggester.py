# -*- coding: utf-8 -*-


#anki/python stuff
from aqt import mw
from aqt.utils import showCritical, showInfo, showWarning, tooltip
from anki.hooks import addHook, wrap

from PyQt4.QtCore import *
from PyQt4 import *
from PyQt4.QtGui import *
import csv
import os
import sys
import apsw
import sqlite3
import re

try:
    import japaneseDict
    from japaneseexamples import japanese_examples
except:
    pass
#from japaneseexamples import japanese_examples

this_dir, this_filename = os.path.split(__file__)
databasePath = os.path.join(this_dir, "edict.db") 
edictPath = os.path.join(this_dir, "edict_freq.txt") 


class WordSuggestor(QtGui.QWidget):
    
    def __init__(self):
        super(WordSuggestor, self).__init__()
        self.initUI()
        
        #kanjiCards
        self.knownKanjiCardIDs = []
        
        #list using kanji as keys
        self.knownKanjis = []
        
        #wordCards
        self.knownWordCardIDs = []
        
        #normal list to use and exclude from database searches (words as keys)
        self.knownWords = []
        
        #might use a flat file for ignored words
        self.ignoredWords = []
        
        
        #Do initial search
        self.onSearch()
        
        
    def initUI(self):
        
        #Create elements
        self.optionsLabel = QtGui.QLabel('Search for cards as you do with the card browser')
        self.optionsLabel.setAlignment(Qt.AlignCenter)
        
        self.kanjiCardsLabel = QtGui.QLabel('Kanji Cards Search:')
        self.kanjiCardsSearch = QtGui.QLineEdit('Deck:KanjiDeck')
        self.kanjiCardsLabel.setAlignment(Qt.AlignCenter)
        
        self.kanjiCardsFieldLabel = QtGui.QLabel('Select Field: ')
        self.kanjiCardsFieldLabel.setAlignment(Qt.AlignCenter)
        self.kanjiCardsFieldSelector = QtGui.QComboBox()
        
        #self.kanjiCardsResultsLabel = QtGui.QLabel('Found: ')
        self.kanjiCardsButton = QtGui.QPushButton('Get cards!')
        self.kanjiCardsResultsNumberLabel = QtGui.QLabel('0')
        
        
        self.WordCardsLabel = QtGui.QLabel('Word Cards Search:')
        self.WordCardsLabel.setAlignment(Qt.AlignCenter)
        self.WordCardsSearch = QtGui.QLineEdit('Deck:VocabDeck')
        
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
        
        self.kanjiCardsFieldSelector.currentIndexChanged.connect(self.onKanjiComboBox)
        self.WordCardsFieldSelector.currentIndexChanged.connect(self.onWordComboBox)
        
        self.kanjiCardsButton.clicked.connect(self.onKanjiFieldChange)
        self.WordCardsButton.clicked.connect(self.onVocabFieldChange)
        
        
        self.searchButton.clicked.connect(self.onSearch)
        self.ignoreButton.clicked.connect(self.onIgnore)
        
        
        #set title, and show
        self.setWindowTitle( 'Simple Japanese Word Suggester' )
        self.show()
        
    

    def getKanjiList(self):
        #TEST
        self.knownKanjis = dict()
        
        if __name__ == '__main__':
            self.knownKanjis['�ｽ�ｽ'] = 0.5
            self.knownKanjis['�ｽL'] = 0.5
            self.knownKanjis['�ｽ�ｽ'] = 0.5
            self.knownKanjis['�ｽ�ｽ'] = 0.5
            self.knownKanjis['�ｽ�ｽ'] = 0.5
            
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
                self.knownKanjis[kanji] = 0.5
                #########################WHAT VALUE
            except KeyError:
                continue
        
        
        
    def getWordList(self):
        #TEST
        self.knownWords = dict()
        
        if __name__ == '__main__':
            self.knownWords['迪ｫ'] = 0.5
            self.knownWords['縺秘｣ｯ'] = 0.5
            self.knownWords['繝舌ぜ'] = 0.5
            
            self.WordCardsResultsNumberLabel.setText(str(len(self.knownKanjis)))
            return
        #########
        
        #goto anki etc
        ids = mw.col.findCards(self.WordCardsSearch.text())
        #get cards from anki
        WordField = self.WordCardsFieldSelector.currentText()
        
        
        for cardid in ids:
            try:
                card = mw.col.getCard(cardid)
                note = card.note()
                #get first kanji in that field
                
                
                word = re.findall(ur'(.*)\[.*', unicode(note[WordField]))
                if not word:
                    continue
                else:
                    word = unicode(note[WordField])

                    #strio html
                    word = stripHTML(word)
                #just set boolean, we're only checking to see if the word exists
                self.knownWords[word] = True

            except KeyError:
                continue
        
        
        return
        
    def onKanjiComboBox(self):
        self.getKanjiList()
        return
    
    def onWordComboBox(self):
        self.getWordList()
        return
    
    def getKanjiCardFields(self):
        #populate combo box with fields available
        
        #TEST
        if __name__ == '__main__':
            self.kanjiCardsFieldSelector.clear()
            self.kanjiCardsFieldSelector.addItems(['1',' 2', '3', '4'])
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
        #set ignore flag
        #open file and append the word
        #load word into ignored list
        #refresh the search/remove from list
        return
    
    def onSearch(self):
        #search and populate the list
        
        
        print self.knownKanjis
        
        print self.knownWords
        #connect
        
        self.connection = apsw.Connection(databasePath)
        self.cursor = self.connection.cursor()
        
        results = self.cursor.execute('SELECT * FROM dict LIMIT 20').fetchall()[0]
        
        
        #search DB for top 20 words that are not in ignore and not in knownwords
        returnedList= self.cursor.execute('SELECT * FROM dict LIMIT 20').fetchall()
        #and have kanji in the knownKanjis list
        #close
        self.cursor.close()
        
        #then sort the results using RANDOM FUNCTION
        
        #clear list
        self.resultsList.clear()
        
        #display results
        
        #placeholder funtion
        
        self.populateList(returnedList)
        return
    
    def populateList(self, results):
        
        for i in results:
            item = QListWidgetItem(i[0] + '[' + i[1] + ']: ' + i[2])
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
    
    def getBestMeaning(self, word):
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
        if results:
            return results[0]
    
    
    def connect2edict(self):
        
        #########
#         os.remove(databasePath)
#         self.createDictionaryDatabase()
        #########
        if not os.path.exists(databasePath) and os.path.exists(edictPath):
            #if no database, but there is an edict file, read from EDICT, and create the database
            self.createDictionaryDatabase()
        
        print results
        
        
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