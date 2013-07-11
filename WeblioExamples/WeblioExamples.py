# -*- coding: utf-8 -*-


import urllib2
from HTMLParser import HTMLParser
import re


from aqt import mw
from anki.hooks import addHook
from japanese.reading import mecab
import sys
import re
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
EList = collections.namedtuple('exampleList',['jap', 'eng'])

expField  = "Expression"
dstField = "Weblio Examples"
qstDst = "Weblio Questions"
infoDst = "Weblio Info"
engDst = "Weblio English"

htmlcomments = re.compile('\<![ \r\n\t]*(--([^\-]|[\r\n]|-[^\-])*--[ \r\n\t]*)\>')


#NUMBER OF EXAMPLES TO PULL
MAX_EXAMPLES = 3

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

def getExamplesold(term):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]


    #search_url = "http://dictionary.goo.ne.jp/srch/ej/"+term+"/m0u        
    search_url = "http://ejje.weblio.jp/sentence/content/" + term.encode('utf-8')
    #search_url = "http://dictionary.goo.ne.jp/freewordsearcher.html?MT="+term+"&mode=0&dict=%E8%BE%9E%E6%9B%B8%E6%A4%9C%E7%B4%A2&id=top&kind=jn"
    #get page
    results=opener.open(search_url)
    text = results.read()
    
    answers = []
    count = 0
    for item in text.split("</div>"):
        #split to examples
        if '<div class=qotC>' in item:
            if count == MAX_EXAMPLES:
                break
            count = count + 1
            stripped = item [ item.find('<div class=qotC>')+len('<div class=qotC>') : ]
            stripped = re.sub('</p><p class=qotCJE>', '\n', stripped)
            stripped = strip_tags(stripped)
            #print stripped
            #only get from this source
            #if '-Weblio Email???' in stripped:
            stripped = htmlcomments.sub('', stripped)
            stripped = re.sub('\n\n\n.*','<br>',stripped)
            stripped = re.sub('\n','<br>',stripped)
            answers.append(stripped)
    return '<br>'.join(answers)


def getExamples(term):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]


    #search_url = "http://dictionary.goo.ne.jp/srch/ej/"+term+"/m0u        
    search_url = "http://ejje.weblio.jp/sentence/content/" + term.encode('utf-8') + "?catId=business"
    #search_url = "http://dictionary.goo.ne.jp/freewordsearcher.html?MT="+term+"&mode=0&dict=%E8%BE%9E%E6%9B%B8%E6%A4%9C%E7%B4%A2&id=top&kind=jn"
    #get page
    try:
        results=opener.open(search_url)
        text = results.read()
    except Exception, e:
        text = ""
    
    
    answers = parseanswer(text, term)
    
    #if (len(answers) < MAX_EXAMPLES):        
    #        search_url = "http://ejje.weblio.jp/sentence/content/" + term.encode('utf-8')
    #        #get page
    #        results=opener.open(search_url)
    #        text = results.read()
    #        answers = answers + (parseanswer(text, term))
            
    #take top x answers
    answers = answers[:MAX_EXAMPLES]
    return answers
       
    
def getInfo(term):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]

    
    search_url = "http://www.sanseido.net/User/Dic/Index.aspx?TWords="+ term.encode('utf-8')+"&st=0&DORDER=&DailyJJ=checkbox"
    
    #get page
    try:
        results=opener.open(search_url)
        text = results.read()
    except Exception, e:
        return ""
    
    #print text
    #results = re.match('(.*)tweetface',text)
    
    results = re.findall('<!-- <div id="wordDetailBorder"></div> -->(.*)<div id="tweetface">',text, re.S)
    results = re.sub('<img.*', '', results[0])
    
    return str(results)
    
def parseanswer(text, term):
    answers = []
    japA = []
    engA = []
    jap = eng = None
    for item in text.split("</div>"):
        #split to examples
                if ('<div class=qotC>' in item) and (term.encode('utf-8') in item):
                    stripped = item [ item.find('<div class=qotC>')+len('<div class=qotC>') : ]
                    stripped = re.findall('<p class=qotCJJ>(.*?)</p>.*?<p class=qotCJE>(.*?)<',stripped)
                    for jap, eng in stripped:
                        #print jap 
                        #print eng
                        
                        #answers.append(strip_tags(jap)+"<br>"+strip_tags(eng))
                        japA.append(strip_tags(jap))
                        engA.append(strip_tags(eng))
    japA = japA[:MAX_EXAMPLES]
    engA = engA[:MAX_EXAMPLES]
    return EList(japA, engA)


def onFocusLost(flag, note, fidx):
    
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
    #    return flag

    # event coming from src field?
    if fidx != None and fidx != srcIdx:
        return flag
    
    if note[dst]:
        return flag
    
    srcTxt = mw.col.media.strip(note[src])
    srcTxt = strip_tags(srcTxt)
    if not srcTxt.strip():
        return flag
        
    #start mecab translator
    #mecab = japanese.reading.MecabController()
    global mecab
    #Add the data to the dst field
    
    try:
        japR, engR = getExamples(srcTxt)
        #sys.stderr.write("got jap:" +'<br>'.join(japR))
        #sys.stderr.write("got eng:" +'<br>'.join(engR))
    except Exception, e:
            raise
    
    #results #array of "jap" and "eng" hashs
    
    Examples = mecab.reading(('<br>'.join(japR)).decode('utf-8'))
    Questions = makeQuestions(srcTxt, ('<br>'.join(japR)).decode('utf-8'))
    English = ('<br>'.join(engR)).decode('utf-8')
    
    
    
    try:
        result = Examples
    except Exception, e:
            mecab = None
            raise	
    
    note[dstField] = result
    #next make question
    #check if the fields exist
    dst = None
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        if name == qstDst:
            dst = qstDst
    if not src or not dst:
        return True
    if note[dst]:
        return True
    try:
        note[dst] = Questions
    except Exception, e:
            mecab = None
            raise
    
    ##add english
    dst = None
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        if name == engDst:
            dst = engDst
    if not src or not dst:
        return True
    if note[dst]:
        return True
    try:
        note[dst] = English
    except Exception, e:
            mecab = None
            raise
    
    
    
        #next get info
    #check if the fields exist
    dst = None
    for c, name in enumerate(mw.col.models.fieldNames(note.model())):
        if name == infoDst:
            dst = infoDst
    if not src or not dst:
        return True
    if note[dst]:
        return True
    try:
        note[dst] = getInfo(srcTxt).decode('utf-8')
    except Exception, e:
            raise
    return True
    
    #return flag

def makeQuestions(term, sentence):
    #sys.stderr.write("Trying to search on: " +term)
    #sys.stderr.write("\n" + sentence)
    return re.sub(term, "___", sentence)
    
    
def onBulkadd(browser):
    nids = browser.selectedNotes()
    for nid in nids:
        note = mw.col.getNote(nid)
        onFocusLost(False, note, None)
        note.flush()
    mw.progress.finish()
    mw.reset()
        
    
addHook('editFocusLost', onFocusLost)


def setupMenu(browser):
    a = QAction("Add Weblio Examples", browser)
    browser.connect(a, SIGNAL("triggered()"), lambda e=browser: onBulkadd(e))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


addHook("browser.setupMenus", setupMenu)


