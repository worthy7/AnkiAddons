# -*- coding: utf-8 -*-


#anki/python stuff
from aqt import mw
from anki.hooks import addHook
from PyQt4.QtCore import *
from PyQt4 import *
from PyQt4.QtGui import *
import csv
import os
import sys
import pickle
import apsw
import sqlite3
import re

try:
    import japaneseDict
    from japaneseexamples import japanese_examples
except:
    pass
#from japaneseexamples import japanese_examples

 
 
databasePath = 'edict.db'
edictPath = 'edict_freq.txt'


class WordSuggestor(QtGui.QWidget):
    
    def __init__(self):
        super(WordSuggestor, self).__init__()
        self.initUI()
        self.connect2edict()
        
    
    def initUI(self):
        
        #Create elements
        optionsLabel = QtGui.QLabel('Options')
        kanjiCardsLabel = QtGui.QLabel('Kanji Cards:')
        kanjiCardsSearch = QtGui.QLineEdit()
        kanjiCardsResultsLabel = QtGui.QLabel('Found: ')
        kanjiCardsResultsNumberLabel = QtGui.QLabel('0')
        
        
        
        WordCardsLabel = QtGui.QLabel('Word Cards:')
        WordCardsSearch = QtGui.QLineEdit()
        WordCardsResultsLabel = QtGui.QLabel('Found: ')
        WordCardsResultsNumberLabel = QtGui.QLabel('0')
        
        self.RL = resultsList = QtGui.QListWidget()
        
        searchButton = QtGui.QPushButton('Search!')
        closeButton = QtGui.QPushButton('Close')

        #Define layout
        grid = QtGui.QGridLayout()
        self.setLayout(grid) 
        grid.setSpacing(10)

        #Add elements
        grid.addWidget(optionsLabel, 1, 0, 1, 2)
        
        grid.addWidget(kanjiCardsLabel, 2, 0, 1, 1)
        grid.addWidget(kanjiCardsSearch, 2, 1, 1, 1)
        grid.addWidget(kanjiCardsResultsLabel, 3, 0, 1, 1)
        grid.addWidget(kanjiCardsResultsNumberLabel, 3, 1, 1, 1)
        
        
        
        grid.addWidget(WordCardsLabel, 4, 0, 1, 1)
        grid.addWidget(WordCardsSearch, 4, 1, 1, 1)
        grid.addWidget(WordCardsResultsLabel, 5, 0, 1, 1)
        grid.addWidget(WordCardsResultsNumberLabel, 5, 1, 1, 1)
             
        grid.addWidget(resultsList, 1, 3, 10, 4)
                
        grid.addWidget(searchButton)
        grid.addWidget(closeButton)
        
        
        #set title, and show
        self.setWindowTitle( 'Simple Japanese Word Suggestor' )
        self.show()
    
    def populateList(self):
        results = self.cursor.execute('SELECT * FROM dict LIMIT 20').fetchall()
        
        for i in results:
            item = QListWidgetItem(i[0] + '[' + i[1] + ']: ' + i[2])
            self.RL.addItem(item)
            
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
        
        self.connection = apsw.Connection(databasePath)
        self.cursor = self.connection.cursor()
        
        results = self.cursor.execute('SELECT * FROM dict LIMIT 20').fetchall()[0]
        print results
        
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = WordSuggestor()
    
    
    ex.populateList()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
else:
    mw.ws = WordSuggestor( mw )
    mw.ws.show()