'''
Created on Nov 10, 2013

@author: avneeshsarwate
'''

import phrase
import Levenshtein as lv
import threading
import OSC
import time
import thread
import random
import cPickle
import copy

class Looper:

    def __init__(self):
        #self.recvAddr = 
        self.loopInd = 0
        self.progInd = 0#len(loopO)
        self.grid = [[0 for i in range(16)] for j in range (16)]
        self.refgrid = [[0 for i in range(16)] for j in range (16)]
        self.pianogrid = [[0 for i in range(16)] for j in range (16)]
        self.prog = phrase.Progression()
        self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.prog.t = [.25 for i in range(16)]
        self.pianoprog = phrase.Progression()
        self.pianoprog.c = [phrase.Chord([-1]) for i in range(16)]
        self.pianoprog.t = [.25 for i in range(16)]
        self.customScale = []
        self.refprog = 0
        self.root = 48
        self.scale = phrase.modes["maj5"]
        self.noisy = False
        self.columnsub = []
        self.subsets = False
        self.gridzz = [0 for i in range(8)]
        self.noiselev = 2
        self.refreshing = False
        self.arrowToggle = False
        self.stepIncrement = 1
        self.noiseInd = 1
        self.undoStack = []
        
        self.lock = threading.Lock()

class MultiLoop:
    
    
    def __init__(self, n):
        #self.recvAddr = 
        
        self.num = n
        self.gridStates = []
        for i in range(n):
            self.gridStates.append(Looper())
        
        
        self.audioThread = 0
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", 50505)) #LANdini 50505, 5174 chuck
        self.oscServSelf.addDefaultHandlers()
        self.oscServSelf.addMsgHandler("/played", self.realPlay)
        self.oscServSelf.addMsgHandler("/tester", self.tester)
        self.oscServSelf.addMsgHandler("/stop", self.stopCallback)
        self.oscServUI = OSC.OSCServer(("169.254.214.184", 8000))
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect(("169.254.133.162", 9000))
        self.oscLANdiniClient = OSC.OSCClient()
        self.oscLANdiniClient.connect(("127.0.0.1", 50506))
        self.touchClient = OSC.OSCClient()
        self.touchClient.connect( ('127.0.0.1', 6449) )
        self.stepTrack = OSC.OSCMessage()
        
        
        self.gridcallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        self.pianocallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        self.uiThread = 0
        self.oscServUI.addDefaultHandlers()
        #print "buildcheck\n\n\n"
        
        for k in range(n):
        
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/noisy", self.noiseFlip)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/colsel", self.colsubflip)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/piano", self.pianoModeOn)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/refresh", self.refreshHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/scaleApply", self.applyCustomScale)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/up", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/down", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/left", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/right", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/arrowToggle", self.arrowTogHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/clear", self.gridClear)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/save", self.saveGridtoFile)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/load", self.loadGridFromFile)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiseHit", self.noiseHit)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/undo", self.undo)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/tempo", self.tempo)
            
            
            
            #need to add everything for moving piano mode grid back to main 
            
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/step/" + str(i+1) + "/1", self.stepjump)
                #print "step jumper " + str(i + 1)
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/pianoKey/" + str(i+1) + "/1", self.pianoKey)
                
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/col/" + str(i+1) + "/1", self.colsub)
                #print "step jumper " + str(i + 1)
            
            for i in range(5):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiselev/" + str(i+1) + "/1", self.noiseLevHandler)
            
            for i in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/gridload/" + str(i+1) + "/1", self.gridload)
            
            for i in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/gridsave/" + str(i+1) + "/1", self.saveGrid)
                
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/custScale/" + str(i+1) + "/1", self.custScale)
                
            for i in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiseSel/" + str(i+1) + "/1", self.noiseSelector)
            
            for i in range(16):
                for j in range(16):
                    self.gridcallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].grid, addr, stuff, self.gridStates[int(addr.split("/")[1])-1].prog)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/grid/"+str(i+1)+"/"+str(j+1), self.gridcallbacks[k][i][j])
            
            for i in range(16):
                for j in range(16):
                    
                    self.pianocallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[k].pianogrid, addr, stuff, self.gridStates[k].pianoprog)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/pianoGrid/"+str(i+1)+"/"+str(j+1), self.pianocallbacks[k][i][j])
            
            #print "\n\n\nbuildcheck\n\n"

    
    def realPlay(self, *args):
        ##print "aoibay"
        #phrase.play(lv.stableMorph(self.loopObj, self.loopVect[self.loopInd]))
#        phrase.play(phrase.transpose(self.loopObj, self.loopVect[self.loopInd]))
#        self.loopInd %= len(self.loopVect)
#        if self.progInd == len(16):     #for playing chord progs (matrix)
#            self.progInd %= len(self.loopObj)
#            self.loopInd += 1 

        chords = []
        for si in range(self.num):
            with self.gridStates[si].lock: 
                if(self.gridStates[si].subsets):
                    l = len(self.gridStates[si].columnsub)
                    self.gridStates[si].progInd %= len(self.gridStates[si].columnsub)
                    playind = self.gridStates[si].columnsub[self.gridStates[si].progInd]
                    
                else:
                    l = 16
                    self.gridStates[si].progInd %= 16
                    playind = self.gridStates[si].progInd
                #print playind, "playind", self.prog.c[playind].n
                #turn light on for progind+1
                self.stepTrack.setAddress("/" + str(si+1) + "/step/" + str(playind+1) + "/1")
                self.stepTrack.append(1)
                self.oscClientUI.send(self.stepTrack)
                self.stepTrack.clearData()
                ##print "in play"
                chords.append(self.gridStates[si].prog.c[playind]) # self.prog.c[playind] make this more efficient turn it into a PLAYER object?
                if self.gridStates[si].refreshing:
                    ##print "                                   refresh", playind
                    self.refreshColumn(playind, si)
                self.gridStates[si].loopInd += 1
                self.gridStates[si].progInd += self.gridStates[si].stepIncrement
            if self.gridStates[si].noisy and ((self.gridStates[si].progInd == l) or(self.gridStates[si].progInd == -1)):
                self.noiseChoice(si)
                #self.gridNoise(self.noiselev)
                #print                               noise at", l
        phrase.play(chords[0], chords[1], chords[2])
            
    
    def refreshColumn(self, k, si):
        msg = OSC.OSCMessage()
        
        for i in range(len(self.gridStates[si].grid)):
            if(self.gridStates[si].refgrid[k][i] != self.gridStates[si].grid[k][i]):
                #print "                            single element refresh", k+1, i+1, self.refgrid[k][i]
                msg.setAddress("/grid/" + str(k+1) + "/" + str(16-i))
                msg.append(self.gridStates[si].refgrid[k][i])
                self.oscClientUI.send(msg)
                msg.clearData()
                self.gridStates[si].grid[k][i] = self.gridStates[si].refgrid[k][i]
        self.gridStates[si].prog.c[k] = self.gridStates[si].refprog.c[k]
    
    def refreshHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        #print "                     hit ref handler", stuff, stuff[0] != 0
        if stuff[0] != 0:
            #print "                    in conditional"
            self.gridStates[si].refreshing = True
            self.gridStates[si].refprog = phrase.Progression(self.gridStates[si].prog)
            #print type(self.refprog), "refprog", "before"
            self.gridStates[si].refgrid = self.gridcopy(self.gridStates[si].grid)
            #print len(self.prog), ":prog", len(self.refprog), ":refprog"
            print "                           refresh on"
        else:
            self.gridStates[si].refreshing = False
            print "                           refresh off"   
    
    def stepjump(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] != 0:
            self.gridStates[si].progInd, j = self.gridAddrInd(addr) #replace with gridAddrInd
            if self.gridStates[si].subsets:
                if self.gridStates[si].progInd in self.gridStates[si].columnsub:
                    self.gridStates[si].progInd = self.gridStates[si].columnsub.index(self.gridStates[si].progInd)
                else:
                    if self.gridStates[si].progInd > self.gridStates[si].columnsub[-1]:
                        self.gridStates[si].progInd = len(self.gridStates[si].columnsub) - 1
                        return
                    i = len(self.gridStates[si].columnsub) - 1
                    while self.gridStates[si].columnsub[i] >= self.gridStates[si].progInd:
                        self.gridStates[si].progInd = self.gridStates[si].columnsub[i]
                        i -= 1
                    
            print "                                jumped to " + str(self.gridStates[si].progInd)
    
    def noiseFlip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        print "                               noise flip " + str(stuff[0] == 1)
        self.gridStates[si].noisy = (stuff[0] == 1)
    #new
    def noiseLevHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        i, j = self.gridAddrInd(addr)
        self.gridStates[si].noiselev = 2 * i
    
    def colsub(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        ind, j = self.gridAddrInd(addr) #replace with gridAddrInd
        if stuff[0] == 1 and ind not in self.gridStates[si].columnsub: #do we need 2nd conditional?
            self.gridStates[si].columnsub.append(ind)
            print "                            added " + str(ind)
        if stuff[0] == 0 and ind in self.gridStates[si].columnsub:
            self.gridStates[si].columnsub.remove(ind)
            print "                            removed " + str(ind)
        self.gridStates[si].columnsub.sort()
    
    def colsubflip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        #print "                             gottem yo", self.progInd
        with self.gridStates[si].lock:
            #print "                             inside lock ", self.progInd
            self.gridStates[si].subsets = (stuff[0] == 1)
            #print "                             past bool", self.subsets 
            self.gridStates[si].progInd = 0 if stuff[0] == 1 else self.gridStates[si].columnsub[self.gridStates[si].progInd]
            print "                      colsub ", str(self.gridStates[si].subsets), "progind" + str(self.gridStates[si].progind)
        
    #new       
    def gridcopy(self, *args):
        #k = self.grid if len(args) == 0 else args[0]
        #print "                                len ", len(args)
        if len(args) == 0:
            k = self.grid
            #print "                                uno "
        else: 
            k = args[0]
            #print "                                dos "
        return [[k[j][i] for i in range(len(k))] for j in range(len(k))]
    #new
    def saveGrid(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        ind, j = self.gridAddrInd(addr)
        if stuff[0] != 0:
            self.gridStates[si].gridzz[ind] = self.gridKeyToString(self.gridStates[si].grid, self.gridStates[si].scale)#self.gridStates[si].gridcopy()
        else: 
            self.gridStates[si].gridzz[ind] = 0 
    #new 
    def gridload(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        ind, j = self.gridAddrInd(addr)#int(addr.split("/")[2]) - 1
        grid, scale = self.stringToGridKey(self.gridStates[si].gridzz[ind])
        self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
        self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
        self.gridStates[si].customScale = [1+i for i in scale]
        self.gridStates[si].grid = grid
        self.gridStates[si].scale = scale
        self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
    #new
    def pullUpGrid(self, grid, gridAddr):
        msg = OSC.OSCMessage()
        print "pullup outside lock"
        #with self.lock:
        print "updating grid of", gridAddr
        for i in range(len(grid)):
            for j in range(len(grid)):
                msg.setAddress(gridAddr + "/"+str(i+1) +"/" + str(16-j))
                msg.append(grid[i][j])
                self.oscClientUI.send(msg)
                msg.clearData()
    
    def pullUpScale(self, scale, scaleAddr):
        print "           ", scale 
        msg = OSC.OSCMessage()
        for i in range(12):
            msg.clearData()
            msg.setAddress(scaleAddr + "/"+ str(i+1) +"/1" )
            if i in scale:
                msg.append(1)
            else:
                msg.append(0)
            self.oscClientUI.send(msg)
                
                 
            
    def pianoModeOn(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        #switch tab to piano mode tab
        if(stuff[0] == 0):
            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            self.oscServSelf.addMsgHandler("/played", self.realPlay)
            self.realPlay()
            return
        print "                      going to piano mode"
        self.stopCallback()
        print "                      stop callback returned"
        msg = OSC.OSCMessage()
        msg.setAddress("/3")
        #msg.append(1)
        self.oscClientUI.send(msg)
        self.gridStates[si].pianogrid = self.gridcopy(self.gridStates[si].grid)
        self.gridStates[si].pianoprog = self.gridToProg(self.gridStates[si].pianogrid, self.gridStates[si].scale, self.gridStates[si].root)
        self.pullUpGrid(self.gridStates[si].pianogrid, "/" +str(si+1) + "/pianoGrid")
        #hanlders for "piano keys" should already be set up
        return
    #SHOULD PIANO GRID BE EDITABLE AND SHOULD EDITS UPDATE TO MAIN GRID
    
    #set up handler using lambda functions like with normal grid 
    def pianoKey(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        i, j = self.gridAddrInd(addr)
        print i
        if(stuff[0] == 1):
            #print "piano on"
            phrase.play(self.gridStates[si].pianoprog.c[i], toggle="on")
        else:
            #print "piano off"
            phrase.play(self.gridStates[si].pianoprog.c[i], toggle="off")
    
    def applyCustomScale(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0:
            return
        with self.gridStates[si].lock:
            custScale = [i - min(self.gridStates[si].customScale) for i in self.gridStates[si].customScale]
            custScale.sort()
            print custScale
            self.gridStates[si].scale = custScale
            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, custScale, self.gridStates[si].root)
    
    def custScale(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        i, j = self.gridAddrInd(addr)
        if(stuff[0] != 0):
            self.gridStates[si].customScale.append(i)
            print "                added note to scale", i 
        else:
            if i in self.gridStates[si].customScale:
                self.gridStates[si].customScale.remove(i)
                print "                removed note from scale", i
    
    #new        
    def gridClear(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        self.gridStates[si].prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.gridStates[si].grid = [[0 for i in range(16)] for j in range (16)]
        self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
        
    
    def stopCallback(self):
        #self.oscServSelf.close() #do we need to close server? probs not
        self.oscServSelf.delMsgHandler("/played")
        print "                    thread closed"
        #self.audioThread.join()
        
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
            #print "starting loop"
            while 1 :
                continue

        except KeyboardInterrupt :
            #print "\nClosing oscServSelf."
            self.oscServSelf.close()
            self.oscServUI.close()
            #print "Waiting for Server-thread to finish"
            if self.audioThread != 0:
                self.audioThread.join() ##!!!
            if self.uiThread != 0:
                self.uiThread.join() ##!!!
            #print "Done"
    
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
    
    def arrowTogHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        self.gridStates[si].arrowToggle = (stuff[0] == 1)
    
    def gridShift(self, g, direction):
        grid = self.gridcopy(g)
        
        if direction == "up":
            print "up"
            for i in range(len(grid)):
                grid[i].insert(0, grid[i].pop())            
                    
        if direction == "down":
            for i in range(len(grid)):
                grid[i] = grid[i][1:len(grid[i])] + [grid[i][0]]
                    
        if direction == "right":
            grid.insert(0, grid.pop())
        
        if direction == "left": 
            grid = grid[1:len(grid)] + [grid[0]]
        
        return grid
    
    def gridShiftHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0:
            return
        direction = addr.split("/")[2]
        print "                   direction:", direction
        if(self.gridStates[si].arrowToggle):
            if direction == "left":
                self.gridStates[si].stepIncrement = -1
            if direction == "right":
                self.gridStates[si].stepIncrement = 1
            if direction == "up":
                self.gridStates[si].root += 1
                with self.gridStates[si].lock:
                    self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            if direction == "down":
                self.gridStates[si].root -= 1
                with self.gridStates[si].lock:
                    self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
                    
        else:
            print "normal grid before", self.gridSum(self.gridStates[0].grid), self.gridSum(self.gridStates[1].grid), self.gridSum(self.gridStates[2].grid)
            g = self.gridShift(self.gridStates[si].grid, direction)
            print "si", si, direction, sum([sum(k) for k in self.gridStates[si].grid]), sum([sum(i) for i in g])
            print self.gridStates[si].grid
            with self.gridStates[si].lock:
                self.gridStates[si].grid = g
                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
            
    
    def scaleNotes(self, root, scale):
        notes = [0]*16
        for i in range(16):
            notes[i] = root + (i/len(scale))*12 + scale[i%len(scale)] 
#            #print i, (i/len(scale))*12, i%len(scale)
        return notes 
        
    def colToChord(self, col, root, scale):
        notes = self.scaleNotes(root, scale)
        if sum(col) == 0:
#            #print "zero"
            return phrase.Chord([-1])
        else: 
            c = phrase.Chord()
            for j in range(len(col)):
                if col[j] != 0:
                    c.append(notes[j])
        return c
    
    def gridAddrInd(self, addr):
        s = addr.split("/")
        i = int(s[3])-1
        j = 16-int(s[4])
        return i, j
        
    def indToUIInd(self, i, j):
        return i+1, 16-j
    def gridSum(self, grid):
        return sum([sum(k) for k in grid])
    
    #a - grid, b - addr, c - stuff, d - prog  
    def assign2(self, a, b, c, d):
        si = int(b.split("/")[1]) - 1 #index of grid action was taken on
        print si 
        with self.gridStates[si].lock:
            #print c
#            s = b.split("/")
#            i = int(s[2])-1
#            j = 16-int(s[3])
            i, j = self.gridAddrInd(b)
            a[i][j] = c[0]
            print "grid count", self.gridSum(a)
            print "          assigned " + str(c[0]) + " to " + str(i+1) +" " + str(16-j), sum(a[i]) #correct?
            if d == 0: 
                print "no prog"
                return
            d.c[i] = self.colToChord(a[i], self.gridStates[si].root, self.gridStates[si].scale)
            #print self.prog, "\n\n\n"        
    
    def saveGridtoFile(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        with self.gridStates[si].lock:
            filename = raw_input("Set Name: ")
            savefile = open(filename +".ss", "w")
            savestr = []
            savestr.append(self.gridKeyToString(self.gridStates[si].grid, self.gridStates[si].scale))
            for i in self.gridStates[si].gridzz:
                if i != 0:
                    savestr.append(i)
            print savestr
            savefile.write("\n".join(savestr))
            savefile.close()
        
    
    def loadGridFromFile(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        with self.gridStates[si].lock:
            filename = raw_input("File Name: ")
            filestr = open(filename).read()
            gridstrs = filestr.split("\n")
            #print gridstrs[0]
            grid, scale = self.stringToGridKey(gridstrs[0])
            self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
            self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
            self.gridStates[si].customScale = [1+i for i in scale]
            self.gridStates[si].grid = grid
            self.gridStates[si].scale = scale
            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            for i in range(1, len(gridstrs)):
                print gridstrs[i]
                self.gridStates[si].gridzz[i-1] = gridstrs[i]
                msg = OSC.OSCMessage()
                msg.setAddress("/gridsave/" + str(i) + "/1")
                msg.append(1)
                self.oscClientUI.send(msg)
                msg.clearData()
    
    def gridKeyToString(self, grid, key):
        strgrid = [[str(grid[i][j]) for i in range(len(grid))] for j in range(len(grid))]
        colstr = [",".join(strgrid[i]) for i in range(len(strgrid))]
        gridstring = ";".join(colstr)
        
        strkey = [str(i) for i in key]
        keystr = ",".join(strkey)
        return gridstring + "+" + keystr
    
    def stringToGridKey(self, string): #rename 
        gridstring = string.split("+")[0]
        colstr = gridstring.split(";")
        strgrid = [i.split(",") for i in colstr]
        grid = [[round(float(strgrid[i][j])) for i in range(len(strgrid))] for j in range(len(strgrid))]
        
        keystr = string.split("+")[1]
        strkey = keystr.split(",")
        key = [int(i) for i in strkey]
        return grid, key
        
        
    def neighborCount(self, grid, i, j):
        count = 0
        for m in [-1, 0, 1]:
            for k in [-1, 0, 1]:
                if abs(m) + abs(k) == 0:
                    continue
                if grid[(i+m)%len(grid)][(j+k)%len(grid)] != 0:
                    count += 1
        return count       
        
    def gameOfLife(self, oldG):
        newG = [[0 for i in range(len(oldG))] for j in range(len(oldG))]
        for i in range(len(oldG)):
            for j in range(len(oldG)):
                c = self.neighborCount(oldG, i, j)
                if c < 2 or c > 3:
                    newG[i][j] = 0
                if c in [2, 3]:
                    newG[i][j] = oldG[i][j]
                if c == 3:
                    newG[i][j] = 1
        return newG
        
    def blend(self, grid1, grid2, direction, amount):
        blend = [[0 for i in range(len(grid1))] for j in range (len(grid1))]
        allslots = range(len(grid1))
        set1 = []
        for i in range(amount):
            k = random.choice(allslots)
            allslots.remove(k)
            set1.append(k)
        if direction == "hor":  #blending columns  
            for i in range(len(grid1)):
                if i in set1:
                    blend[i] = copy.copy(grid1[i])
                else:
                    blend[i] = copy.copy(grid2[i])
        if direction == "vert":
            for i in range(len(grid1)):
                if i in set1:
                    for j in range(len(grid1)):
                        blend[j][i] = grid1[j][i]
                else:
                    for j in range(len(grid1)):
                        blend[j][i] = grid2[j][i]
        return blend
    
    def smartNoise(self, grid, si):
        newgrid = [[0 for i in range(16)] for j in range (16)]
        vert = [i for i in range(1, 6)] + [i for i in range(-5, 0)]
        hor = [i for i in range(1, 4)] + [i for i in range(-3, 0)]
        v = random.choice(vert)
        h = random.choice(hor)
        for i in range(len(grid)):
            for j in range(len(grid)):
                if grid[i][j] != 0:
                    if random.uniform(0, 1) < (1.0 * self.gridStates[si].noiselev) / 20: #if any change happens
                        if random.uniform(0, 1) < .2: #probability of add/remove
                            if random.uniform(0, 1) < .5:
                                newgrid[i][j] = 0
                            else:
                                newgrid[(i+h)%len(grid)][(j+v)%len(grid)] = 1
                        else:
                            newgrid[i][(j+v)%len(grid)] = 1 
                    else:
                        newgrid[i][j] = 1
        return newgrid
                        
    def noiseSelector(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1])  - 1 #index of grid action was taken on
        i, j = self.gridAddrInd(addr)
        print i+1, "noise selector"
        self.gridStates[si].noiseInd = i+1
    
    def noiseHit(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        self.noiseChoice(si)
        
    
    def simplify(self, grid, voices):
        sets = [[] for i in range(len(grid))]
        newG = [[0 for i in range(16)] for j in range (16)]
        for i in range(len(grid)):
            for j in range(len(grid)):
                if grid[i][j] != 0:
                    sets[i].append(j)
        for i in range(len(sets)):
            for j in range(voices):
                if len(sets[i]) == 0: break
                k = random.choice(sets[i])
                newG[i][k] = 1
                sets[i].remove(k)
        return newG
    
    def noiseChoice(self, si):
        self.gridStates[si].undoStack.append(self.gridcopy(self.gridStates[si].grid))
        print "the noise that was selected was", self.gridStates[si].noiseInd
        if self.gridStates[si].noiseInd == 1:
            self.gridNoise(self.gridStates[si].noiselev, si)
            return
        if self.gridStates[si].noiseInd == 2:
            with self.gridStates[si].lock:
                self.gridStates[si].grid = self.smartNoise(self.gridStates[si].grid, si)
                self.pullUpGrid(self.gridStates[si].grid, "/" + str(si+1) + "/grid")
                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            return
        if self.gridStates[si].noiseInd == 3:
            print "game of life chosen"
            g = self.gridcopy(self.gridStates[si].grid)
            for i in range(self.gridStates[si].noiselev/2):
                g = self.gameOfLife(g)
                print "iteration number", i, "diff", self.gridDif(g, self.gridStates[si].grid)
            with self.gridStates[si].lock:
                self.gridStates[si].grid = g
                self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            return  
        if self.gridStates[si].noiseInd == 4:
            g = self.simplify(self.gridStates[si].grid, self.gridStates[si].noiselev/2)
            with self.gridStates[si].lock:
                self.gridStates[si].grid = g
                self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            return   
    
    def tempo(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print "sent touch message"
        msg = OSC.OSCMessage()
        msg.setAddress("/touch")
        msg.append("touched")
#        msg.setAddress("/send/GD")
#        msg.append("all")
#        msg.append("/touch")
#        msg.append("stuff")
        self.touchClient.send(msg)
        
    
    def undo(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0 or len(self.gridStates[si].undoStack) == 0: return
        with self.gridStates[si].lock:
            self.gridStates[si].grid = self.gridStates[si].undoStack.pop()
            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
            self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
     
    def gridDif(self, g1, g2):
        hamming = 0
        for i in range(len(g1)):
            for j in range(len(g1)):
                if (g1[i][j] != 0 and g2[i][j] == 0) or (g1[i][j] == 0 and g2[i][j] != 0): #both not zero or both zero
                    hamming += 1
        return hamming
    
    def gridNoise(self, k, si):
        #print "in noise"
        with self.gridStates[si].lock:
            #print "in lock"
            l = len(self.gridStates[si].grid)
            p = 1.0 * k / (l*l)
            msg = OSC.OSCMessage()
            #make everything 1 instead of 14 in touchOSC
            for i in range(l):
                for j in range(l):
                    if random.uniform(0, 1) < p:
                        msg.setAddress("/grid/"+str(i+1) +"/" + str(16-j))
                        if self.gridStates[si].grid[i][j] != 0:
                            self.gridStates[si].grid[i][j] = 0
                            msg.append(0)
                            self.oscClientUI.send(msg)
                            msg.clearData()
                        else: 
                            self.gridStates[si].grid[i][j] = 18
                            msg.append(18)
                            self.oscClientUI.send(msg)
                            msg.clearData()
                self.gridStates[si].prog.c[i] = self.colToChord(self.gridStates[si].grid[i], self.gridStates[si].root, self.gridStates[si].scale)
            print "                                randomized"
            #self.prog = self.gridToProg(self.grid, self.scale, self.root) 
            
                
        
    
n = [60, 62, 64, 65]
t = [1, 1, 1, 1]
p = phrase.Phrase(n, t)
trans = [1, 2, 5, 1]

loop = MultiLoop(3)
#loop2 = Looper(p, trans)
#loop.check()
loop.uiStart()
loop.playStart()
loop.loopStart()
