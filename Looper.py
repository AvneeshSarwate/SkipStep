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
import cPickle
import copy



class Looper:
    
    
    def __init__(self, loopO, loopV):
        #self.recvAddr = 
        self.loopObj = loopO
        self.loopVect = loopV
        self.loopInd = 0
        self.progInd = len(loopO)
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
        
        
        self.audioThread = 0
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", 50505)) #LANdini 50505, 5174 chuck
        self.oscServSelf.addDefaultHandlers()
        self.oscServSelf.addMsgHandler("/played", self.realPlay)
        self.oscServSelf.addMsgHandler("/tester", self.tester)
        self.oscServSelf.addMsgHandler("/stop", self.stopCallback)
        self.oscServUI = OSC.OSCServer(("169.254.252.125", 8000))
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect(("169.254.48.128", 9000))
        self.oscLANdiniClient = OSC.OSCClient()
        self.oscLANdiniClient.connect(("127.0.0.1", 50506))
        self.stepTrack = OSC.OSCMessage()
        
        
        self.lock = threading.Lock()
        
        self.gridcallbacks = [[0 for i in range(16)] for j in range (16)]
        self.pianocallbacks = [[0 for i in range(16)] for j in range (16)]
        self.recievedcallbacks = [[0 for i in range(16)] for j in range (16)]
        self.copycallbacks = [[0 for i in range(16)] for j in range (16)]
        self.uiThread = 0
        self.oscServUI.addDefaultHandlers()
        #print "buildcheck\n\n\n"
        
        self.oscServSelf.addMsgHandler("/recievedGrid", self.recieveGrid)
        self.oscServUI.addMsgHandler("/noisy", self.noiseFlip)
        self.oscServUI.addMsgHandler("/colsel", self.colsubflip)
        self.oscServUI.addMsgHandler("/piano", self.pianoModeOn)
        self.oscServUI.addMsgHandler("/refresh", self.refreshHandler)
        self.oscServUI.addMsgHandler("/compare", self.toCompareView)
        self.oscServUI.addMsgHandler("/compareReturn", self.compareToMain)
        self.oscServUI.addMsgHandler("/scaleApply", self.applyCustomScale)
        self.oscServUI.addMsgHandler("/up", self.gridShiftHandler)
        self.oscServUI.addMsgHandler("/down", self.gridShiftHandler)
        self.oscServUI.addMsgHandler("/left", self.gridShiftHandler)
        self.oscServUI.addMsgHandler("/right", self.gridShiftHandler)
        self.oscServUI.addMsgHandler("/arrowToggle", self.arrowTogHandler)
        self.oscServUI.addMsgHandler("/sendgrid", self.sendButtonTest)
        self.oscServUI.addMsgHandler("/4", self.prepareToSend)
        self.oscServUI.addMsgHandler("/setgrid", self.applyRecvGrid)
        self.oscServUI.addMsgHandler("/clear", self.gridClear)
        
        
        #need to add everything for moving piano mode grid back to main 
        
        for i in range(16):
            self.oscServUI.addMsgHandler("/step/" + str(i+1) + "/1", self.stepjump)
            #print "step jumper " + str(i + 1)
            self.oscServUI.addMsgHandler("/pianoKey/" + str(i+1) + "/1", self.pianoKey)
            
        for i in range(16):
            self.oscServUI.addMsgHandler("/col/" + str(i+1) + "/1", self.colsub)
            #print "step jumper " + str(i + 1)
        
        for i in range(5):
            self.oscServUI.addMsgHandler("/noiselev/" + str(i+1) + "/1", self.noiseLevHandler)
        
        for i in range(6):
            self.oscServUI.addMsgHandler("/gridload/" + str(i+1) + "/1", self.gridload)
        
        for i in range(6):
            self.oscServUI.addMsgHandler("/gridsave/" + str(i+1) + "/1", self.saveGrid)
            
        for i in range(16):
            self.oscServUI.addMsgHandler("/custScale/" + str(i+1) + "/1", self.custScale)
            
            
        for i in range(16):
            for j in range(16):
                self.gridcallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.grid, addr, stuff, self.prog)
                ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("grid/"+str(i+1)+"/"+str(j+1), self.gridcallbacks[i][j])
        
        for i in range(16):
            for j in range(16):
                
                self.pianocallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.pianogrid, addr, stuff, self.pianoprog)
                ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("pianoGrid/"+str(i+1)+"/"+str(j+1), self.pianocallbacks[i][j])
        
        for i in range(16):
            for j in range(16):
                
                self.recievedcallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.recievedGrid, addr, stuff, 0)
                ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("recievedGrid/"+str(i+1)+"/"+str(j+1), self.recievedcallbacks[i][j])
        
        for i in range(16):
            for j in range(16):
                
                self.copycallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.copyGrid, addr, stuff, 0)
                ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("copyGrid/"+str(i+1)+"/"+str(j+1), self.copycallbacks[i][j])
        
        #print "\n\n\nbuildcheck\n\n"

    
    def realPlay(self, *args):
        ##print "aoibay"
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
            #print playind, "playind"
            #turn light on for progind+1
            self.stepTrack.setAddress("/step/" + str(playind+1) + "/1")
            self.stepTrack.append(1)
            self.oscClientUI.send(self.stepTrack)
            self.stepTrack.clearData()
            ##print "in play"
            phrase.play(self.prog.c[playind]) # self.prog.c[playind] make this more efficient turn it into a PLAYER object?
            if self.refreshing:
                ##print "                                   refresh", playind
                self.refreshColumn(playind)
            self.loopInd += 1
            self.progInd += self.stepIncrement
        if self.noisy and (self.progInd == (l) or(self.progInd == -1)):
            self.gridNoise(self.noiselev)
            #print "                             noise at", l
            
    
    def refreshColumn(self, k):
        msg = OSC.OSCMessage()
        
        for i in range(len(self.grid)):
            if(self.refgrid[k][i] != self.grid[k][i]):
                #print "                            single element refresh", k+1, i+1, self.refgrid[k][i]
                msg.setAddress("/grid/" + str(k+1) + "/" + str(16-i))
                msg.append(self.refgrid[k][i])
                self.oscClientUI.send(msg)
                msg.clearData()
                self.grid[k][i] = self.refgrid[k][i]
        self.prog.c[k] = self.refprog.c[k]
    
    def refreshHandler(self, addr, tags, stuff, source):
        #print "                     hit ref handler", stuff, stuff[0] != 0
        if stuff[0] != 0:
            #print "                    in conditional"
            self.refreshing = True
            self.refprog = phrase.Progression(self.prog)
            #print type(self.refprog), "refprog", "before"
            self.refgrid = self.gridcopy(self.grid)
            #print len(self.prog), ":prog", len(self.refprog), ":refprog"
            print "                           refresh on"
        else:
            self.refreshing = False
            print "                           refresh off"   
    
    def stepjump(self, addr, tags, stuff, source):
        if stuff[0] != 0:
            self.progInd = int(addr.split("/")[2]) - 1 #replace with gridAddrInd
            if self.subsets:
                if self.progInd in self.columnsub:
                    self.progInd = self.columnsub.index(self.progInd)
                else:
                    if self.progInd > self.columnsub[-1]:
                        self.progInd = len(self.columnsub) - 1
                        return
                    i = len(self.columnsub) - 1
                    while self.columnsub[i] >= self.progInd:
                        self.progInd = self.columnsub[i]
                        i -= 1
                    
            print "                                jumped to " + str(self.progInd)
    
    def noiseFlip(self, addr, tags, stuff, source):
        print "                               noise flip " + str(stuff[0] == 1)
        self.noisy = (stuff[0] == 1)
    #new
    def noiseLevHandler(self, addr, tags, stuff, source):
        self.noiselev = 2 * int(addr.split("/")[2])
    
    def colsub(self, addr, tags, stuff, source):
        ind = int(addr.split("/")[2]) - 1 #replace with gridAddrInd
        if stuff[0] == 1 and ind not in self.columnsub: #do we need 2nd conditional?
            self.columnsub.append(ind)
            print "                            added " + str(ind)
        if stuff[0] == 0 and ind in self.columnsub:
            self.columnsub.remove(ind)
            print "                            removed " + str(ind)
        self.columnsub.sort()
    
    def colsubflip(self, addr, tags, stuff, source):
        #print "                             gottem yo", self.progInd
        with self.lock:
            #print "                             inside lock ", self.progInd
            self.subsets = (stuff[0] == 1)
            #print "                             past bool", self.subsets 
            self.progInd = 0 if stuff[0] == 1 else self.columnsub[self.progInd]
            print "                      colsub ", str(self.subsets), "progind" + str(self.progind)
        
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
        ind = int(addr.split("/")[2]) - 1
        if stuff[0] != 0:
            self.gridzz[ind] = self.gridKeyToString(self.grid, self.key)#self.gridcopy()
        else: 
            self.gridzz[ind] = 0 
    #new 
    def gridload(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        ind, j = self.gridAddrInd(addr)#int(addr.split("/")[2]) - 1
        grid, scale = self.stringToGridKey(self.gridzz[ind])
        self.pullUpGrid(grid, "/grid")
        self.pullUpScale(scale, "/custScale")
        self.customScale = [1+i for i in scale]
        self.grid = grid
        self.scale = scale
        self.prog = self.gridToProg(self.grid, self.scale, self.root)
    #new
    def pullUpGrid(self, grid, gridAddr):
        msg = OSC.OSCMessage()
        print "pullup outside lock"
        with self.lock:
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
            msg.setAddress("/custScale/"+ str(i+1) +"/1" )
            if i in scale:
                msg.append(1)
            else:
                msg.append(0)
            self.oscClientUI.send(msg)
                
                 
            
    def pianoModeOn(self, addr, tags, stuff, source):
        #switch tab to piano mode tab
        if(stuff[0] == 0):
            self.prog = self.gridToProg(self.grid, self.scale, self.root)
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
        self.pianogrid = self.gridcopy(self.grid)
        self.pianoprog = self.gridToProg(self.pianogrid, self.scale, self.root)
        self.pullUpGrid(self.pianogrid, "/pianoGrid")
        #hanlders for "piano keys" should already be set up
        return
    #SHOULD PIANO GRID BE EDITABLE AND SHOULD EDITS UPDATE TO MAIN GRID
    
    #set up handler using lambda functions like with normal grid 
    def pianoKey(self, addr, tags, stuff, source):
        i, j = self.gridAddrInd(addr)
        print i
        if(stuff[0] == 1):
            #print "piano on"
            phrase.play(self.pianoprog.c[i], toggle="on")
        else:
            #print "piano off"
            phrase.play(self.pianoprog.c[i], toggle="off")
    
    def applyCustomScale(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        with self.lock:
            custScale = [i - min(self.customScale) for i in self.customScale]
            custScale.sort()
            print custScale
            self.scale = custScale
            self.prog = self.gridToProg(self.grid, custScale, self.root)
    
    def custScale(self, addr, tags, stuff, source):
        i, j = self.gridAddrInd(addr)
        if(stuff[0] != 0):
            self.customScale.append(i)
            print "                added note to scale", i 
        else:
            if i in self.customScale:
                self.customScale.remove(i)
                print "                removed note from scale", i
    
    def toCompareView(self, addr, tags, stuff, source):
        #change page
        self.pullUpGrid(self.grid, "/compareBack")
    
    def compareToMain(self, addr, tags, stuff, source):
        with self.lock:
            #change page
            self.pullUpGrid(self.compareFrontGrid, "/grid")
            self.grid = self.gridcopy(self.compareFrontGrid)
            self.prog = self.gridToProg(self.grid, self.scale, self.root)
            
    
    #new        
    def gridClear(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        self.prog.c = [phrase.Chord([-1]) for i in range(16)]
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
        self.arrowToggle = (stuff[0] == 1)
    
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
        if stuff[0] == 0:
            return
        direction = addr.split("/")[1]
        print "                   direction:", direction
        if(self.arrowToggle):
            if direction == "left":
                self.stepIncrement = -1
            if direction == "right":
                self.stepIncrement = 1
            if direction == "up":
                self.root += 1
                with self.lock:
                    self.prog = self.gridToProg(self.grid, self.scale, self.root)
            if direction == "down":
                self.root -= 1
                with self.lock:
                    self.prog = self.gridToProg(self.grid, self.scale, self.root)
                    
        else:
            g = self.gridShift(self.grid, direction)
            with self.lock:
                self.grid = g
                self.prog = self.gridToProg(self.grid, self.scale, self.root)
            self.pullUpGrid(self.grid, "/grid")
            
    
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
        i = int(s[2])-1
        j = 16-int(s[3])
        return i, j
        
    def indToUIInd(self, i, j):
        return i+1, 16-j
    
    #a - grid, b - addr, c - stuff, d - prog  
    def assign2(self, a, b, c, d):
        with self.lock:
            #print c
#            s = b.split("/")
#            i = int(s[2])-1
#            j = 16-int(s[3])
            i, j = self.gridAddrInd(b)
            a[i][j] = c[0]
            print "          assigned " + str(c[0]) + " to " + str(i+1) +" " + str(16-j), sum(a[i]) #correct?
            if d == 0: 
                print "no prog"
                return
            d.c[i] = self.colToChord(a[i], self.root, self.scale)
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
        if stuff[0] == 0:
            return
        else:
            self.sendGrid()
            
    def prepareToSend(self, addr, tags, stuff, source):
        self.pullUpGrid(self.grid, "/copyGrid")
        self.copyGrid = self.gridcopy(self.grid)
    
    def sendGrid(self):
        recipient = raw_input("Who do you want to send a grid to: ")
        print recipient
        #recipient = "all"
        msg = OSC.OSCMessage()
        msg.setAddress("/send/GD")
        msg.append(recipient)
        msg.append("/recievedGrid")
        print self.copyGrid 
        print
        print
        msg.append(self.gridKeyToString(self.copyGrid, self.scale)) #replace with edit grid?
        #print self.gridKeyToString(self.grid, self.scale)
        self.oscLANdiniClient.send(msg)
        print "sent"
        
    def recieveGrid(self, addr, tags, stuff, source):
        print stuff[0], "got it"
        grid, scale = self.stringToGridKey(stuff[0])
        self.recievedGrid = grid
        self.pullUpGrid(grid, "/recievedGrid")
        self.pullUpScale(scale, "/custScale")
        self.customScale = [i+1 for i in scale]
        
    def applyRecvGrid(self, addr, tags, stuff, source):
        with self.lock:
            self.grid = self.gridcopy(self.recievedGrid)
            self.scale = [i - min(self.customScale) for i in self.customScale]
            self.scale.sort()
            self.prog = self.gridToProg(self.grid, self.scale, self.root)
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
              
    
    def gridNoise(self, k):
        #print "in noise"
        with self.lock:
            #print "in lock"
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
