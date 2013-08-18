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
import random

def bo(*args):
    print "oibayabu"

class Looper:
    
    
    def __init__(self, loopO, loopV):
        #self.recvAddr = 
        self.loopObj = loopO
        self.loopVect = loopV
        self.loopInd = 0
        self.progInd = len(loopO)
        self.grid = [[0 for i in range(16)] for j in range (16)]
        self.refgrid = [[0 for i in range(16)] for j in range (16)]
        self.prog = phrase.Progression()
        self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.prog.t = [.25 for i in range(16)]
        self.refprog = 0
        self.root = 48
        self.scale = phrase.modes["maj5"]
        self.noisy = False
        self.columnsub = []
        self.subsets = False
        self.gridzz = [0 for i in range(6)]
        self.noiselev = 2
        self.refreshing = False
        
        
        self.audioThread = 0
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", 5174))
        self.oscServSelf.addDefaultHandlers()
        self.oscServSelf.addMsgHandler("/played", self.realPlay)
        self.oscServSelf.addMsgHandler("/tester", self.tester)
        self.oscServSelf.addMsgHandler("/stop", self.stopCallback)
        self.oscServUI = OSC.OSCServer(("192.168.1.3", 8000))
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect(("192.168.1.2", 9000))
        self.stepTrack = OSC.OSCMessage()
        
        
        self.lock = threading.Lock()
        
        self.callbacks = [[0 for i in range(16)] for j in range (16)]
        self.uiThread = 0
        self.oscServUI.addDefaultHandlers()
        print "buildcheck\n\n\n"
        
        self.oscServUI.addMsgHandler("/noisy", self.noiseFlip)
        self.oscServUI.addMsgHandler("/colsel", self.colsubflip)
        
        for i in range(16):
            self.oscServUI.addMsgHandler("/step/" + str(i+1) + "/1", self.stepjump)
            print "step jumper " + str(i + 1)
            
        for i in range(16):
            self.oscServUI.addMsgHandler("/col/" + str(i+1) + "/1", self.colsub)
            print "step jumper " + str(i + 1)
        
        for i in range(5):
            self.oscServUI.addMsgHandler("/noiselev/" + str(i+1) + "/1", self.noiseLevHandler)
        
        for i in range(6):
            self.oscServUI.addMsgHandler("/gridload/" + str(i+1) + "/1", self.gridload)
        
        for i in range(6):
            self.oscServUI.addMsgHandler("/gridsave/" + str(i+1) + "/1", self.saveGrid)
            
        for i in range(16):
            for j in range(16):
                #don't need lambda functions
                self.callbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.grid, addr, stuff)
                #self.callbacks[i][j](self.grid, 1, 2, 3)
                print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("grid/"+str(i+1)+"/"+str(j+1), self.callbacks[i][j])
        print "\n\n\nbuildcheck\n\n"

    
    def realPlay(self, *args):
        print "aoibay"
        #phrase.play(lv.stableMorph(self.loopObj, self.loopVect[self.loopInd]))
#        phrase.play(phrase.transpose(self.loopObj, self.loopVect[self.loopInd]))
#        self.loopInd %= len(self.loopVect)
#        if self.progInd == len(16):     #for playing chord progs (matrix)
#            self.progInd %= len(self.loopObj)
#            self.loopInd += 1 
        with self.lock: 
            if(self.subsets):
                l = len(self.columnsub)
                self.progInd %= len(self.columnsub)
                playind = self.columnsub[self.progInd]
                
            else:
                l = 16
                self.progInd %= 16
                playind = self.progInd
            print playind, "playind"
            #turn light on for progind+1
            self.stepTrack.setAddress("/step/" + str(playind+1) + "/1")
            self.stepTrack.append(1)
            self.oscClientUI.send(self.stepTrack)
            self.stepTrack.clearData()
            phrase.play(self.prog.c[playind]) #make this more efficient turn it into a PLAYER object?
            if self.refreshing:
                self.refreshColumn(playind)
            self.loopInd += 1
            self.progInd += 1
            if len(args) > 0:
                print args[0]
        if self.noisy and self.progInd == (l-1):
            self.gridNoise(self.noiselev)
    
    def refreshColumn(self, k):
        msg = OSC.OSCMessage()
        msg.setAddress("/refresh")
        for i in len(self.grid):
            if(self.refgrid[k][i] != self.grid[k][i]):
                msg.append(self.refgrid[k][i])
                self.oscClientUI.send(msg)
                msg.clearData()
                self.grid[k][i] = self.refgrid[k][i]
        self.prog.c[k] = self.refprog.c[k]
    
    def refreshHanlder(self, addr, tags, stuff, source):
        if stuff[0] != 0:
            self.refreshing = True
            self.refprog = phrase.Progression(self.prog)
            self.refgrid = self.gridcopy(self.grid)
        else:
            self.refreshing = False   
    
    def stepjump(self, addr, tags, stuff, source):
        if stuff[0] != 0:
            self.progInd = int(addr.split("/")[2]) - 1
            print "                                jumped to " + str(self.progInd)
    
    def noiseFlip(self, addr, tags, stuff, source):
        print "                               noise flip " + str(stuff[0] == 1)
        self.noisy = (stuff[0] == 1)
    #new
    def noiseLevHandler(self, addr, tags, stuff, source):
        self.noiselev = 2 * int(addr.split("/")[2])
    
    def colsub(self, addr, tags, stuff, source):
        ind = int(addr.split("/")[2]) - 1
        if stuff[0] == 1 and ind not in self.columnsub: #do we need 2nd conditional?
            self.columnsub.append(ind)
            print "                            added " + str(ind)
        if stuff[0] == 0 and ind in self.columnsub:
            self.columnsub.remove(ind)
            print "                            removed " + str(ind)
        self.columnsub.sort()
    
    def colsubflip(self, addr, tags, stuff, source):
        print "                             gottem yo", self.progInd
        with self.lock:
            print "                             inside lock ", self.progInd
            self.subsets = (stuff[0] == 1)
            print "                             past bool", self.subsets 
            self.progInd = 0 if stuff[0] == 1 else self.columnsub[self.progInd]
            print "                      colsub ", str(self.subsets), "progind" + str(self.progind)
        
    #new       
    def gridcopy(self, *args):
        #k = self.grid if len(args) == 0 else args[0]
        print "                                len ", len(args)
        if len(args) == 0:
            k = self.grid
            print "                                uno "
        else: 
            k = args[0]
            print "                                dos "
        return [[k[j][i] for i in range(len(k))] for j in range(len(k))]
   #new 
    def gridload(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        ind = int(addr.split("/")[2]) - 1
        self.pullUpGrid(self.gridzz[ind])
    #new
    def pullUpGrid(self, grid):
        msg = OSC.OSCMessage()
        with self.lock:
            for i in range(len(grid)):
                for j in range(len(grid)):
                    msg.setAddress("/grid/"+str(i+1) +"/" + str(16-j))
                    msg.append(grid[i][j])
                    self.oscClientUI.send(msg)
                    msg.clearData()
            print "                          pre", type(grid), type(self.scale), type(self.root)
            self.prog = self.gridToProg(grid, self.scale, self.root)
            print "                          progged"
            self.grid = self.gridcopy(grid)
            
    #new
    def saveGrid(self, addr, tags, stuff, source):
        ind = int(addr.split("/")[2]) - 1
        if stuff[0] != 0:
            self.gridzz[ind] = self.gridcopy()
        else: 
            self.gridzz[ind] = 0 
    #new        
    def gridClear(self):
        self.prog = self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.pullUpGrid([[0 for i in range(16)] for j in range (16)])
    
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
        for i in range(len(grid)):
            if sum(grid[i]) == 0:
                prog.append((phrase.Chord([-1]), .25))
                continue
            else: c = phrase.Chord()
            for j in range(len(grid[i])):
                if grid[i][j] != 0:
                    c.append(notes[j])
            prog.append((c, .25))
        return prog
    
     
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
    
    #a is actually self.grid - change this later    
    def assign2(self, a, b, c):
        with self.lock:
            print c
            s = b.split("/")
            i = int(s[2])-1
            j = 16-int(s[3])
            a[i][j] = c[0]
            print "assigned " + str(c[0]) + " to " + str(i+1) +" " + str(j+1)
            self.prog.c[i] = self.colToChord(a[i], self.root, self.scale)
            print self.prog, "\n\n\n"        
        
    def gridNoise(self, k):
        print "in noise"
        with self.lock:
            print "in lock"
            l = len(self.grid)
            p = 1.0 * k / (l*l)
            msg = OSC.OSCMessage()
            #make everything 1 instead of 14 in touchOSC
            for i in range(l):
                for j in range(l):
                    if random.uniform(0, 1) < p:
                        msg.setAddress("/grid/"+str(i+1) +"/" + str(16-j))
                        if self.grid[i][j] != 0:
                            self.grid[i][j] = 0
                            msg.append(0)
                            self.oscClientUI.send(msg)
                            msg.clearData()
                        else: 
                            self.grid[i][j] = 18
                            msg.append(18)
                            self.oscClientUI.send(msg)
                            msg.clearData()
                self.prog.c[i] = self.colToChord(self.grid[i], self.root, self.scale)
            print "randomized"
            #self.prog = self.gridToProg(self.grid, self.scale, self.root) 
            
                
        
    
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
