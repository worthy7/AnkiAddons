# -*- coding: utf-8 -*-
# Copyright: Ian Worthington <Worthy.vii@gmail.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#
# Adding of Vocabulary - to the "Common JWord" field
#

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from collections import defaultdict
import os
import re

import sys
import codecs
import csv
import cPickle as pickle


# Vocab file path
this_dir, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(this_dir, "edict-freq-20081002") 

edictPicklePath = os.path.join(this_dir, "edict2.pickle")



heisigWordsPath = os.path.join(this_dir, "heisigVocab.txt")
heisigLearnerWordsPath = os.path.join(this_dir, "heisigLearnerVocab.txt") 
					
rtkPicklePath = os.path.join(this_dir, "rtk.pickle") 



bestKanjiPath= os.path.join(this_dir, "bestKanjiWords.pickle")
bestKanjiLearnerPath= os.path.join(this_dir, "bestKanjiLearnerWords.pickle")
#Select from the above 2 paths
dictToUse = bestKanjiPath
	
#Vocab gets indexed into here
vocabIndex = defaultdict(list)
#Fields used
#in					
expField = 'Expression'
#out
vocabDstField = 'Common JWord'


#the kanji dict
kanjiBestWordDict = dict()
kanjiBestWordLearnerDict = dict()
RTKKanji = dict()

def getHardestKanji(kanjiz):
	#it will never be 0 length
	global RTKKanji
	#first get only the kanji
	hardestKanji = None
	
	for k in kanjiz:
		if (k in RTKKanji):
			if hardestKanji == None or int(RTKKanji[hardestKanji]['heisig2010']) < int(RTKKanji[k]['heisig2010']):
				hardestKanji = k
	return unicode(hardestKanji)

def createBestWordDict():
	def file_len(fname):
		with open(fname) as f:
			for i, l in enumerate(f):
				pass
		return i + 1
	
	filelength = str( file_len(DATA_PATH))
	
	edictDict = dict()
	global kanjiBestWordDict
	global kanjiBestWordLearnerDict
	
	with open(DATA_PATH, 'rb') as input_file:
		reader = csv.reader(input_file, delimiter="/")
# あがり目 [あがりめ] /(n) (1) eyes slanted upward/(2) rising tendency/###50/
# あきたこまち /(n) Akitakomachi (variety of rice)/###3290/

		#allows me to use the kanjithing
		global RTKKanji
		RTKKanji = pickle.load((open( rtkPicklePath, "rb" )))
		#('kanji', 'heisigold', 'heisig2010', 'keyword'),
							
		count = 0
		
		for i in reader:
			
			percentOfTotal = i[len(i)-2][3:len(i[len(i)-2])] #maybe -2
			possibleP = i[len(i)-3]
			
			print str(count) + ' / ' + filelength
			count = count + 1
			
			#detect if kanji and save them
			firstfield = i[0]
			kanjis = []
			kanjis = re.findall(ur'[\u4e00-\u9fbf]', unicode(firstfield))
			
			
			#disable this to enable all word, not just kanji words
			if len(kanjis) == 0:
				continue
			
			if re.findall('九六',''.join(i)):
				print 'HERE I AM'
			
			#get the most difficult kanji according to heisig
			hardestKanji = getHardestKanji(kanjis)
			
			if hardestKanji  == None:
				continue
			
			
			#strip readings
			expression = re.findall(ur'(.*) \[.*', unicode(firstfield))[0]
		
			#skip dupes
# 			if expression in edictDict:
# 				if edictDict[expression]['pFlag']:
# 					continue
			
			
			
			#if there is a reading get it, else its the expression
			reading = re.findall(ur'.*\[(.*)\]', unicode(firstfield))[0]
			if not reading:
				reading = expression
			meaning = unicode(','.join(i[1:len(i)-2])) #maybe more minus.....
				
			print possibleP
			popular = re.findall(ur'\(P\)', possibleP)
			if popular:
				popular = 1
				meaning = '(P)' + meaning
			else:
				popular = 0
				
				#{'one': 1, 'two': 2, 'three': 3}
				
			
			#percentOfTotal, expression, reading , meaning, popular, kanjis[])
			entry = {'expression': expression , 'reading':reading, 'meaning':meaning, 'kanjis':kanjis, 'percentOfTotal':float(percentOfTotal), 'P':popular}
			
			
			for k in kanjis:
				if k not in kanjiBestWordDict: 
					kanjiBestWordDict[k] = entry
				elif kanjiBestWordDict[k]['P'] == 0 and entry['P'] == 1:
					kanjiBestWordDict[k] = entry
				elif kanjiBestWordDict[k]['percentOfTotal'] < entry['percentOfTotal']:
					kanjiBestWordDict[k] = entry
					

		
			if hardestKanji not in kanjiBestWordLearnerDict: 
				kanjiBestWordLearnerDict[hardestKanji] = entry
			elif kanjiBestWordLearnerDict[hardestKanji]['P'] == 0 and entry['P'] == 1:
				kanjiBestWordLearnerDict[hardestKanji] = entry
			elif kanjiBestWordLearnerDict[hardestKanji]['percentOfTotal'] < entry['percentOfTotal']:
				kanjiBestWordLearnerDict[hardestKanji] = entry
					
								
			edictDict[expression] = entry
		pickle.dump(edictDict, open( edictPicklePath, "wb" ), -1)
		pickle.dump(kanjiBestWordDict, open( bestKanjiPath, "wb" ), -1)
		pickle.dump(kanjiBestWordLearnerDict , open( bestKanjiLearnerPath, "wb" ), -1)

def readVocabfile():
	with open(DATA_PATH, 'r') as f:
		content = f.read().splitlines()
		
	for line in content:
		fieldhash = dict(zip(('exp', 'reading', 'meaning', 'grade'),
							line.split('\t')))
		#extract kanji from keyword
		kanjis = extractKanji(fieldhash['exp'].decode('utf8'))
		for kanji in kanjis:
			vocabIndex[kanji].append(fieldhash)
	


##########################################################################

def addCommonVocab(nids):
	global kanjiBestWordDict
	kanjiBestWordDict = pickle.load(open( dictToUse, "rb" ))
	
	fields = []
	
	anote=mw.col.getNote(nids[0])
	#get the fields of the first note
	for (i, f) in anote.items():
		fields.append(i)
	
	#get input/output fields from user
	src = addinfofuncts.getKeyFromList("Select field to read from", "Read relevant kanji/expression from:", fields)
	if (src is None):
		return
	
		#get input/output fields from user
	dst = addinfofuncts.getKeyFromList("Select field to write to", "Write Kanji vocabulary to:", fields)
	if (dst is None):
		return
	
	
	mw.checkpoint("Add JPVocab")
	mw.progress.start()
	#For each seleccted card
	
	####bump to file
	fileout = open(heisigWordsPath, 'w+')
	
	for nid in nids:
		note = mw.col.getNote(nid)
		srcTxt = mw.col.media.strip(note[src])
		if not srcTxt.strip():
			continue
		#Add the data to the dst field
		note[dst] = lookupVocab(srcTxt)
		#if (note[dst] == ""):
		#	note[dst] = note['Story']
		pre = '\t'.join([note['Heisig Number'], srcTxt]) + '\t' + note[dst] + '\n'
		fileout.write(re.sub('<br>|<br \>', '\t', pre))
		note.flush()
	mw.progress.finish()
	mw.reset()
	fileout.close()
	
	
def extractKanji(exp):
	#first get only the kanji
	separator = ','
	#Get only the kanji
	words = re.findall(ur'[\u4e00-\u9fbf]',unicode(exp))
	
	return words




def lookupVocab(kanjiTxt):
	#first get only the kanji
	separator = '<br>'
	words = extractKanji(kanjiTxt)
	vocabs = []
	outstr = ""
	#should just be one word but whatever
	for w in words:
		if w in kanjiBestWordDict:
			v = kanjiBestWordDict[w]
			vocabs.append(v['expression'] + '[' + v['reading'] + '] <br> ' + v['meaning'])
	outstr = separator.join(vocabs)
# 	for k in words:
# 		outstr = outstr.replace(k, "_")
	return outstr

#old	
def oldlookupVocab(wordsTxt):
	#first get only the kanji
	separator = '<br>'
	words = extractKanji(wordsTxt)
	vocabs = []
	outstr = ""
	for w in words:
		for v in vocabIndex[w]:
			vocabs.append(v['exp'].decode('utf8') + "[" + 
					v['reading'].decode('utf8') + "] <br> " + v['meaning'])
	outstr = separator.join(vocabs)
	for k in words:
		outstr = outstr.replace(k, "_")
	return outstr
		
		

	
	
def main():
	
	#createBestWordDict()
	global kanjiBestWordDict
	kanjiBestWordDict = pickle.load(open( dictToUse, "rb" ))
	print lookupVocab('六')
	
	global RTKKanji
	RTKKanji = pickle.load((open( rtkPicklePath, "rb" )))
	print getHardestKanji(['\\u5341', '\\u56db'])

if __name__ == '__main__':
	main()
else:
	
# import the main window object (mw) from ankiqt
	from aqt import mw
	from aqt.utils import showInfo
	import addinfofuncts

