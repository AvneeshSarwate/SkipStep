'''
Created on Nov 10, 2013

@author: avneeshsarwate
'''

import phrase
import threading
import OSC
import random
import copy
import subprocess

class Looper:

    def __init__(self):
        #self.recvAddr = 
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
        self.pianomode = False
        self.gridseq = [-1]*8
        self.gridseqInd = 0
        self.gridseqFlag = False
        self.gridseqEdit = False
        
        
        self.lock = threading.Lock()

class MultiLoop:
    
    
    def __init__(self, n):
        #self.recvAddr = 
        
        self.chuckThread = threading.Thread(target=self.chuckThreadFunc)
        
        k = subprocess.check_output(["ifconfig | grep \"inet \" | grep -v 127.0.0.1"], shell=True)
        ip = k.split(" ")[1]
        selfIP = ip
        print "\n" + "Your computer's IP address is: " + selfIP + "\n enter this into your iPad"
        
        ipadFile = open("ipadIP.txt")
        oldIpadIP = ipadFile.read().strip("\n")
        ipadFile.close()
        iPadRead = raw_input("\n\nIs the IP address of your iPad " + oldIpadIP +"?" +
                           "\n If so, hit enter. If not, type it in below:\n")
        if(iPadRead == ""): iPadIP = oldIpadIP
        else:
            iPadIP = iPadRead
            ipadFile = open("ipadIP.txt", "w")
            ipadFile.write(iPadRead)
            ipadFile.close()
            
        self.pageAddrs = []
        self.pageAddrs.append(open("page1.txt").read().split(" "))
        
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
        self.oscServUI = OSC.OSCServer((selfIP, 8000))
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect((iPadIP, 9000))
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
        
        self.oscServUI.addMsgHandler("/tempo", self.tempo)
        
        self.recievedGrid = [[0 for i in range(16)] for j in range (16)]
        self.copyGrid = [[0 for i in range(16)] for j in range (16)]
        self.copyScale = []
        self.recievedScale = []
        self.recievedcallbacks = [[0 for i in range(16)] for j in range (16)]
        self.copycallbacks = [[0 for i in range(16)] for j in range (16)]
        
        self.oscServUI.addMsgHandler("/test", self.seqtest)
        
        for i in range(16):
                self.oscServUI.addMsgHandler("/copyScale/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.assignScale(addr, stuff, self.copyScale))
            
        for i in range(16):
            self.oscServUI.addMsgHandler("/recievedScale/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.assignScale(addr, stuff, self.recievedScale))
        
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
        
        self.oscServUI.addMsgHandler("/sendGrid", self.sendButtonTest)
        self.oscServSelf.addMsgHandler("/recievedGrid", self.recieveGrid)
        
        self.oscServUI.addMsgHandler("/save", self.saveGridtoFile)
        self.oscServUI.addMsgHandler("/load", self.loadGridFromFile)
        
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
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiseHit", self.noiseHit)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/undo", self.undo)
            
            for j in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/gridseq/" + str(j) + "/1", self.gridSeqIndHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/seqtoggle", self.gridSeqToggleHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/seqedit", self.gridSeqEditHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/seqclear", self.gridSeqClear)
            
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
                
#            for i in range(16):
#                self.oscServUI.addMsgHandler("/" +str(k+1) +"/custScale/" + str(i+1) + "/1", self.custScale)
#            
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/custScale/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.assignScale(addr, stuff, self.gridStates[int(addr.split("/")[1])-1].customScale))
                
            for i in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiseSel/" + str(i+1) + "/1", self.noiseSelector)
            
            for i in range(16):
                for j in range(16):
                    self.gridcallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].grid, addr, stuff, self.gridStates[int(addr.split("/")[1])-1].prog)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/grid/"+str(i+1)+"/"+str(j+1), self.gridcallbacks[k][i][j])
            
            for i in range(16):
                for j in range(16):
                    
                    self.pianocallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].pianogrid, addr, stuff, self.gridStates[int(addr.split("/")[1])-1].pianoprog)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/pianoGrid/"+str(i+1)+"/"+str(j+1), self.pianocallbacks[k][i][j])
            
            self.oscServUI.addMsgHandler("/getGridScale/" +str(k+1) + "/1", self.getGridToSend)
            self.oscServUI.addMsgHandler("/applyRecvGrid/" +str(k+1) + "/1", self.applyRecvGrid)
            self.oscServUI.addMsgHandler("/applyRecvScale/" +str(k+1) + "/1", self.applyRecvScale)
            
            
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
            state = self.gridStates[si]
            with state.lock: 
                if(state.subsets):
                    state.progInd %= len(state.columnsub)
                    playind = state.columnsub[state.progInd]
                    
                else:
                    state.progInd %= 16
                    playind = state.progInd
                #print playind, "playind", self.prog.c[playind].n
                #turn light on for progind+1
                if state.pianomode:
                    chords.append(phrase.Chord([-1]))
                else:
                    self.stepTrack.setAddress("/" + str(si+1) + "/step/" + str(playind+1) + "/1")
                    self.stepTrack.append(1)
                    self.oscClientUI.send(self.stepTrack)
                    self.stepTrack.clearData()
                    ##print "in play"
                    chords.append(state.prog.c[playind]) # self.prog.c[playind] make this more efficient turn it into a PLAYER object?
                if state.refreshing:
                    ##print "                                   refresh", playind
                    self.refreshColumn(playind, si)
                #self.gridStates[si].loopInd += 1
                state.progInd += state.stepIncrement
            
                #self.gridNoise(self.noiselev)
                #print                               noise at", l
        phrase.play(chords[0], chords[1], chords[2])
        
        #noise moved to after playing so noise calculations can be done in downtime while note is "playing"
        #could move other stuff into this loop as well if performance is an issue
        
        for si in range(self.num):
            state = self.gridStates[si]
            if (not state.subsets and (state.progInd == 16))  or (state.subsets and (state.progInd == len(state.columnsub))) or (state.progInd == -1):
                #print "LOOPEND " + str(si+1)
                if state.gridseqFlag and sum(state.gridseq) != -8:
                    while state.gridseq[state.gridseqInd] == -1: 
                        state.gridseqInd = (state.gridseqInd + state.stepIncrement) % 8
                        print "       progressing to index", state.gridseqInd
                    
                    
                    print "GRID SEQUENCING CHANGE ", si+1, "seq ind is ", state.gridseqInd, "seq value is", state.gridseq[state.gridseqInd]
                    msg = OSC.OSCMessage()
                    msg.setAddress("/" + str(si+1) + "/gridseq/" + str(state.gridseqInd+1) + "/1")
                    msg.append(1)
                    self.oscClientUI.send(msg)
                    
                    if state.gridseq[state.gridseqInd] == "blank": 
                        g = [[0 for i in range(16)] for j in range(16)]
                    else:
                        g = self.stringToGridKey(state.gridzz[state.gridseq[state.gridseqInd]])[0]
                        #g, scale, root, colsub = self.stringToMiniState(state.gridzz[state.gridseq[state.gridseqInd]])
                    #print "          g is grid number ", state.gridseq[state.gridseqInd], "of length ", len(g)
                    
                    if state.noisy:
                        g = self.noiseChoice(si)
                        if not state.refeshing:
                            state.gridzz[state.gridseq[state.gridseqInd]] = self.gridKeyToString(g, state.scale)
                            #state.gridzz[state.gridseq[state.gridseqInd]] = self.miniStateToString(g, scale, root, colsub, si)
                    with state.lock:
                        self.putGridLive(g, si)
                        #self.putMiniStateLive(g, scale, root, columnsub, si) 
                    state.gridseqInd = (state.gridseqInd + state.stepIncrement) % 8
                    print "done with sequencing update"
                    
                else:
                    print "NOT SEQUENCING ", si+1
                    if state.noisy:
                        g = self.noiseChoice(si)
                        with state.lock:
                            self.putGridLive(g, si)
                        
#            if self.gridStates[si].noisy:
#                if not self.gridStates[si].subsets and ((self.gridStates[si].progInd == 16) or(self.gridStates[si].progInd == -1)):
#                    self.noiseChoice(si)
#                if self.gridStates[si].subsets and ((self.gridStates[si].progInd == len(self.gridStates[si].columnsub)) or(self.gridStates[si].progInd == -1)):
#                    self.noiseChoice(si)
#            if self.gridStates[si].gridseqFlag:
#                state = self.gridStates[si]
#                nextgrid = state.gridzz[state.gridseq[state.gridseqInd]]
#                state.grid = self.gridcopy(nextgrid)
#                state.prog = self.gridToProg(state.grid, state.scale, state.root)
#                self.pullUpGrid(nextgrid, "grid")
#                #update visual stepper for grid indexes. 
#                state.gridseqInd = (state.gridseqInd+1) % len(state.gridseq)
        
                
    
    def refreshColumn(self, k, si):
        msg = OSC.OSCMessage()
        
        for i in range(len(self.gridStates[si].grid)):
            if(self.gridStates[si].refgrid[k][i] != self.gridStates[si].grid[k][i]):
                #print "                            single element refresh", k+1, i+1, self.refgrid[k][i]
                msg.setAddress("/" + str(si+1) + "/grid/" + str(k+1) + "/" + str(16-i))
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
        self.gridStates[si].noiselev = 2 * (i+1)
    
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
            print "                      colsub ", str(self.gridStates[si].subsets), "progind" + str(self.gridStates[si].progInd)
        
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
        state = self.gridStates[si]
        ind, j = self.gridAddrInd(addr)
        if stuff[0] != 0:
            #state.gridzz[ind] = self.gridKeyToString(state.grid, state.scale)#self.gridStates[si].gridcopy()
            state.gridzz[ind] = self.miniStateToString(state.grid, state.scale, state.root, state.columnsub, si)
        else: 
            state.gridzz[ind] = 0 
    #new 
    def gridload(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        ind = self.gridAddrInd(addr)[0]
        if stuff[0] == 0: return
        if state.gridseqEdit:
            state.gridseq[state.gridseqInd] = ind
            msg = OSC.OSCMessage()
            print "/" + str(si+1) + "/seqtext/" + str(state.gridseqInd)
            msg.setAddress("/" + str(si+1) + "/seqtext/" + str(state.gridseqInd+1))
            msg.append(str(ind+1))
            self.oscClientUI.send(msg)
            return
        else:
            print "grid seq edit is" + str(state.gridseqEdit) 
        grid, scale, root, columnsub = self.stringToMiniState(self.gridStates[si].gridzz[ind])  
        self.putMiniStateLive(grid, scale, root, columnsub, si)
#        grid, scale = self.stringToGridKey(self.gridStates[si].gridzz[ind])
#        self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
#        self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
#        state.customScale = [1+i for i in scale]
#        state.grid = grid
#        state.scale = scale
#        state.prog = self.gridToProg(state.grid, state.scale, state.root)
    #new
    def pullUpGrid(self, grid, gridAddr): #add difG arguement? add reference to target grid object, and change object in this function itself?
        msg = OSC.OSCMessage()
        #print "pullup outside lock"
        #with self.lock:
        #print "updating grid of", gridAddr
        for i in range(len(grid)):
            for j in range(len(grid)):
                #if diG[i][j]
                msg.setAddress(gridAddr + "/"+str(i+1) +"/" + str(16-j))
                msg.append(grid[i][j])
                self.oscClientUI.send(msg)
                msg.clearData()
    
    def difGrid(self, g1, g2):
        difG = [[0 for i in range(len(g1))] for j in range(len(g2))]
        for i in range(len(g1)):
            for j in range(len(g2)):
                if g1[i][j] == g2[i][j]:    #assuming all grid values  jsut 0/1
                    difG[i][j] = False
                else:
                    difG[i][j] = True
        return difG
                
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
            self.gridStates[si].pianomode = False
#            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
#            self.oscServSelf.delMsgHandler("/played")
#            self.oscServSelf.addMsgHandler("/played", self.realPlay)
#            self.realPlay()
            return
        print "                      going to piano mode"
        #self.stopCallback()
        #print "                      stop callback returned"
        self.gridStates[si].pianomode = True
        msg = OSC.OSCMessage()
        msg.setAddress("/" + str((si+1)*2))
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
        playargs = []
        for m in range(si):
            k = phrase.Chord([-1])
            #k.type = "skip"
            playargs.append(k)
        playargs.append(self.gridStates[si].pianoprog.c[i])
        print "len playargs ", len(playargs)
        if(stuff[0] == 1):
            #print "piano on"
            phrase.play(playargs, toggle="on", list="yes")
        else:
            #print "piano off"
            phrase.play(playargs, toggle="off", list="yes")
    
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
            self.gridStates[si].pianoprog = self.gridToProg(self.gridStates[si].pianogrid, custScale, self.gridStates[si].root)
    
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
                
    def assignScale(self, addr, stuff, scale):
        print addr
        i = int(addr.split("/")[len(addr.split("/"))-2]) 
        if(stuff[0] != 0):
            scale.append(i)
            print "                added note to scale", i 
        else:
            if i in scale:
                scale.remove(i)
                print "                removed note from scale", i
        scale.sort()
        print scale
    
    #new        
    def gridClear(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        if state.gridseqEdit:
            state.gridseq[state.gridseqInd] = "blank"
            msg = OSC.OSCMessage()
            msg.setAddress("/" + str(si) + "/seqtext/" + str(state.gridseqInd))
            msg.append("b")
            self.oscClientUI.send(msg)
            return
        state.prog.c = [phrase.Chord([-1]) for i in range(16)]
        state.grid = [[0 for i in range(16)] for j in range (16)]
        self.pullUpGrid(state.grid, "/" +str(si+1) + "/grid")
        
    
    def stopCallback(self):
        #self.oscServSelf.close() #do we need to close server? probs not
        self.oscServSelf.delMsgHandler("/played")
        self.oscServSelf.addMsgHandler("/played", self.pianoModeMetronomeCatcher)
        print "                    thread closed"
        #self.audioThread.join()
    
    def pianoModeMetronomeCatcher(self, addr, tags, stuff, source):
        return
        
    def playStart(self):
        self.audioThread = threading.Thread(target=self.oscServSelf.serve_forever)
        #self.chuckThread.start()
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
            #self.chuckThread.join()
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
        #si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        filename = raw_input("Set Name: ")
        savefile = open(filename +".ss", "w")
        instruments = []
        for si in range(3):
            with self.gridStates[si].lock:
                
                savestr = []
                savestr.append(self.gridKeyToString(self.gridStates[si].grid, self.gridStates[si].scale))
                for i in self.gridStates[si].gridzz:
                    if i != 0:
                        savestr.append(i)
                print savestr
                instruments.append("\n".join(savestr))
        savefile.write("instrument".join(instruments))
        savefile.close()
        
    
    def loadGridFromFile(self, addr, tags, stuff, source):
        #si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        filename = raw_input("File Name: ")    
        filestr = open(filename).read()
        instruments = filestr.split("instrument")
        for si in range(3):
            with self.gridStates[si].lock:
                
                gridstrs = instruments[si].split("\n")
                #print gridstrs[0]
                grid, scale = self.stringToGridKey(gridstrs[0])
                self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
                self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
                self.gridStates[si].customScale = [1+i for i in scale]
                self.gridStates[si].grid = grid
                self.gridStates[si].scale = scale
                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
                for i in range(1, len(gridstrs)):
                    print "send hte save light message"
                    self.gridStates[si].gridzz[i-1] = gridstrs[i]
                    msg = OSC.OSCMessage()
                    msg.setAddress("/" +str(si+1) +"/gridsave/" + str(i) + "/1")
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
    
    def miniStateToString(self, grid, scale, root, colsub, si):
        state = self.gridStates[si]
        
        if state.subsets:
            colsublist = [str(i) for i in state.columnsub]
        else:
            colsublist = []
        colsubstring = ";".join(colsublist)
        
        rootstr = str(state.root)
        
        return self.gridKeyToString(state.grid, state.scale) + "+" + rootstr + "+" + colsubstring
        
    
    def stringToGridKey(self, string): #rename 
        gridstring = string.split("+")[0]
        colstr = gridstring.split(";")
        strgrid = [i.split(",") for i in colstr]
        grid = [[round(float(strgrid[i][j])) for i in range(len(strgrid))] for j in range(len(strgrid))]
        
        keystr = string.split("+")[1]
        strkey = keystr.split(",")
        key = [int(i) for i in strkey]
        return grid, key
        
    def stringToMiniState(self, string):
        grid, scale = self.stringToGridKey(string.split("+")[0]+"+"+string.split("+")[1])
        
        root = int(string.split("+")[2])
        if string.split("+")[3].split(";")[0] == "":
            colsub = []
        else:
            colsub = [int(i) for i in string.split("+")[3].split(";")]
        return grid, scale, root, colsub
        
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
            g = self.naiveNoise(self.gridStates[si].grid, self.gridStates[si].noiselev)
            #self.gridNoise(self.gridStates[si].noiselev, si)
#            with self.gridStates[si].lock:
#                self.gridStates[si].grid = g
#                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
#                self.pullUpGrid(g, "/" +str(si+1) + "/grid")
#            return
        if self.gridStates[si].noiseInd == 2:
            g = self.smartNoise(self.gridStates[si].grid, si)
#            with self.gridStates[si].lock:
#                self.gridStates[si].grid = self.smartNoise(self.gridStates[si].grid, si)
#                self.pullUpGrid(self.gridStates[si].grid, "/" + str(si+1) + "/grid")
#                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
#            return
        if self.gridStates[si].noiseInd == 3:
            print "game of life chosen"
            g = self.gridcopy(self.gridStates[si].grid)
            print "the level of noise is", self.gridStates[si].noiselev/2
            for i in range(self.gridStates[si].noiselev/2):
                g = self.gameOfLife(g)
                print "iteration number", i, "diff", self.gridDif(g, self.gridStates[si].grid)
#            with self.gridStates[si].lock:
#                self.gridStates[si].grid = g
#                self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
#                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
#            return  
        if self.gridStates[si].noiseInd == 4:
            g = self.simplify(self.gridStates[si].grid, self.gridStates[si].noiselev/2)
#            with self.gridStates[si].lock:
#                self.gridStates[si].grid = g
#                self.pullUpGrid(self.gridStates[si].grid, "/" +str(si+1) + "/grid")
#                self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
#            return   
        return g
    
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
    
    def naiveNoise(self, grid, lev):
        l = len(grid)
        p = 1.0 * lev / (l*l)
        newG = [[0 for i in range(l)] for k in range(l)]
        for i in range(l):
            for j in range(l):
                if random.uniform(0, 1) < p:
                    if grid[i][j] != 0:
                        newG[i][j] = 0
                    else: 
                        newG[i][j] = 1
                else: 
                    newG[i][j] = grid[i][j]
        return newG
    
    def getGridToSend(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        si = int(addr.split("/")[2])-1
        self.copyGrid = self.gridcopy(self.gridStates[si].grid)
        self.copyScale = copy.deepcopy(self.gridStates[si].scale)
        self.pullUpGrid(self.copyGrid, "/copyGrid")
        self.pullUpScale(self.copyScale, "/copyScale")
    
    def sendButtonTest(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        else:
            self.sendGrid()
    
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
        msg.append(self.gridKeyToString(self.copyGrid, self.copyScale)) #replace with edit grid?
        #print self.gridKeyToString(self.grid, self.scale)
        self.oscLANdiniClient.send(msg)
        print "sent"
    
    def recieveGrid(self, addr, tags, stuff, source):
        print stuff[0], "got it"
        grid, scale = self.stringToGridKey(stuff[0])
        self.recievedGrid = grid
        self.pullUpGrid(grid, "/recievedGrid")
        self.pullUpScale(scale, "/recievedScale")
        self.recievedScale = [i+1 for i in scale]
        print self.recievedScale
        
    def applyRecvGrid(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        si = int(addr.split("/")[2])-1
        with self.gridStates[si].lock:
            self.gridStates[si].grid = self.gridcopy(self.recievedGrid)
            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
        self.pullUpGrid(self.gridStates[si].grid, "/" + str(si+1) + "/grid")
        
    def applyRecvScale(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        si = int(addr.split("/")[2])-1
        with self.gridStates[si].lock:
            minN = min(self.recievedScale)
            self.gridStates[si].scale = [i - minN for i in self.recievedScale]
            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
        self.pullUpScale(self.gridStates[si].scale, "/" + str(si+1) + "/custScale")
    
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
                        msg.setAddress("/" + str(si+1) + "/grid/"+str(i+1) +"/" + str(16-j))
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
    
    def chuckThreadFunc(self):
        subprocess.call("chuck LooperBackendMulti.ck", shell=True)  
        
    def changePage(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1
        minipageNum = int(addr.split("/")[4]) - 1 #assuming column multiselect
        if stuff[0] == 1:
            for k in self.pageAddrs[minipageNum]:
                msg = OSC.OSCMessage()
                msg.setAddress("/" + str(si+1) + k + "/visible")
                msg.append(1)
                self.oscClientUI.send(msg)
                msg.clear()
        else:
            for k in self.pageAddrs[minipageNum]:
                msg = OSC.OSCMessage()
                msg.setAddress("/" + str(si+1) + k + "/visible")
                msg.append(0)
                self.oscClientUI.send(msg)
                msg.clear()
    
    def gridSeqToggleHandler(self, addr, tags, stuff, source):
        print "grid sequencing " + str(stuff[0])
        si = int(addr.split("/")[1]) - 1
        self.gridStates[si].gridseqFlag = (stuff[0] == 1)
        print "grid sequencing " + str(si+1) + " " + str(self.gridStates[si].gridseqFlag)
    
    def gridSeqEditHandler(self, addr, tags, stuff, source):
        print" grid sequence edit " + str(stuff[0])
        si = int(addr.split("/")[1]) - 1
        self.gridStates[si].gridseqEdit = (stuff[0] == 1)
        print "grid sequence edit" + str(self.gridStates[si].gridseqEdit)
    
    def gridSeqIndHandler(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print "in seq ind"
        si = int(addr.split("/")[1]) - 1
        if stuff[0] == 1:
            state = self.gridStates[si]
            state.gridseqInd = self.gridAddrInd(addr)[0]
            print" grid sequence index " + str(state.gridseqInd)
    
    def gridSeqClear(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1
        state = self.gridStates[si]
        state.gridseq = [-1]*8
        msg = OSC.OSCMessage()
        for i in range(8):
            msg.setAddress("/" + str(si+1) + "/seqtext/" + str(i+1))
            msg.append("-")
            self.oscClientUI.send(msg)
            msg.clear()
    
    def gridwiseStepSynch(self, addr, tags, stuff, source):
        return
            
    def putGridLive(self, grid, si):
        self.gridStates[si].grid = grid
        self.pullUpGrid(self.gridStates[si].grid, "/" + str(si+1) + "/grid")
        self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root) 
    
    def putMiniStateLive(self, grid, scale, root, columnsub, si):
        state = self.gridStates[si]
        with state.lock:
            state.customScale = [1+i for i in scale]
            state.grid = grid
            state.scale = scale
            state.root = root
            state.columnsub = columnsub
            msg = OSC.OSCMessage()
            if len(columnsub) == 0:
                state.subsets = False
                msg.setAddress("/" +str(si+1) + "/colsel")
                msg.append(0)
                self.oscClientUI.send(msg)
                msg.clear()
                
                #change UI, switch and selecors
            else:
                state.subsets = True
                msg.setAddress("/" +str(si+1) + "/colsel")
                msg.append(1)
                self.oscClientUI.send(msg)
                msg.clear()
            for i in range(16):
                msg.setAddress("/" +str(si+1) + "/col/" + str(i+1) + "/1")
                if i in columnsub:
                    msg.append(1)
                else:
                    msg.append(0)
                self.oscClientUI.send(msg)
                msg.clear()
                #change UI, switch and selecors
            state.prog = self.gridToProg(state.grid, state.scale, state.root)
            self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
            self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
    
    def seqtest(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print "           gridseqFlag", self.gridStates[0].gridseqFlag  
        
    
    
        
        
    
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
