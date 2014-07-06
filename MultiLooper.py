'''
Created on Nov 3, 2013

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
        self.progInd = 0
        self.grid = [[0 for i in range(16)] for j in range (16)]
        self.refgrid = [[0 for i in range(16)] for j in range (16)]
        self.pianogrid = [[0 for i in range(16)] for j in range (16)]
        self.compareBackGrid = [[0 for i in range(16)] for j in range (16)]
        self.compareFrontGrid = [[0 for i in range(16)] for j in range (16)]
        self.recievedGrid = [[0 for i in range(16)] for j in range (16)]
        self.copyGrid = [[0 for i in range(16)] for j in range (16)]
        self.prog = phrase.Progression()
        self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.prog.t = [.25 for i in range(16)]
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
        
        self.lock = threading.Lock()
    

class MultiLooper:
    
    
    def __init__(self, n):
        self.num = n
        self.gridStates = []
        for i in range(n):
            self.gridStates.append(Looper())
        
        
        self.audioThread = 0
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", 5174)) #LANdini 50505, 5174 chuck
        self.oscServSelf.addDefaultHandlers()
        self.oscServSelf.addMsgHandler("/played", self.realPlay)
        self.oscServSelf.addMsgHandler("/tester", self.tester)
        self.oscServSelf.addMsgHandler("/stop", self.stopCallback)
        self.oscServUI = OSC.OSCServer(("10.76.205.109", 8000))
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect(("169.254.133.247", 9000))
        self.oscLANdiniClient = OSC.OSCClient()
        self.oscLANdiniClient.connect(("127.0.0.1", 50506))
        self.stepTrack = OSC.OSCMessage()
        
        
        
        
        self.gridcallbacks = [[[0 for i in range(16)] for j in range (16)] for i in range(n)]
        self.pianocallbacks = [[[0 for i in range(16)] for j in range (16)] for i in range(n)]
        self.recievedcallbacks = [[[0 for i in range(16)] for j in range (16)] for i in range(n)]
        self.copycallbacks = [[[0 for i in range(16)] for j in range (16)] for i in range(n)]
        self.uiThread = 0
        self.oscServUI.addDefaultHandlers()
        #print "buildcheck\n\n\n"
        
        
        
        for k in range(n):
            #self.oscServSelf.addMsgHandler("/" +str(k) + "/gridrecv", self.recieveGrid)
            
            self.oscServUI.addMsgHandler("/" +str(k) +"/noisy", self.noiseFlip)
            self.oscServUI.addMsgHandler("/" +str(k) +"/colsel", self.colsubflip)
            self.oscServUI.addMsgHandler("/" +str(k) +"/piano", self.pianoModeOn)
            self.oscServUI.addMsgHandler("/" +str(k) +"/refresh", self.refreshHandler)
            self.oscServUI.addMsgHandler("/" +str(k) +"/compare", self.toCompareView)
            self.oscServUI.addMsgHandler("/" +str(k) +"/compareReturn", self.compareToMain)
            self.oscServUI.addMsgHandler("/" +str(k) +"/scaleApply", self.applyCustomScale)
            self.oscServUI.addMsgHandler("/" +str(k) +"/up", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k) +"/down", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k) +"/left", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k) +"/right", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k) +"/arrowToggle", self.arrowTogHandler)
            
            #self.oscServUI.addMsgHandler("/sendgrid", self.sendButtonTest)
            #self.oscServUI.addMsgHandler("/4", self.prepareToSend)
            #self.oscServUI.addMsgHandler("/setgrid", self.applyRecvGrid)
        
        #need to add everything for moving piano mode grid back to main 
        
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k) +"/step/" + str(i+1) + "/1", self.stepjump)
                #print "step jumper " + str(i + 1)
                self.oscServUI.addMsgHandler("/" +str(k) +"/pianoKey/" + str(i+1) + "/1", self.pianoKey)
                
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k) +"/col/" + str(i+1) + "/1", self.colsub)
                #print "step jumper " + str(i + 1)
            
            for i in range(5):
                self.oscServUI.addMsgHandler("/" +str(k) +"/noiselev/" + str(i+1) + "/1", self.noiseLevHandler)
            
            for i in range(6):
                self.oscServUI.addMsgHandler("/" +str(k) +"/gridload/" + str(i+1) + "/1", self.gridload)
            
            for i in range(6):
                self.oscServUI.addMsgHandler("/" +str(k) +"/gridsave/" + str(i+1) + "/1", self.saveGrid)
                
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k) +"/custScale/" + str(i+1) + "/1", self.custScale)
                
                
            for i in range(16):
                for j in range(16):
                    self.gridcallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.grid, addr, stuff)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k) +"grid/"+str(i+1)+"/"+str(j+1), self.gridcallbacks[i][j])
            
            for i in range(16):
                for j in range(16):
                    
                    self.pianocallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.pianogrid, addr, stuff)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k) +"pianoGrid/"+str(i+1)+"/"+str(j+1), self.pianocallbacks[i][j])
            
#            for i in range(16):
#                for j in range(16):
#                    
#                    self.recievedcallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.recievedGrid, addr, stuff)
#                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
#                    self.oscServUI.addMsgHandler("recievedGrid/"+str(i+1)+"/"+str(j+1), self.recievedcallbacks[i][j])
#            
#            for i in range(16):
#                for j in range(16):
#                    
#                    self.copycallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.copyGrid, addr, stuff)
#                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
#                    self.oscServUI.addMsgHandler("copyGrid/"+str(i+1)+"/"+str(j+1), self.copycallbacks[i][j])
            
            #print "\n\n\nbuildcheck\n\n"

    
    def realPlay(self, *args):
        ##print "aoibay"
        #phrase.play(lv.stableMorph(self.loopObj, self.loopVect[self.loopInd]))
#        phrase.play(phrase.transpose(self.loopObj, self.loopVect[self.loopInd]))
#        self.loopInd %= len(self.loopVect)
#        if self.progInd == len(16):     #for playing chord progs (matrix)
#            self.progInd %= len(self.loopObj)
#            self.loopInd += 1 

        for i in range(self.num):
            chords = []
            with self.gridStates[i].lock: 
                if(self.gridStates[i].subsets):
                    l = len(self.gridStates[i].columnsub)
                    self.gridStates[i].progInd %= len(self.gridStates[i].columnsub)
                    playind = self.gridStates[i].columnsub[self.gridStates[i].progInd]
                    
                else:
                    l = 16
                    self.gridStates[i].progInd %= 16
                    playind = self.gridStates[i].progInd
                #print playind, "playind"
                #turn light on for progind+1
                self.gridStates[i].stepTrack.setAddress("/" +str(i) +"/step/" + str(playind+1) + "/1")
                self.gridStates[i].stepTrack.append(1)
                self.gridStates[i].oscClientUI.send(self.gridStates[i].stepTrack)
                self.gridStates[i].stepTrack.clearData()
                ##print "in play"
                chords.append(copy.deepcopy(self.gridStates[i].prog.c[playind])) # self.prog.c[playind] make this more efficient turn it into a PLAYER object?
                if self.gridStates[i].refreshing:
                    ##print "                                   refresh", playind
                    self.gridStates[i].refreshColumn(playind, i)
                self.gridStates[i].loopInd += 1
                self.gridStates[i].progInd += self.gridStates[i].stepIncrement
            if self.gridStates[i].noisy and (self.gridStates[i].progInd == (l) or(self.gridStates[i].progInd == -1)):
                self.gridStates[i].gridNoise(self.gridStates[i].noiselev)
                #print "                             noise at", l
        phrase.play(chords[0], chords[1], chords[2])
            
    
    def refreshColumn(self, k, gridind):
        msg = OSC.OSCMessage()
        
        for i in range(len(self.gridStates[gridind].grid)):
            if(self.gridStates[gridind].refgrid[k][i] != self.gridStates[gridind].grid[k][i]):
                #print "                            single element refresh", k+1, i+1, self.refgrid[k][i]
                msg.setAddress("/grid/" + str(k+1) + "/" + str(16-i))
                msg.append(self.gridStates[gridind].refgrid[k][i])
                self.gridStates[gridind].oscClientUI.send(msg)
                msg.clearData()
                self.gridStates[gridind].grid[k][i] = self.gridStates[gridind].refgrid[k][i]
        self.gridStates[gridind].prog.c[k] = self.gridStates[gridind].refprog.c[k]
    
    def refreshHandler(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #print "                     hit ref handler", stuff, stuff[0] != 0
        if stuff[0] != 0:
            #print "                    in conditional"
            self.gridStates[gridind].refreshing = True
            self.gridStates[gridind].refprog = phrase.Progression(self.gridStates[gridind].prog)
            #print type(self.refprog), "refprog", "before"
            self.gridStates[gridind].refgrid = self.gridcopy(self.gridStates[gridind].grid)
            #print len(self.prog), ":prog", len(self.refprog), ":refprog"
            print "                           refresh on"
        else:
            self.gridStates[gridind].refreshing = False
            print "                           refresh off"   
    
    def stepjump(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        if stuff[0] != 0:
            self.gridStates[gridind].progInd, k = self.gridAddrInd(addr) #int(addr.split("/")[3]) - 1 #replace with gridAddrInd
            if self.gridStates[gridind].subsets:
                if self.gridStates[gridind].progInd in self.gridStates[gridind].columnsub:
                    self.gridStates[gridind].progInd = self.gridStates[gridind].columnsub.index(self.gridStates[gridind].progInd)
                else:
                    if self.gridStates[gridind].progInd > self.gridStates[gridind].columnsub[-1]:
                        self.gridStates[gridind].progInd = len(self.gridStates[gridind].columnsub) - 1
                        return
                    i = len(self.gridStates[gridind].columnsub) - 1
                    while self.gridStates[gridind].columnsub[i] >= self.gridStates[gridind].progInd:
                        self.gridStates[gridind].progInd = self.gridStates[gridind].columnsub[i]
                        i -= 1
                    
            print "                                jumped to " + str(self.gridStates[gridind].progInd)
    
    def noiseFlip(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        print "                               noise flip " + str(stuff[0] == 1)
        self.gridStates[gridind].noisy = (stuff[0] == 1)
    #new
    
    def noiseLevHandler(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #self.noiselev = 2 * int(addr.split("/")[2])
        i, j = self.gridAddrInd(addr)
        self.gridStates[gridind].noiselev = 2 * (i+1)
    
    def colsub(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #ind = int(addr.split("/")[2]) - 1 #replace with gridAddrInd
        ind, j = self.gridAddrInd(addr)
        if stuff[0] == 1 and ind not in self.gridStates[gridind].columnsub: #do we need 2nd conditional?
            self.gridStates[gridind].columnsub.append(ind)
            print "                            added " + str(ind)
        if stuff[0] == 0 and ind in self.gridStates[gridind].columnsub:
            self.gridStates[gridind].columnsub.remove(ind)
            print "                            removed " + str(ind)
        self.gridStates[gridind].columnsub.sort()
    
    def colsubflip(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #print "                             gottem yo", self.progInd
        with self.gridStates[gridind].lock:
            #print "                             inside lock ", self.progInd
            self.gridStates[gridind].subsets = (stuff[0] == 1)
            #print "                             past bool", self.subsets 
            self.gridStates[gridind].progInd = 0 if stuff[0] == 1 else self.gridStates[gridind].columnsub[self.gridStates[gridind].progInd]
            print "                      colsub ", str(self.gridStates[gridind].subsets), "progind" + str(self.gridStates[gridind].progind)
        
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
    def gridload(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        if stuff[0] == 0: return
        #ind = int(addr.split("/")[2]) - 1
        ind, j = self.gridAddrInd(addr)
        self.pullUpGrid(self.gridStates[gridind].gridzz[ind], "/" +str(gridind)+ "/grid")
    #new
    def pullUpGrid(self, grid, gridAddr):
        gridind = int(gridAddr[1])
        msg = OSC.OSCMessage()
        with self.gridStates[gridind].lock:
            self.gridStates[gridind].prog = self.gridToProg(grid, self.gridStates[gridind].scale, self.gridStates[gridind].root)
            for i in range(len(grid)):
                for j in range(len(grid)):
                    msg.setAddress(gridAddr + "/"+str(i+1) +"/" + str(16-j))
                    msg.append(grid[i][j])
                    self.gridStates[gridind].oscClientUI.send(msg)
                    msg.clearData()
            self.gridStates[gridind].grid = self.gridcopy(grid)
            #print "                          pre", type(grid), type(self.scale), type(self.root)
            #print "                          progged"
            
    
    def pullUpScale(self, scale, scaleAddr):
        print "           ", scale 
        msg = OSC.OSCMessage()
        for i in range(12):
            msg.clearData()
            msg.setAddress("/custScale/"+ str(i+1) +"/1" )
            if i in scale:
                msg.append(1)
            else:
                msg.append(0)
            self.oscClientUI.send(msg)
                
                 
            
    def pianoModeOn(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #switch tab to piano mode tab
        if(stuff[0] == 0):
            self.gridStates[gridind].prog = self.gridToProg(self.gridStates[gridind].grid, self.gridStates[gridind].scale, self.gridStates[gridind].root)
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
        self.gridStates[gridind].pianogrid = self.gridcopy(self.grid)
        self.pullUpGrid(self.gridStates[gridind].grid, "/" + str(gridind)+ "/pianoGrid")
        #hanlders for "piano keys" should already be set up
        return
    #SHOULD PIANO GRID BE EDITABLE AND SHOULD EDITS UPDATE TO MAIN GRID
    
    #set up handler using lambda functions like with normal grid 
    def pianoKey(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        i, j = self.gridAddrInd(addr)
        if(stuff[0] == 1):
            #print "piano on"
            phrase.play(self.gridStates[gridind].prog.c[i], toggle="on")
        else:
            #print "piano off"
            phrase.play(self.gridStates[gridind].prog.c[i], toggle="off")
    
    def applyCustomScale(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        if stuff[0] == 0:
            return
        with self.gridStates[gridind].lock:
            custScale = [i - min(self.gridStates[gridind].customScale) for i in self.gridStates[gridind].customScale]
            custScale.sort()
            print custScale
            self.gridStates[gridind].scale = custScale
            self.gridStates[gridind].prog = self.gridToProg(self.gridStates[gridind].grid, custScale, self.gridStates[gridind].root)
    
    def custScale(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        i, j = self.gridAddrInd(addr)
        if(stuff[0] != 0):
            self.gridStates[gridind].customScale.append(i)
            print "                added note to scale", i 
        else:
            if i in self.gridStates[gridind].customScale:
                self.gridStates[gridind].customScale.remove(i)
                print "                removed note from scale", i
    
    def toCompareView(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #change page
        self.pullUpGrid(self.grid, "/compareBack")
    
    def compareToMain(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        with self.lock:
            #change page
            self.pullUpGrid(self.compareFrontGrid, "/grid")
            self.grid = self.gridcopy(self.compareFrontGrid)
            self.prog = self.gridToProg(self.grid, self.scale, self.root)
            
    #new
    def saveGrid(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        #ind = int(addr.split("/")[2]) - 1
        ind, j = self.gridAddrInd(addr)
        if stuff[0] != 0:
            self.gridStates[gridind].gridzz[ind] = self.gridcopy(self.gridStates[gridind].grid)
        else: 
            self.gridStates[gridind].gridzz[ind] = 0 
    #new        
    def gridClear(self):
        self.prog = self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.pullUpGrid([[0 for i in range(16)] for j in range (16)], "/grid")
    
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
        gridind = int(addr[1])
        self.gridStates[gridind].arrowToggle = (stuff[0] == 1)
    
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
        gridind = int(addr[1])
        if stuff[0] == 0:
            return
        direction = addr.split("/")[1]
        print "                   direction:", direction
        if(self.gridStates[gridind].arrowToggle):
            if direction == "left":
                self.gridStates[gridind].stepIncrement = -1
            if direction == "right":
                self.gridStates[gridind].stepIncrement = 1
            if direction == "up":
                self.gridStates[gridind].root += 1
                with self.gridStates[gridind].lock:
                    self.gridStates[gridind].prog = self.gridToProg(self.gridStates[gridind].grid, self.gridStates[gridind].scale, self.gridStates[gridind].root)
            if direction == "down":
                self.gridStates[gridind].root -= 1
                with self.gridStates[gridind].lock:
                    self.gridStates[gridind].prog = self.gridToProg(self.gridStates[gridind].grid, self.gridStates[gridind].scale, self.gridStates[gridind].root)
                    
        else:
            g = self.gridShift(self.gridStates[gridind].grid, direction)
            with self.gridStates[gridind].lock:
                self.gridStates[gridind].grid = g
            self.pullUpGrid(self.gridStates[gridind].grid, "/grid")
            
    
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
    
    #a is actually self.grid - change this later    
    def assign2(self, a, b, c):
        gridind = int(b[1])
        with self.gridStates[gridind].lock:
            #print c
#            s = b.split("/")
#            i = int(s[2])-1
#            j = 16-int(s[3])
            i, j = self.gridAddrInd(b)
            a[i][j] = c[0]
            print "          assigned " + str(c[0]) + " to " + str(i+1) +" " + str(16-j) #correct?
            self.gridStates[gridind].prog.c[i] = self.colToChord(a[i], self.gridStates[gridind].root, self.gridStates[gridind].scale)
            #print self.prog, "\n\n\n"        
    
    def saveGridtoFile(self):
        filename = raw_input("Grid Name: ")
        savefile = open(filename +".ss", "rw")
        cPickle.dump(self.grid, savefile)
    
    def loadGridFromFile(self):
        filename = raw_input("File Name: ")
        obj = cPickle.load(open(filename))
        self.grid = obj
        self.prog = self.gridToProg(obj, self.scale, self.root)
        self.pullUpGrid(obj, "/grid")
    
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
    
    def sendButtonTest(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        if stuff[0] == 0:
            return
        else:
            self.sendGrid()
            
    def prepareToSend(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        self.pullUpGrid(self.grid, "/copyGrid")
    
    def sendGrid(self):
        recipient = raw_input("Who do you want to send a grid to: ")
        #recipient = "all"
        msg = OSC.OSCMessage()
        msg.setAddress("/send/GD")
        msg.append(recipient)
        msg.append("/gridrecv")
        msg.append(self.gridKeyToString(self.copyGrid, self.scale)) #replace with edit grid?
        print self.gridKeyToString(self.grid, self.scale)
        self.oscLANdiniClient.send(msg)
        
    def recieveGrid(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        grid, scale = self.stringToGridKey(stuff[0])
        self.recievedGrid = grid
        self.pullUpGrid(grid, "/recievedGrid")
        self.pullUpScale(scale, "/custScale")
        self.customScale = [i+1 for i in scale]
        
    def applyRecvGrid(self, addr, tags, stuff, source):
        gridind = int(addr[1])
        with self.lock:
            self.grid = self.gridcopy(self.recievedGrid)
            self.scale = [i - min(self.customScale) for i in self.customScale]
            self.scale.sort()
            #self.prog = self.gridToProg(self.grid, self.scale, self.root)
            self.pullUpGrid(self.grid, "/grid")
        
        
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
        return 
        
    def blend(self, grid1, grid2, direction, amount):
        blend = [[0 for i in range(len(grid1))] for j in range (len(grid1))]
        allslots = range(len(grid1))
        set1 = []
        for i in range(amount):
            k = random.choice(allslots)
            allslots.remove(k)
            set.append(k)
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
              
    
    def gridNoise(self, k, gridind): #fix this 
        #print "in noise"
        with self.gridStates[gridind].lock:
            #print "in lock"
            l = len(self.gridStates[gridind].grid)
            p = 1.0 * k / (l*l)
            msg = OSC.OSCMessage()
            #make everything 1 instead of 14 in touchOSC
            for i in range(l):
                for j in range(l):
                    if random.uniform(0, 1) < p:
                        msg.setAddress("/grid/"+str(i+1) +"/" + str(16-j))
                        if self.gridStates[gridind].grid[i][j] != 0:
                            self.gridStates[gridind].grid[i][j] = 0
                            msg.append(0)
                            self.oscClientUI.send(msg)
                            msg.clearData()
                        else: 
                            self.gridStates[gridind].grid[i][j] = 18
                            msg.append(18)
                            self.oscClientUI.send(msg)
                            msg.clearData()
                self.gridStates[gridind].prog.c[i] = self.colToChord(self.gridStates[gridind].grid[i], self.gridStates[gridind].root, self.gridStates[gridind].scale)
            print "                                randomized"
            #self.prog = self.gridToProg(self.grid, self.scale, self.root) 
            
                
        
    
n = [60, 62, 64, 65]
t = [1, 1, 1, 1]
p = phrase.Phrase(n, t)
trans = [1, 2, 5, 1]

loop = Looper(p, trans)
#loop2 = Looper(p, trans)
#loop.check()
loop.uiStart()
loop.playStart()
loop.loopStart()
