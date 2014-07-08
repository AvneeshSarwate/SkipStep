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
import sys
import IPentry

class Looper:

    def __init__(self):
        #self.recvAddr = 
        self.progInd = 0#len(loopO)
        self.grid = [[0 for i in range(16)] for j in range (16)]
        self.refgrid = [[0 for i in range(16)] for j in range (16)]
        self.pianogrid = [[0 for i in range(16)] for j in range (16)]
        self.offlineGrid = [[0 for i in range(16)] for j in range (16)]
        self.prog = phrase.Progression()
        self.prog.c = [phrase.Chord([-1]) for i in range(16)]
        self.prog.t = [.25 for i in range(16)]
        self.pianoKeyDown = [0 for i in range(16)];
        self.pianoprog = phrase.Progression()
        self.pianoprog.c = [phrase.Chord([-1]) for i in range(16)]
        self.pianoprog.t = [.25 for i in range(16)]
        self.customScale = []
        self.refprog = 0
        self.root = 48
        self.scale = phrase.modes["maj5"]
        self.noisy = False
        self.columnsub = []
        self.offlineColsub = []
        self.subsets = False
        self.gridzz = [0 for i in range(8)]
        self.noiselev = 2
        self.refreshing = False
        self.arrowToggle = False
        self.stepIncrement = 1
        self.noiseInd = 1
        self.undoStack = []
        self.offlineUndoStack = []
        self.pianomode = False
        self.gridseq = [-1]*8
        self.gridseqInd = 0
        self.gridseqFlag = False
        self.gridseqEdit = False
        self.offlineEdit = False
        
        
        self.lock = threading.Lock()

class MultiLoop:
    
    
    ##initialization function that sets up all of the initial values, handlers, etc 
    def __init__(self, n, port):
        #self.recvAddr = 
        
        k = subprocess.check_output(["ifconfig | grep \"inet \" | grep -v 127.0.0.1"], shell=True)
        ip = k.split(" ")[1]
        selfIP = ip
        print "\n" + "Your computer's IP address is: " + selfIP + "\n enter this into your iPad"
        
        ipadFile = open("ipadIP.txt")
        oldIpadIP = ipadFile.read().strip("\n")
        ipadFile.close()
        self.iPadIP = oldIpadIP

        #sets the value of self.iPadIP
        print "pregui"
        ipGui = IPentry.IPApp(None, selfIP, oldIpadIP, self)
        ipGui.title('my application')
        ipGui.mainloop()

        iPadIP = self.iPadIP

        ipadFile = open("ipadIP.txt", "w")
        ipadFile.write(self.iPadIP)
        ipadFile.close()

        # iPadRead = raw_input("\n\nIs the IP address of your iPad " + oldIpadIP +"?" +
        #                    "\n If so, hit enter. If not, type it in below:\n")
        # if(iPadRead == ""): iPadIP = oldIpadIP
        # else:
        #     iPadIP = iPadRead
        #     ipadFile = open("ipadIP.txt", "w")
        #     ipadFile.write(iPadRead)
        #     ipadFile.close()
        
        self.num = n
        self.gridStates = []
        for i in range(n):
            self.gridStates.append(Looper())
        
        self.notenames = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
        
        self.pageAddrs = open("page1.txt").read().split(" ")
        self.miniPages = []
        self.miniPages.append(["/noisy", "/noiselev", "/noiseSel", "/refresh", "/clear", "/gridload", "/gridsave"])
        self.miniPages.append([])
        for i in self.pageAddrs:
            if i not in self.miniPages[0]: 
                self.miniPages[1].append(i)
        self.miniPages.append(["/seqedit", "/seqtoggle", "/gridseq", "/seqclear", "/stepMode"])
        self.miniPages[2] = self.miniPages[2] + ['/seqtext/' + str(i) for i in range(1, 9)]
        self.miniPages.append(["/miniSave", "/miniLoad", "/custScale", "/scaleApply", "/scene"])
        self.miniPages.append(["/pullGrid", "/offGrid", "/up", "/down", "/left", "/right", "/col", "/noiseHit", "/undo"])
        
        
        
        
        self.audioThread = 0
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", port)) #LANdini 50505, 5174 chuck
        self.oscServSelf.addDefaultHandlers()
        self.oscServSelf.addMsgHandler("/played", self.realPlay)
        #MultiMetronomoe: replace with lambda functions of self.realPlay(int(addr.split("/")[2]))
        
        self.oscServSelf.addMsgHandler("/tester", self.tester)
        self.oscServSelf.addMsgHandler("/stop", self.stopCallback)
        self.oscServUI = OSC.OSCServer((selfIP, 8000))
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect((iPadIP, 9000))
        self.iPadClients = []
        self.iPadClients.append(self.oscClientUI)
        #TODO: DONE replace for cli in self.iPadClients: cli.send(msg) #self.oscClientUI.send(msg) with loop over iPadClients
        #for cli in self.iPadClients: cli.send(msg)
        
        self.oscLANdiniClient = OSC.OSCClient()
        self.oscLANdiniClient.connect(("127.0.0.1", 50506))
        self.touchClient = OSC.OSCClient()
        self.touchClient.connect( ('127.0.0.1', 6449) )
        self.stepTrack = OSC.OSCMessage()
        
        for si in range(n):
            for i in range(2, len(self.miniPages)):
                for ad in (self.miniPages[i] + ["/pianoKey"]):
                    self.sendToUI("/" + str(si+1) + ad + "/visible", 0)
            self.sendToUI("/" + str(si+1) + "/pageSelector/1/" +str(len(self.miniPages)), 1) #used to be /pageSelector/1/3
            self.sendToUI("/" + str(si+1) + "pianoKey/visible", 0)
            self.sendToUI("/" + str(si+1) + "offGrid/visible", 0)
            
        #TODO:  self.oscServUI.addMsgHandler("/address", lambda addr, tags, stuff, source: bounceBack(addr, tags, stuff, source, callback)) #(callback can be a lambda function)
        
        self.gridcallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        self.pianocallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        self.offlinecallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
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
        
        self.noBounce = [] #addresses that do not get bounced to other pages 
        #self.noBounce.append("/tempo")
        for j in range(10):
            self.noBounce.append("/" + str(k+1) +"/pageSelector/1/"+str(j+1))
            self.noBounce.append("/"+str(i))
        
        self.oscServUI.addMsgHandler("/test", self.miniStateSave)
        
        self.oscServUI.addMsgHandler("/addiPad", self.addiPad)
        
        for i in range(16):
                self.oscServUI.addMsgHandler("/copyScale/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, lambda addr, tags, stuff, source: self.assignScale(addr, stuff, self.copyScale)))
            
        for i in range(16):
            self.oscServUI.addMsgHandler("/recievedScale/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, lambda addr, tags, stuff, source: self.assignScale(addr, stuff, self.recievedScale)))
        
        for i in range(16):
            for j in range(16):
                self.recievedcallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.recievedGrid, addr, stuff, 0)
                ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("recievedGrid/"+str(i+1)+"/"+str(j+1), lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.recievedcallbacks[i][j]))
        
        for i in range(16):
            for j in range(16):
                self.copycallbacks[i][j] = lambda addr, tags, stuff, source: self.assign2(self.copyGrid, addr, stuff, 0)
                ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                self.oscServUI.addMsgHandler("copyGrid/"+str(i+1)+"/"+str(j+1), lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.copycallbacks[i][j]))
        
        self.oscServUI.addMsgHandler("/sendGrid", self.sendButtonTest)
        self.oscServSelf.addMsgHandler("/recievedGrid", self.recieveGrid)
        
        self.oscServUI.addMsgHandler("/save", self.saveGridtoFile)
        self.oscServUI.addMsgHandler("/load", self.loadGridFromFile)
        
        for k in range(n):
            
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/miniSave", self.miniStateSave)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/miniLoad", self.miniStateLoad)
            
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/noisy", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.noiseFlip))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/colsel", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.colsubflip))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/piano", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.pianoModeOn))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/refresh", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.refreshHandler))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/scaleApply", self.applyCustomScale)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/up", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/down", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/left", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/right", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/arrowToggle", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.arrowTogHandler))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/clear", self.gridClear)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiseHit", self.noiseHit)
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/undo", self.undo)

            self.oscServUI.addMsgHandler("/" +str(k+1) +"/sync", self.indexSync)

            for j in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/scene/" + str(j) + "/1", self.scene)

            for j in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/gridseq/" + str(j) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.gridSeqIndHandler))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/seqtoggle", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.gridSeqToggleHandler))
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/seqedit", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.gridSeqEditHandler)) 
            self.oscServUI.addMsgHandler("/" +str(k+1) +"/seqclear", self.gridSeqClear)
            
            #need to add everything for moving piano mode grid back to main 
            
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/step/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.stepjump))
                #print "step jumper " + str(i + 1)
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/pianoKey/" + str(i+1) + "/1", self.pianoKey)
                
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/col/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.colsub))
                #print "step jumper " + str(i + 1)
            
            for i in range(5):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiselev/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.noiseLevHandler))
            
            for i in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/gridload/" + str(i+1) + "/1", self.gridload)
            
            for i in range(8):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/gridsave/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.saveGrid))
                
#            for i in range(16):
#                self.oscServUI.addMsgHandler("/" +str(k+1) +"/custScale/" + str(i+1) + "/1", self.custScale)
#            
            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/custScale/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, lambda addr, tags, stuff, source: self.assignScale(addr, stuff, self.gridStates[int(addr.split("/")[1])-1].customScale)))
                
            for i in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/noiseSel/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.noiseSelector))
            
            for i in range(16):
                for j in range(16):
                    self.gridcallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].grid, addr, stuff, self.gridStates[int(addr.split("/")[1])-1].prog)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/grid/"+str(i+1)+"/"+str(j+1), lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.gridcallbacks[k][i][j]))
            
            for i in range(16):
                for j in range(16):
                    self.pianocallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].pianogrid, addr, stuff, self.gridStates[int(addr.split("/")[1])-1].pianoprog)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/pianoGrid/"+str(i+1)+"/"+str(j+1), lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.pianocallbacks[k][i][j]))
            
            for i in range(16):
                for j in range(16):
                    self.offlinecallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].offlineGrid, addr, stuff, 0)
                    ##print "grid ui listener " + str(i+1) + " " + str(j+1)
                    self.oscServUI.addMsgHandler("/" +str(k+1) +"/offGrid/"+str(i+1)+"/"+str(j+1), lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.offlinecallbacks[k][i][j]))
            
            for j in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) +"/pageSelector/1/"+str(j+1), self.changeMiniPage)
            
            self.oscServUI.addMsgHandler("/getGridScale/" +str(k+1) + "/1", self.getGridToSend)
            self.oscServUI.addMsgHandler("/applyRecvGrid/" +str(k+1) + "/1", self.applyRecvGrid)
            self.oscServUI.addMsgHandler("/applyRecvScale/" +str(k+1) + "/1", self.applyRecvScale)
            
            self.updateNoteLabels(self.gridStates[k].scale, k)
            
            #print "\n\n\nbuildcheck\n\n"
    #TODO: DONE for miniPage and piano mode, page changing should only happen for specific ipad that sent message
    

    def sendToUI(self, addr, *args):
        msg = OSC.OSCMessage()
        msg.setAddress(addr)
        for i in args: msg.append(i)
        for cli in self.iPadClients: cli.send(msg)




    ##wrapper function that allows for UI synchronization in "google docs mode"
    ##the function takes the input OSCmessage, calls the handler for the message
    ##and then sends the input message back out to the UI on all other iPads to update them 
    def bounceBack(self, addr, tags, stuff, source, callback):
        #TODO: DONE send stuff to addr (don't send it to where it came from (check source)
        if addr in self.noBounce:
            return
        
        if (not "step" in addr) and stuff[0] != 0:
            print "bounceback hit ", addr, stuff
        msg = OSC.OSCMessage()
        msg.setAddress(addr)
        for i in range(len(stuff)):
            msg.append(stuff[i])
        for cli in self.iPadClients:
            if cli.address()[0] != source[0]:
                cli.send(msg)
        callback(addr, tags, stuff, source)
    
    #TODO: DONE register this handler and add a control to UI
    def addiPad(self, addr, tags, stuff, source):
        print "add iPad stuff", stuff
        if stuff[0] == 0: return
        iPadIP = raw_input("\nEnter the IP address of your iPad (and set its port to 9000):")
        print "test 1"
        oscClient = OSC.OSCClient()
        oscClient.connect((iPadIP, 9000))
        print "test 2"
        self.iPadClients.append(oscClient)
    
    
    ##the function that handles everything that needs to happen during the "step" of a metronome
    ##is called when an OSC message from the ChucK metronome is recieved 
    def realPlay(self, *args): #MultiMetronome: give si as an argument, remove loops
        #print "aoibay"
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
                    self.sendToUI("/" + str(si+1) + "/step/" + str(playind+1) + "/1", 1)
                    ##print "in play"
                    chords.append(state.prog.c[playind]) # self.prog.c[playind] make this more efficient turn it into a PLAYER object?
                if state.refreshing and not state.pianomode:
                    ##print "                                   refresh", playind
                    self.refreshColumn(playind, si)
                #self.gridStates[si].loopInd += 1
                state.progInd += state.stepIncrement
            
                #self.gridNoise(self.noiselev)
                #print                               noise at", l
        phrase.play(chords[0], chords[1], chords[2], chords[3])
        
        #noise moved to after playing so noise calculations can be done in downtime while note is "playing"
        #could move other stuff into this loop as well if performance is an issue
        
        for si in range(self.num):
            state = self.gridStates[si]
            if (not state.subsets and (state.progInd == 16))  or (state.subsets and (state.progInd == len(state.columnsub))) or (state.progInd == -1):
                #print "LOOPEND " + str(si+1)
                #print "                      after gridend, before seq check"
                if state.gridseqFlag and sum(state.gridseq) != -8:
                    #print "                      after seq check"
                    state.progInd = 0 #this fixes a indexing bug when mixing subset and nonsubset mini states 
                    while state.gridseq[state.gridseqInd] == -1: 
                        state.gridseqInd = (state.gridseqInd + state.stepIncrement) % 8
                        print "       progressing to index", state.gridseqInd
                    
                    
                    print "GRID SEQUENCING CHANGE ", si+1, "seq ind is ", state.gridseqInd, "seq value is", state.gridseq[state.gridseqInd]
                    self.sendToUI("/" + str(si+1) + "/gridseq/" + str(state.gridseqInd+1) + "/1", 1)
                    
                    if state.gridseq[state.gridseqInd] == "blank": 
                        g = [[0 for i in range(16)] for j in range(16)]
                        scale = state.scale
                        root = state.root
                        colsub = []
                    else:
                        #g = self.stringToGridKey(state.gridzz[state.gridseq[state.gridseqInd]])[0]
                        g, scale, root, colsub = self.stringToMiniState(state.gridzz[state.gridseq[state.gridseqInd]])
                    #print "          g is grid number ", state.gridseq[state.gridseqInd], "of length ", len(g)
                    
                    if state.noisy:
                        g = self.noiseChoice(si)
                        if not state.refreshing:
                            #state.gridzz[state.gridseq[state.gridseqInd]] = self.gridKeyToString(g, state.scale)
                            state.gridzz[state.gridseq[state.gridseqInd]] = self.miniStateToString(g, scale, root, colsub, si)
                    with state.lock:
                        #self.putGridLive(g, si)
                        self.putMiniStateLive(g, scale, root, colsub, si) 
                    state.gridseqInd = (state.gridseqInd + state.stepIncrement) % 8
                    print "done with sequencing update"
                    
                else:
                    #print "NOT SEQUENCING ", si+1
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
        
                
    ##is called to return columns to their saved state when snapshot mode is on 
    def refreshColumn(self, k, si):
        state = self.gridStates[si]
        for i in range(len(state.grid)):
            if(state.refgrid[k][i] != state.grid[k][i]):
                #print "                            single element refresh", k+1, i+1, self.refgrid[k][i]
                self.sendToUI("/" + str(si+1) + "/grid/" + str(k+1) + "/" + str(16-i), state.refgrid[k][i])
                state.grid[k][i] = state.refgrid[k][i]
        state.prog.c[k] = self.gridStates[si].refprog.c[k]
    
    ##is the hanlder for the snapshot mode control
    def refreshHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        #print "                     hit ref handler", stuff, stuff[0] != 0
        if stuff[0] != 0:
            #print "                    in conditional"
            state.refreshing = True
            state.refprog = phrase.Progression(state.prog)
            #print type(self.refprog), "refprog", "before"
            state.refgrid = self.gridcopy(state.grid)
            #print len(self.prog), ":prog", len(self.refprog), ":refprog"
            print "                           refresh on"
        else:
            state.refreshing = False
            print "                           refresh off"   

    def indexSync(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1
        syncInd = self.gridStates[si].progInd
        for i in range(self.num):
            self.gridStates[i].progInd = syncInd
    
    ##is the handler for the stepjump control 
    def stepjump(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        if stuff[0] != 0:
            state.progInd, j = self.gridAddrInd(addr) #replace with gridAddrInd
            if state.subsets:
                if state.progInd in state.columnsub:
                    state.progInd = state.columnsub.index(state.progInd)
                else:
                    if state.progInd > state.columnsub[-1]:
                        state.progInd = len(state.columnsub) - 1
                        return
                    i = len(state.columnsub) - 1
                    while state.columnsub[i] >= state.progInd:
                        state.progInd = state.columnsub[i]
                        i -= 1
                    
            print "                                jumped to " + str(self.gridStates[si].progInd)
    
    ## is the hanlder for the grid noise toggle control 
    def noiseFlip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        print "                               noise flip " + str(stuff[0] == 1)
        state.noisy = (stuff[0] == 1)
    
    ## is the hanlder for the noise level control 
    def noiseLevHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        i, j = self.gridAddrInd(addr)
        self.gridStates[si].noiselev = 2 * (i+1)
    
    ##is the hanlder for the column subset control 
    def colsub(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        ind, j = self.gridAddrInd(addr) #replace with gridAddrInd
        if state.offlineEdit:
            colvar = state.columnsub
        else:
            colvar = state.offlineColsub

        if stuff[0] == 1 and ind not in colvar: #do we need 2nd conditional?
            colvar.append(ind)
            print "                            added " + str(ind)
        if stuff[0] == 0 and ind in colvar:
            colvar.remove(ind)
            print "                            removed " + str(ind)
        colvar.sort()
    
    #i#s the hanlder for the column sub toggle control 
    def colsubflip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        #print "                             gottem yo", self.progInd
        with state.lock:
            #print "                             inside lock ", self.progInd
            state.subsets = (stuff[0] == 1)
            #print "                             past bool", self.subsets 
            state.progInd = 0 if stuff[0] == 1 else state.columnsub[state.progInd]
            print "                      colsub ", str(state.subsets), "progind" + str(state.progInd)
        
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
    
    ##is the hanlder for the grid save control 
    def saveGrid(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        ind, j = self.gridAddrInd(addr)
        if stuff[0] != 0:
            #state.gridzz[ind] = self.gridKeyToString(state.grid, state.scale)#self.gridStates[si].gridcopy()
            if state.offlineEdit:
                print "OFFLINE SAVE", self.gridDif(state.offlineGrid, state.grid)             
                state.gridzz[ind] = self.miniStateToString(state.offlineGrid, state.scale, state.root, state.offlineColsub, si)
            else:
                state.gridzz[ind] = self.miniStateToString(state.grid, state.scale, state.root, state.columnsub, si)
        else: 
            state.gridzz[ind] = 0 #or -1??
    
    ##is the hanlder for the grid load control
    def gridload(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        ind = self.gridAddrInd(addr)[0]
        if stuff[0] == 0: return
        if state.gridseqEdit:
            state.gridseq[state.gridseqInd] = ind
            print "/" + str(si+1) + "/seqtext/" + str(state.gridseqInd)
            self.sendToUI("/" + str(si+1) + "/seqtext/" + str(state.gridseqInd+1), str(ind+1))
            return
        else:
            if state.offlineEdit:
                grid, scale, root, columnsub = self.stringToMiniState(state.gridzz[ind])
                self.offlineGrid = grid
                self.offlineColsub = columnsub
                self.pullUpGrid(grid, "/" + str(si+1) + "/offlineGrid")
                self.pullUpScale(scale, "/" + str(si+1) + "/custScale")
                self.pullUpColSub(columnsub, "/" + str(si+1) + "/col")
            print "grid seq edit is" + str(state.gridseqEdit) 
            grid, scale, root, columnsub = self.stringToMiniState(state.gridzz[ind])  
            self.putMiniStateLive(grid, scale, root, columnsub, si)
#        

    ##is the hanlder for the simple scene control 
    def scene(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        ind, j = self.gridAddrInd(addr)
        for i in range(1, self.num+1):
            state = self.gridStates[i-1]
            if state.gridzz[ind] != 0:
                print "/" + str(i) + addr[2:len(addr)]
                self.gridload("/" + str(i) + addr[2:len(addr)], tags, stuff, source)
            else:
                self.putMiniStateLive([[0 for i in range(16)] for j in range (16)], state.scale, state.root, state.columnsub, i-1)


    ## is the helper function used to take a grid and display it in the specified grid UI element  
    def pullUpGrid(self, grid, gridAddr): #add difG arguement? add reference to target grid object, and change object in this function itself?
        #print "pullup outside lock"
        #with self.lock:
        #print "updating grid of", gridAddr
        for i in range(len(grid)):
            for j in range(len(grid)):
                #if diG[i][j]
                self.sendToUI(gridAddr + "/"+str(i+1) +"/" + str(16-j), grid[i][j])
    
    ## counts the hamming distance between grids 
    def difGrid(self, g1, g2):
        difG = [[0 for i in range(len(g1))] for j in range(len(g2))]
        for i in range(len(g1)):
            for j in range(len(g2)):
                if g1[i][j] == g2[i][j]:    #assuming all grid values  jsut 0/1
                    difG[i][j] = False
                else:
                    difG[i][j] = True
        return difG
    
    ## is the helper function used to take a scale and display it in the specified scale UI element      
    def pullUpScale(self, scale, scaleAddr):
        print "           ", scale 
        for i in range(12):
            if i in scale:
                self.sendToUI(scaleAddr + "/"+ str(i+1) +"/1", 1)
            else:
                self.sendToUI(scaleAddr + "/"+ str(i+1) +"/1", 0)  

    def pullUpColSub(self, columnsub, colAddr, sel=""): ##TODO: add this to putMiniStateLive()
        if sel != "":
            if len(columnsub) == 0:
                self.sendToUI(selAddr, 0)        
                #change UI, switch and selecors
            else:
                self.sendToUI(selAddr, 1)
        for i in range(16):
            if i in columnsub:
                self.sendToUI(colAddr + "/" + str(i+1) + "/1", 1)
            else:
                self.sendToUI(colAddr + "/" + str(i+1) + "/1", 0)

    
    ## is the hanlder for the piano mode toggle control 
    def pianoModeOn(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        #switch tab to piano mode tab
        if(stuff[0] == 0):
            state.pianomode = False
#            self.gridStates[si].prog = self.gridToProg(self.gridStates[si].grid, self.gridStates[si].scale, self.gridStates[si].root)
#            self.oscServSelf.delMsgHandler("/played")
#            self.oscServSelf.addMsgHandler("/played", self.realPlay)
#            self.realPlay()

            for ad in ["/step", "/col", "/colsel"]:
                msg = OSC.OSCMessage()
                msg.setAddress("/" + str(si+1) + ad + "/visible")
                msg.append(1)
                for cli in self.iPadClients: 
                    if cli.address()[0] == source[0]:
                        cli.send(msg) #self.oscClientUI.send(msg)

            msg = OSC.OSCMessage()
            msg.setAddress("/" + str(si+1) + "/pianoKey/visible")
            msg.append(0)
            for cli in self.iPadClients: 
                if cli.address()[0] == source[0]:
                    cli.send(msg) #self.oscClientUI.send(msg)
            return
        print "                      going to piano mode"
        #self.stopCallback()
        #print "                      stop callback returned"
        state.pianomode = True

        for ad in ["/step", "/col", "/colsel"]:
            msg = OSC.OSCMessage()
            msg.setAddress("/" + str(si+1) + ad + "/visible")
            msg.append(0)
            for cli in self.iPadClients: 
                if cli.address()[0] == source[0]:
                    cli.send(msg) #self.oscClientUI.send(msg)

        msg = OSC.OSCMessage()
        msg.setAddress("/" + str(si+1) + "/pianoKey/visible")
        msg.append(1)
        for cli in self.iPadClients: 
            if cli.address()[0] == source[0]:
                cli.send(msg) #self.oscClientUI.send(msg)

        state.pianogrid = self.gridcopy(state.grid)
        state.pianoprog = self.gridToProg(state.pianogrid, state.scale, state.root)
        self.pullUpGrid(state.pianogrid, "/" +str(si+1) + "/pianoGrid")
        #hanlders for "piano keys" should already be set up
        return
    #SHOULD PIANO GRID BE EDITABLE AND SHOULD EDITS UPDATE TO MAIN GRID
    
    ## is the hanlder for the piano key control 
    def pianoKey(self, addr, tags, stuff, source): #set up handler using lambda functions like with normal grid 
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        i, j = self.gridAddrInd(addr)
        print i
        playargs = []
        for m in range(si):
            k = phrase.Chord([-1])
            #k.type = "skip"
            playargs.append(k)
        print "len playargs ", len(playargs)
        if(stuff[0] == 1):
            playargs.append(state.prog.c[i])
            state.pianoKeyDown[i] = copy.deepcopy(state.prog.c[i])
            #print "piano on"
            phrase.play(playargs, toggle="on", list="yes")
        else:
            #print "piano off"
            playargs.append(state.pianoKeyDown[i])
            phrase.play(playargs, toggle="off", list="yes")
            if state.refreshing:
                ##print "                                   refresh", playind
                self.refreshColumn(i, si)

    ## is the hanlder for the apply custom scale control 
    def applyCustomScale(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0:
            return
        state = self.gridStates[si]
        with state.lock:
            custScale = [i - min(state.customScale) for i in state.customScale]
            custScale.sort()
            print custScale
            state.scale = custScale
            state.prog = self.gridToProg(state.grid, custScale, state.root)
            state.pianoprog = self.gridToProg(state.pianogrid, custScale, state.root)
        self.updateNoteLabels(state.scale, si)
    
    ## is the handler for the scale definer control 
    def custScale(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        i, j = self.gridAddrInd(addr)
        if(stuff[0] != 0):
            state.customScale.append(i)
            print "                added note to scale", i 
        else:
            if i in state.customScale:
                state.customScale.remove(i)
                print "                removed note from scale", i
    
    ## unused             
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
    
    ## is hanlder for the grid clear control       
    def gridClear(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print source, addr
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        if state.offlineEdit:
            state.offlineGrid = [[0 for i in range(16)] for j in range (16)]
            self.pullUpGrid(state.offlineGrid, "/" +str(si+1) + "/offGrid")
        if state.gridseqEdit:
            state.gridseq[state.gridseqInd] = "blank"
            self.sendToUI("/" + str(si+1) + "/seqtext/" + str(state.gridseqInd+1), "b")
            return
        state.prog.c = [phrase.Chord([-1]) for i in range(16)]
        state.grid = [[0 for i in range(16)] for j in range (16)]
        self.pullUpGrid(state.grid, "/" +str(si+1) + "/grid")
        
    ## unused
    def stopCallback(self):
        #self.oscServSelf.close() #do we need to close server? probs not
        self.oscServSelf.delMsgHandler("/played")
        self.oscServSelf.addMsgHandler("/played", self.pianoModeMetronomeCatcher)
        print "                    thread closed"
        #self.audioThread.join()
    
    ##unsued 
    def pianoModeMetronomeCatcher(self, addr, tags, stuff, source):
        return
    
    ##is used to start the threading in the SkipStep initialization     
    def playStart(self):
        self.audioThread = threading.Thread(target=self.oscServSelf.serve_forever)
        #self.chuckThread.start()
        self.audioThread.start()
        self.realPlay()
    
    ##is used to start the threading in the SkipStep initialization 
    def uiStart(self):
        self.uiThread = threading.Thread(target=self.oscServUI.serve_forever)
        self.uiThread.start()
    
    ## unused 
    def oi(self, addr, tags, stuff, source):
        print "yo"
    
    ## starts the threads and listens for messages, startking SkipStep 
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
    ##unused
    def tester(self, *args):
        print "hurr"
    
    ##unused
    def default(self, *args):
        print "default"
    
    ##unused 
    def check(self):
        for addr in self.oscServSelf.getOSCAddressSpace():
            print addr
        for addr in self.oscServUI.getOSCAddressSpace():
            print addr
    
    ## converts a grid into a phrase.prog object 
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
    
    ## is the hanlder for the arrow toggle control
    def arrowTogHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        self.gridStates[si].arrowToggle = (stuff[0] == 1)
    
    ## is a function that takes a grid and "shifts" it the specified direction (up, down, left right)
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
    
    ## is the hanlder for the arrow pad control
    def gridShiftHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0:
            return
        state = self.gridStates[si]
        direction = addr.split("/")[2]
        print "                   direction:", direction
        if(state.arrowToggle):
            if direction == "left":
                state.stepIncrement = -1
            if direction == "right":
                state.stepIncrement = 1
            if direction == "up":
                state.root += 1
                with state.lock:
                    state.prog = self.gridToProg(state.grid, state.scale, state.root)
                self.updateNoteLabels(state.scale, si)
            if direction == "down":
                state.root -= 1
                with state.lock:
                    state.prog = self.gridToProg(state.grid, state.scale, state.root)
                self.updateNoteLabels(state.scale, si)
                    
        else:

            if state.offlineEdit:
                print "offline shift", direction
                g = self.gridShift(state.offlineGrid, direction)

                print self.gridDif(g, state.offlineGrid)

                state.offlineGrid = g
                print self.gridDif(state.offlineGrid, state.grid), "SHOULD BE DIF"
                self.pullUpGrid(state.offlineGrid, "/" +str(si+1) + "/offGrid")
            else: 
                print "shift", direction
                g = self.gridShift(state.grid, direction)
                print self.gridDif(g, state.grid)
                with state.lock:
                    state.grid = g
                    state.prog = self.gridToProg(state.grid, state.scale, state.root)
                self.pullUpGrid(state.grid, "/" +str(si+1) + "/grid")
            
    ## takes a scale and a root note and returns a list of 16 notes from the scale starting from the root 
    def scaleNotes(self, root, scale):
        notes = [0]*16
        for i in range(16):
            notes[i] = root + (i/len(scale))*12 + scale[i%len(scale)] 
#            #print i, (i/len(scale))*12, i%len(scale)
        return notes 
    
    ## converts a column in a grid into a phrase.chord object   
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
    
    ## takes an OSC addres of a grid or selector from the touchOSC ui and returns the corrdinates of the picked element 
    def gridAddrInd(self, addr):
        s = addr.split("/")
        i = int(s[3])-1
        j = 16-int(s[4])
        return i, j
    
    ## unused   
    def indToUIInd(self, i, j):
        return i+1, 16-j

    ## sums the number of on elements in the grid 
    def gridSum(self, grid):
        return sum([sum(k) for k in grid])
    
    ## helper function that turns on a specified element in a specified grid 
    ## is almost function, but is used inside a lambda function that is the actual hanlder 
    def assign2(self, a, b, c, d): #a - grid, b - addr, c - stuff, d - prog  
        si = int(b.split("/")[1]) - 1 #index of grid action was taken on
        state = self.gridStates[si]
        print si 
        with state.lock:
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
            d.c[i] = self.colToChord(a[i], state.root, state.scale)
            #print self.prog, "\n\n\n"        
    
    
    def saveGridtoFile(self, addr, tags, stuff, source):
        #si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        filename = "savefile" #raw_input("Set Name: ")
        savefile = open(filename +".ss", "w")
        instruments = []
        for si in range(3):
            state = self.gridStates[si]
            with state.lock:
                
                savestr = []
                savestr.append(self.gridKeyToString(state.grid, state.scale))
                for i in state.gridzz:
                    if i != 0:
                        savestr.append(i)
                print savestr
                instruments.append("\n".join(savestr))
        savefile.write("instrument".join(instruments))
        savefile.close()
        
    
    def loadGridFromFile(self, addr, tags, stuff, source):
        #si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0: return
        filename = "savefile.ss" #raw_input("File Name: ")    
        filestr = open(filename).read()
        instruments = filestr.split("instrument")
        for si in range(3):
            state = self.gridStates[si]
            with state.lock:
                
                gridstrs = instruments[si].split("\n")
                #print gridstrs[0]
                grid, scale = self.stringToGridKey(gridstrs[0])
                self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
                self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
                state.customScale = [1+i for i in scale]
                state.grid = grid
                state.scale = scale
                state.prog = self.gridToProg(state.grid, state.scale, state.root)
                for i in range(1, len(gridstrs)):
                    print "send hte save light message"
                    state.gridzz[i-1] = gridstrs[i]
                    self.sendToUI("/" +str(si+1) +"/gridsave/" + str(i) + "/1", 1)
    

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
        
        return self.gridKeyToString(grid, scale) + "+" + rootstr + "+" + colsubstring
    
    def stateToString(self, si):
        state = self.gridStates[si]
        liveMini = self.miniStateToString(state.grid, state.scale, state.root, state.columnsub, si)
        miniList = []
        miniList.append(liveMini)
        for i in range(len(state.gridzz)):
            if state.gridzz[i] == 0:
                miniList.append("")
            else:
                miniList.append(state.gridzz[i])
        return ":".join(miniList)

    def stringToState(self, stateString, si):
        state = self.gridStates[si]
        miniStrList = stateString.split(":")
        grid, key, root, col = self.stringToMiniState(miniStrList[0])
        self.putMiniStateLive(grid, key, root, col, si)
        for i in range(len(state.gridzz)):
            if miniStrList[i+1] == "":
                state.gridzz[i] = 0
            else:
                state.gridzz[i] = miniStrList[i+1]
                self.sendToUI("/" + str(si+1) + "/gridsave/" + str(i+1) + "/1", 1)

    def saveState(self, si):
        f = open("savefile" + str(si) + ".ss", "w")
        f.write(self.stateToString(si))
        f.close()

    def loadState(self, si):
        stateStr = open("savefile" + str(si) + ".ss").read()
        self.stringToState(stateStr, si)

    
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
    
    ## helper function for game of life that counts the number of neighbors (with wraparound) of a cell     
    def neighborCount(self, grid, i, j):
        count = 0
        for m in [-1, 0, 1]:
            for k in [-1, 0, 1]:
                if abs(m) + abs(k) == 0:
                    continue
                if grid[(i+m)%len(grid)][(j+k)%len(grid)] != 0:
                    count += 1
        return count       
    
    ## transformation function that transforms a grid to its next step according to conways game of life     
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
    
    ## transformation function that varries the grid respecting its structure 
    def smartNoise(self, grid, noise):
        newgrid = [[0 for i in range(16)] for j in range (16)]
        vert = [i for i in range(1, 6)] + [i for i in range(-5, 0)]
        hor = [i for i in range(1, 4)] + [i for i in range(-3, 0)]
        
        for i in range(len(grid)):
            for j in range(len(grid)):
                if grid[i][j] != 0:
                    if random.uniform(0, 1) < (1.0 * noise) / 10: #if any change happens
                        v = random.choice(vert)
                        h = random.choice(hor)
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

    ## transformation function that randomly drops columns from the grid 
    def rhythmBreak(self, grid, noise):
        newgrid = copy.deepcopy(grid)
        #newgrid2 = copy.deepcopy(grid)
        cols = range(16)
        if(random.uniform(0, 1) < .5):
            numDrop = 2*(noise-1) + 1
        else: 
            numDrop = 2*(noise-1) + 2
        colDrop = random.sample(cols, numDrop)
        print colDrop
        for i in colDrop:
            print i
            newgrid[i] = [0 for j in range(16)]
        print newgrid
        return newgrid

    ## transformation function that adds harmonies to the grid 
    def chordify(self, grid, noise):
        def smartNoiseMod(grid, noise):
            newgrid = [[0 for i in range(16)] for j in range (16)]
            vertRad = noise/2 + 1
            vert = [i for i in range(1, 1+vertRad)] + [i for i in range(-(1+vertRad), 0)]
    
            for i in range(len(grid)):
                for j in range(len(grid)):
                    if grid[i][j] != 0:
                        if random.uniform(0, 1) < (1.0 * noise) / 20: #if any change happens
                            v = random.choice(vert)
                            if random.uniform(0, 1) < .2: #probability of add/remove
                                if random.uniform(0, 1) < .5:
                                    newgrid[i][j] = 0
                                else:
                                    newgrid[(i)%len(grid)][(j+v)%len(grid)] = 1
                            else:
                                newgrid[i][(j+v)%len(grid)] = 1 
                        else:
                            newgrid[i][j] = 1
            return newgrid

        newgrid = copy.deepcopy(grid)
        offsetRange= range(1, 1+noise) + range(-noise, 0)
        offsets = random.sample(offsetRange, 2)

        gridz = [copy.deepcopy(newgrid), copy.deepcopy(newgrid)]
        for i in range(2):
            if offsets[i] > 0: direction = "up"
            else: direction = "down"
            for j in range(abs(offsets[i])):
                gridz[i] = self.gridShift(gridz[i], direction)
            gridz[i] = smartNoiseMod(gridz[i], noise)

        for g in gridz:
            for i in range(16):
                for j in range(16):
                    if g[i][j] != 0:
                        newgrid[i][j] = 1.0

        return newgrid


    ## hanlder for the transformation function selector control                         
    def noiseSelector(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1])  - 1 #index of grid action was taken on
        i, j = self.gridAddrInd(addr)
        print i+1, "noise selector"
        self.gridStates[si].noiseInd = i+1
    
    ## hanlder for the transformation trigger control 
    def noiseHit(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        if stuff[0] == 0: return
        grid = self.noiseChoice(si)
        if state.offlineEdit:
            state.offlineGrid = grid
            self.pullUpGrid(grid, "/" + str(si+1) + "/offGrid")
        else:
            self.putGridLive(grid, si)
        
    ## transformation function that picks up to k (k is voices) elements to leave on from each column 
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
    
    ## helper function that returns the grid from the selected transformation function at the selected noise level 
    def noiseChoice(self, si):
        state = self.gridStates[si]
        inputGrid = [[]]
        if state.offlineEdit:     ##TODO: should noiseChoice be responsible for managing undo-stack?
            inputGrid = self.gridcopy(state.offlineGrid)
            state.offlineUndoStack.append(self.gridcopy(state.offlineGrid))
        else:
            inputGrid = self.gridcopy(state.grid)
            state.undoStack.append(self.gridcopy(state.grid))
        print "the noise that was selected was", state.noiseInd

        if state.noiseInd == 1:
            g = self.chordify(inputGrid, state.noiselev/2)
            
        if state.noiseInd == 2:
            g = self.smartNoise(inputGrid, state.noiselev/2)
            
        if state.noiseInd == 3:
            g = self.rhythmBreak(inputGrid, state.noiselev/2)
            
        if state.noiseInd == 4:
            g = self.simplify(inputGrid, state.noiselev/2)
#             
        return g
    
    ## hanlder for the tap tempo control 
    def tempo(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print "sent touch message"
        msg = OSC.OSCMessage()
        msg.setAddress("/touch")
        msg.append("touched")
        self.touchClient.send(msg)

        msg.clear()
        msg.setAddress("/send/GD")
        msg.append("all")
        msg.append("/touch") #triggers tempo hit on ALL SkipStep.py, which then sends it to chuck back end
        msg.append("stuff")
        self.oscLANdiniClient.send(msg)
        
    ## hanlder for the undo button 
    def undo(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        if stuff[0] == 0: return
        if state.offlineEdit:
            print "offline undo"
            if len(state.offlineUndoStack) == 0: return
            self.offlineGrid = state.offlineUndoStack.pop()
            self.pullUpGrid(state.offlineGrid, "/" + str(si+1) + "/offGrid")
        else:
            if len(state.undoStack) == 0: return
            with state.lock:
                state.grid = state.undoStack.pop()
                state.prog = self.gridToProg(state.grid, state.scale, state.root)
                self.pullUpGrid(state.grid, "/" +str(si+1) + "/grid")
     
    def gridDif(self, g1, g2):
        hamming = 0
        print "hamming", len(g1), len(g2)
        for i in range(len(g1)):
            for j in range(len(g2)):
                if g1[i][j] != g2[i][j]: #both not zero or both zero
                    print i, j, "index check", g1[i][j], g2[i][j]
                    hamming += 1
        return hamming
    
    ## transformation function that randomly flips elements of the grid on or off 
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
        state = self.gridStates[si]
        self.copyGrid = self.gridcopy(state.grid)
        self.copyScale = copy.deepcopy(state.scale)
        self.pullUpGrid(self.copyGrid, "/copyGrid")
        self.pullUpScale(self.copyScale, "/copyScale")
    
    def sendButtonTest(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        else:
            self.sendGrid()
    
    def sendGrid(self):
        #recipient = raw_input("Who do you want to send a grid to: ")
        #print recipient

        self.destname = ""

        app = IPentry.SendNameGUI(None, self)
        app.title('my application')
        app.mainloop()

        recipient = self.destname

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
        state = self.gridStates[si]
        with state.lock:
            state.grid = self.gridcopy(self.recievedGrid)
            state.prog = self.gridToProg(state.grid, state.scale, state.root)
        self.pullUpGrid(state.grid, "/" + str(si+1) + "/grid")
        
    def applyRecvScale(self, addr, tags, stuff, source):
        if stuff[0] == 0:
            return
        si = int(addr.split("/")[2])-1
        state = self.gridStates[si]
        with state.lock:
            minN = min(self.recievedScale)
            state.scale = [i - minN for i in self.recievedScale]
            state.prog = self.gridToProg(state.grid, state.scale, state.root)
        self.pullUpScale(state.scale, "/" + str(si+1) + "/custScale")
    
    def gridNoise(self, k, si):
        #print "in noise"
        state = self.gridStates[si]
        with state.lock:
            #print "in lock"
            l = len(state.grid)
            p = 1.0 * k / (l*l)
            msg = OSC.OSCMessage()
            #make everything 1 instead of 14 in touchOSC
            for i in range(l):
                for j in range(l):
                    if random.uniform(0, 1) < p:
                        msg.setAddress("/" + str(si+1) + "/grid/"+str(i+1) +"/" + str(16-j))
                        if state.grid[i][j] != 0:
                            state.grid[i][j] = 0
                            self.sendToUI("/" + str(si+1) + "/grid/"+str(i+1) +"/" + str(16-j), 0)
                        else: 
                            state.grid[i][j] = 18
                            self.sendToUI("/" + str(si+1) + "/grid/"+str(i+1) +"/" + str(16-j), 18)
                state.prog.c[i] = self.colToChord(state.grid[i], state.root, state.scale)
            print "                                randomized"
            #self.prog = self.gridToProg(self.grid, self.scale, self.root)  
    
    ## unused   
    def changePage(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1
        minipageNum = int(addr.split("/")[4]) - 1 #assuming column multiselect
        if stuff[0] == 1:
            for k in self.pageAddrs[minipageNum]:
                self.sendToUI("/" + str(si+1) + k + "/visible", 1)
            
        else:
            for k in self.pageAddrs[minipageNum]:
                self.sendToUI("/" + str(si+1) + k + "/visible", 0)
            
    
    ## hanlder for the grid sequence toggle control 
    def gridSeqToggleHandler(self, addr, tags, stuff, source):
        print "grid sequencing " + str(stuff[0])
        si = int(addr.split("/")[1]) - 1
        state = self.gridStates[si]
        state.gridseqFlag = (stuff[0] == 1)
        print "grid sequencing " + str(si+1) + " " + str(state.gridseqFlag)
    
    ## hanlder for the grid sequence edit toggle control 
    def gridSeqEditHandler(self, addr, tags, stuff, source):
        print" grid sequence edit " + str(stuff[0])
        si = int(addr.split("/")[1]) - 1
        self.gridStates[si].gridseqEdit = (stuff[0] == 1)
        print "grid sequence edit" + str(self.gridStates[si].gridseqEdit)
    
    ## hanlder for the grid sequence index selector control 
    def gridSeqIndHandler(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print "in seq ind"
        si = int(addr.split("/")[1]) - 1
        if stuff[0] == 1:
            state = self.gridStates[si]
            state.gridseqInd = self.gridAddrInd(addr)[0]
            print" grid sequence index " + str(state.gridseqInd)
    
    ## hanlder for the grid sequence clear control 
    def gridSeqClear(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1
        state = self.gridStates[si]
        state.gridseq = [-1]*8
        for i in range(8):
            self.sendToUI("/" + str(si+1) + "/seqtext/" + str(i+1), "-")
    
    def gridwiseStepSynch(self, addr, tags, stuff, source):
        return
            
    def putGridLive(self, grid, si):
        state = self.gridStates[si]
        state.grid = grid
        self.pullUpGrid(state.grid, "/" + str(si+1) + "/grid")
        state.prog = self.gridToProg(state.grid, state.scale, state.root) 
    
    ## helper function that takes the variables of a miniState and makes them the active mini state 
    def putMiniStateLive(self, grid, scale, root, columnsub, si):
        state = self.gridStates[si]
        #with state.lock:
        state.customScale = [1+i for i in scale]
        state.grid = grid
        state.scale = scale
        state.root = root
        state.columnsub = columnsub
        state.prog = self.gridToProg(state.grid, state.scale, state.root)
        if len(columnsub) == 0:
            state.subsets = False
            self.sendToUI("/" +str(si+1) + "/colsel", 0)        
            #change UI, switch and selecors
        else:
            state.subsets = True
            self.sendToUI("/" +str(si+1) + "/colsel", 1)
        for i in range(16):
            if i in columnsub:
                self.sendToUI("/" +str(si+1) + "/col/" + str(i+1) + "/1", 1)
            else:
                self.sendToUI("/" +str(si+1) + "/col/" + str(i+1) + "/1", 0)
            #change UI, switch and selecors
        self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
        self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
        self.updateNoteLabels(scale, si)

    


    def miniStateSave(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split('/')[1]) - 1
        self.saveState(si)
        return
        # state = self.gridStates[0]
        # filename = "yodawg" #raw_input("Set Name: ")
        # savefile = open(filename +".ss", "w")
        # ministatestr = self.miniStateToString(state.grid, state.scale, state.root, [], si)
        # savefile.write(ministatestr)
        # savefile.close()
    
    def miniStateLoad(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split('/')[1]) - 1
        self.loadState(si)
        return
        # state = self.gridStates[0]
        # filename = raw_input("File Name: ")
        # savefile = open(filename)
        # ministatestr = savefile.read()
        # grid, scale, root, columnsub = self.stringToMiniState(ministatestr)
        # print scale, root
        # self.putMiniStateLive(grid, scale, root, columnsub, si)
        # savefile.close()
    
    ## helper function that changes the note labels when a scale is changed 
    def updateNoteLabels(self, scale, si):
        notes = self.scaleNotes(self.gridStates[si].root, scale)
        print "in label update"
        for i in range(16):
            print self.notenames[notes[i]%12]
            self.sendToUI("/"+str(si+1)+"/notelabel/" + str(i+1), self.notenames[notes[i]%12])
            
    ## hanlder function for the minipage selector control 
    def changeMiniPage(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1
        state = self.gridStates[si]
        ind = 5 - int(addr.split("/")[4]) #used to be 4 - ...
        print "\nIND: ", ind, "\n"
        if stuff[0] == 1: 
            state.offlineEdit = (ind == 4) 
            if state.offlineEdit:
                state.offlineGrid = self.gridcopy(state.grid)
                state.offlineColsub = copy.deepcopy(state.columnsub)
                self.pullUpGrid(state.grid, "/" + str(si+1) + "/offGrid")
        msg = OSC.OSCMessage()
        print "miniPage address", addr
        for i in self.miniPages:
            print
            print i
        for ad in self.miniPages[ind]:
            msg.setAddress("/" + str(si+1) + ad + "/visible")
            msg.append(stuff[0])
            for cli in self.iPadClients: 
                if cli.address()[0] == source[0]:
                    cli.send(msg) #self.oscClientUI.send(msg)
            msg.clear()
                 
def startSoloBackend():
    subprocess.call("chuck LooperBackendSolo.ck", shell=True)

def startMasterBackend():
    subprocess.call("chuck LooperBackendMaster.ck", shell=True)

def startSlaveBackend():
    subprocess.call("chuck LooperBackendSlave.ck", shell=True)

def startLANdini():
    subprocess.call("open /Applications/LANdini.app", shell=True)
    
    
        
        
    
n = [60, 62, 64, 65]
t = [1, 1, 1, 1]
p = phrase.Phrase(n, t)
trans = [1, 2, 5, 1]
res = []
modeGui = IPentry.ModeSelect(None, res)
modeGui.title("Select Mode")
modeGui.mainloop()
subprocess.call("chuck --kill all", shell=True)
if res[0] == 0: #solo
    threading.Thread(target = startSoloBackend).start()
    port = 5174
    print res[0]
if res[0] == 1: #master
    threading.Thread(target = startMasterBackend).start()
    threading.Thread(target = startLANdini).start()
    port = 50505
    print res[0]
if res[0] == 2: #slave
    threading.Thread(target = startSlaveBackend).start()
    threading.Thread(target = startLANdini).start()
    port = 50505
    print res[0]
loop = MultiLoop(4, port)
#loop2 = Looper(p, trans)
#loop.check()
loop.uiStart()
loop.playStart()
loop.loopStart()
