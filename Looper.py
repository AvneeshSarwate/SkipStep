'''
Created on Jun 12, 2013

@author: avneeshsarwate
'''
import phrase
import Levenshtein as lv
import threading
import OSC
import time
import thread

def bo(*args):
    print "oibayabu"

class Looper:
    
    def realPlay(self, *args):
        print "aoibay"
        #phrase.play(lv.stableMorph(self.loopObj, self.loopVect[self.loopInd]))
#        phrase.play(phrase.transpose(self.loopObj, self.loopVect[self.loopInd]))
#        self.loopInd %= len(self.loopVect)
#        if self.progInd == len(16):     #for playing chord progs (matrix)
#            self.progInd %= len(self.loopObj)
#            self.loopInd += 1 
        lock = threading.Lock()
        lock.acquire()
        self.progInd %= 16
        print self.progInd, "progInd"
        phrase.play(self.prog.c[self.progInd])
        self.loopInd += 1
        self.progInd += 1
        if len(args) > 0:
            print args[0]
        lock.release()
    
    def stopCallback(self):
        self.oscServSelf.close()
        self.audioThread.join()
        
    def playStart(self):
        self.audioThread = threading.Thread(target=self.oscServSelf.serve_forever)
        self.audioThread.start()
        self.realPlay()
    
    def uiStart(self):
        self.uiThread = threading.Thread(target=self.oscServUI.serve_forever)
        self.uiThread.start()
    
    def oi(self, addr, tags, stuff, source):
        print "yo"
    
    def loopStart(self):
        try :
            print "starting loop"
            while 1 :
                continue

        except KeyboardInterrupt :
            print "\nClosing oscServSelf."
            self.oscServSelf.close()
            self.oscServUI.close()
            print "Waiting for Server-thread to finish"
            if self.audioThread != 0:
                self.audioThread.join() ##!!!
            if self.uiThread != 0:
                self.uiThread.join() ##!!!
            print "Done"
    
    def tester(self, *args):
        print "hurr"
    
    def default(self, *args):
        print "default"
    
    def check(self):
        for addr in self.oscServSelf.getOSCAddressSpace():
            print addr
        for addr in self.oscServUI.getOSCAddressSpace():
            print addr
    
    def gridToProg(self, grid, scale, root):
        notes = self.scaleNotes(root, scale)
        prog = phrase.Progression()
        for i in len(grid):
            if sum(grid[i]) == 0:
                prog.append((phrase.Chord([-1]), .25))
                continue
            else: c = phrase.Chord()
            for j in len(grid[i]):
                if grid[i][j] != 0:
                    c.append(notes[j])
            prog.append((c, .25))
    
     
    def scaleNotes(self, root, scale):
        notes = [0]*16
        for i in range(16):
            notes[i] = root + (i/len(scale))*12 + scale[i%len(scale)] 
#            print i, (i/len(scale))*12, i%len(scale)
        return notes 
        
    def colToChord(self, col, root, scale):
        notes = self.scaleNotes(root, scale)
        if sum(col) == 0:
#            print "zero"
            return phrase.Chord([-1])
        else: 
            c = phrase.Chord()
            for j in range(len(col)):
                if col[j] != 0:
                    c.append(notes[j])
        return c
        
    def assign2(self, a, b, c):
        lock = threading.Lock()
        lock.acquire()
        print c
        s = b.split("/")
        i = int(s[2])-1
        j = 16-int(s[3])
        a[i][j] = c[0]
        print "assigned " + str(c[0]) + " to " + str(i+1) +" " + str(j+1)
        self.prog.c[i] = self.colToChord(a[i], 48, phrase.modes["maj5"])
        print self.prog, "\n\n\n"
        lock.release()
        
    def __init__(self, loopO, loopV):
        #self.recvAddr = 
        self.loopObj = loopO
        self.loopVect = loopV
        self.loopInd = 0
        self.progInd = len(loopO)
        self.grid = [[0 for i in range(16)] for j in range (16)]
        self.prog = phrase.Progression()
        self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.prog.t = [.25 for i in range(16)]
        
        self.audioThread = 0
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", 5174))
        self.oscServSelf.addDefaultHandlers()
        self.oscServSelf.addMsgHandler("/played", self.realPlay)
        self.oscServSelf.addMsgHandler("/tester", self.tester)
        self.oscServSelf.addMsgHandler("/stop", self.stopCallback)
        self.oscServUI = OSC.OSCServer(("10.76.205.109", 8000))
        
        self.callbacks = [[0 for i in range(16)] for j in range (16)]
        self.uiThread = 0
        self.oscServUI.addDefaultHandlers()
        print "buildcheck\n\n\n"
        for i in range(16):
            for j in range(16):
                self.callbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.grid, addr, stuff)
                #self.callbacks[i][j](self.grid, 1, 2, 3)
                print "wat"
                self.oscServUI.addMsgHandler("grid/"+str(i+1)+"/"+str(j+1), self.callbacks[i][j])
        print "\n\n\nbuildcheck\n\n"

n = [60, 62, 64, 65]
t = [1, 1, 1, 1]
p = phrase.Phrase(n, t)
trans = [1, 2, 5, 1]

loop = Looper(p, trans)
loop.check()
time.sleep(2)
loop.uiStart()
loop.playStart()
loop.loopStart()
