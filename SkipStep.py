'''
Created on Nov 10, 2013

@author: Avneesh Sarwate
'''

import phrase
import threading
import OSC
import random
import copy
import subprocess
import IPentry

# the class that represnts all the data of a single "instrument state"
class Looper:

    def __init__(self):
        self.progInd = 0
        self.grid = [[0 for i in range(16)] for j in range (16)] # the data of the active grid
        self.refreshModeSavedGrid = [[0 for i in range(16)] for j in range (16)] # the data of the "saved" grid in refresh mode
        self.offlineGrid = [[0 for i in range(16)] for j in range (16)] # the data of the offline-edit grid
        self.prog = phrase.Progression() # object represnting the melodic content of the active grid 
        self.prog.c = [phrase.Chord([-1]) for i in range(16)] # initializing self.prog
        self.prog.t = [.25 for i in range(16)] # initialzing self.prog 
        self.pianoKeyDown = [0 for i in range(16)] # a list to track what piano keys are down to manage piano logic
        self.customScale = [] # the data of what scale is represented in the custom scale control  
        self.refreshModeSavedProg = 0 #  representing the melodic content of self.refreshModeSavedGrid 
        self.root = 48 # the "root note" of the grid
        self.scale = phrase.modes["minor"] # the scale that is being used to translate the grid into notes
        self.noisy = False # boolean for whether automatic varation is turned on
        self.columnSubsetLooping = [] # the data for what columns have been selected with the online looping column subset control
        self.offlineColumnSubsetLooping = [] # the data for what columns have been selected with the OFFLINE looping column subset control
        self.isColSubLooping = False # boolean for whether or not looping is ocurring over column subsets 
        self.algColumnSub = [] # the data for what columns have been selected with the algorithmic column subset control
        self.algSubsets = False # boolean for whether or not algorithms are occuring over column subsets 
        self.savedGrid = [0 for i in range(8)] # the object which stores the data of the "saved" miniStates
        self.noiselev = 2 # the "intensity" of the random variation as indicated by the intensity control
        self.refreshModeOn = False # boolean for whether or not refresh mode is on
        self.arrowToggle = False # boolean for whether or not the arrow toggles perform their alternate functions
        self.stepIncrement = 1 # number indicating whether looping is forwards (1) or backwards (-1)
        self.noiseInd = 1 # index determining which transofrmation function is selected 
        self.undoStack = [] # stack which saves grids when transformations are triggered, allowing "undoing" the transformation
        self.offlineUndoStack = [] # stack allowing for "undoing" when editing the offline grid 
        self.pianoModeIsOn = False # boolean indicating whether piano mode is active or not
        self.gridseq = [-1]*8 # object that stores what miniStates are assigned what position when they are sequenced
        self.gridseqInd = 0 # index for which miniState in the sequence is being played 
        self.gridseqFlag = False # boolean for whether or not miniState sequencing is ocurring 
        self.gridseqEdit = False # boolean for whether or not the miniState sequence is in edit mode
        self.offlineEdit = False # boolean for whether or not offline editing is occuring 
        self.metronomeToggled = True 
        self.rhythmInstSubsets = [] # set of indexes for the instruments will be affected by rhythm controls
        self.syncTypes = [] # set of indexes for what rhythmic synchronizations will be applied. order: [tempo, nexthit, index]
        self.skipHit = False #flag that determines whether to skip the handling of the metronome hit based on the residual time between a stepjump hit and the next metronome hit
        self.melodyStates = [MelodyState() for i in range(4)]
        self.melodyStateScreenInd = 0
        self.melodyStatePadInd = 0
        self.padTranspose = 0


        self.lock = threading.Lock()

class MelodyState:

    def __init__(self):
        self.startInd = 0
        self.grid = [[0 for i in range(16)] for j in range (16)] # the data of the active grid
        self.refreshModeSavedGrid = [[0 for i in range(16)] for j in range (16)] # the data of the "saved" grid in refresh mode
        self.prog = phrase.Progression() # object represnting the melodic content of the active grid
        self.prog.c = [phrase.Chord([-1]) for i in range(16)] # initializing self.prog
        self.prog.t = [.25 for i in range(16)] # initialzing self.prog
        self.customScale = copy.deepcopy(phrase.modes["minor"]+[]) #(create new object) # the data of what scale is represented in the custom scale control
        self.refreshModeSavedProg = 0 #  representing the melodic content of self.refreshModeSavedGrid
        self.root = 48 # the "root note" of the grid
        self.scale = copy.deepcopy(phrase.modes["minor"]) ##(create new object) # the scale that is being used to translate the grid into notes
        self.noisy = False # boolean for whether automatic varation is turned on
        self.columnSubsetLooping = [] # the data for what columns have been selected with the online looping column subset control
        self.isColSubLooping = False # boolean for whether or not looping is ocurring over column subsets
        self.algColumnSub = [] # the data for what columns have been selected with the algorithmic column subset control
        self.algSubsets = False # boolean for whether or not algorithms are occuring over column subsets
        self.noiselev = 2 # the "intensity" of the random variation as indicated by the intensity control (is 2xi where i is 1 based index of selector)
        self.refreshModeOn = False # boolean for whether or not refresh mode is on
        self.noiseInd = 1 # index determining which transofrmation function is selected (1 indexed)
        self.undoStack = [] # stack which saves grids when transformations are triggered, allowing "undoing" the transformation





class MultiLoop:
    
    
    ##initialization function that sets up all of the initial values, handlers, etc 
    def __init__(self, n, port):
        
        
        #finds the IP of the computer
        selfIP = subprocess.check_output("ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'", shell=True).replace("\n", "")
        print "\n" + "Your computer's IP address is: " + selfIP + "\n enter this into your iPad"

        #opens window to enter IP address of iPad, retrieves the entered value 
        ipadFile = open("ipadIP.txt")
        oldIpadIP = ipadFile.read().strip("\n")
        ipadFile.close()
        self.iPadIP = oldIpadIP
        print "pregui"
        ipGui = IPentry.IPApp(None, selfIP, oldIpadIP, self)
        ipGui.title('my application')
        ipGui.mainloop()
        iPadIP = self.iPadIP
        ipadFile = open("ipadIP.txt", "w")
        ipadFile.write(self.iPadIP)
        ipadFile.close()
        

        self.sceneInd = [-1]*4 # stores the selected indicies of the scene selectors
        self.sceneTogs = [False] * 4 # stores a boolean for each scene selector indicating whether or not it will be used
        self.recievedGrid = [[0 for i in range(16)] for j in range(16)] # the data of the grid recieved from over the network
        self.copyGrid = [[0 for i in range(16)] for j in range(16)] # the data from the grid being prepped to send over the network
        self.copyScale = [] # the data from the grid being prepped to send over the network
        self.recievedScale = [] # the data of the grid recieved from over the network
        self.num = n # the number of "instruments" used in SkipStep
        self.numMiniPages = 4 # the number of miniPages in the interface
        self.gridStates = [] # the array of Looper instances for each "instrument"
        self.doubleMap = {} # the dictionary that maps the addresses of the double-view grids to their corresponding miniState grids
        for i in range(n):
            self.gridStates.append(Looper())
        
        #helper object for updating note labels 
        self.notenames = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]


        # sets up OSC server that sends melodic information to ChucK
        self.audioThread = 0 # thread that is created from the server
        # server that sends the data  
        self.oscServSelf = OSC.OSCServer(("127.0.0.1", port)) #LANdini 50505, 5174 chuck
        self.oscServSelf.addDefaultHandlers()
        for i in range(self.num):
            self.oscServSelf.addMsgHandler("/played-" + str(i), self.realPlay)
        self.oscServSelf.addMsgHandler("/padHit", self.padHitResponder)
        self.oscServSelf.addMsgHandler("/padTranspose", self.padTransposeResponder)



        # OSC server that recieves messages from the iPad        
        self.oscServUI = OSC.OSCServer((selfIP, 8000))
        self.uiThread = 0
        self.oscServUI.addDefaultHandlers()

        # osc client for sending UI messages to the iPad 
        self.oscClientUI = OSC.OSCClient()
        self.oscClientUI.connect((iPadIP, 9000))

        # list of OSC clients for when multiple iPads are used to control a single SkipStep instance
        self.iPadClients = []
        self.iPadClients.append(self.oscClientUI)
        #TODO: DONE replace for cli in self.iPadClients: cli.send(msg) #self.oscClientUI.send(msg) with loop over iPadClients
        #for cli in self.iPadClients: cli.send(msg)
        
        # OSC client for sending messages to landini for networked performance 
        self.oscLANdiniClient = OSC.OSCClient()
        self.oscLANdiniClient.connect(("127.0.0.1", 50506))
 
        # OSC client for sending tap-tempo messages to Supercollider
        self.superColliderClient = OSC.OSCClient()
        self.superColliderClient.connect( ('127.0.0.1', 57120) ) #default superCollider port


        #organizes what controls are on what miniPages - NEW
        uiPageAddrs = open("newPages.txt").read().split('\n\n')
        self.miniPages = []
        self.miniPages.append(0) #miniPages is 1 indexed to match TouchOSC ui
        for i in range(1, self.num+1):
            self.miniPages.append([ad for ad in uiPageAddrs[i-1].split(" ")])

            #initializes the note labels 
            self.updateNoteLabels(self.gridStates[i-1].scale, i-1)

        for i in self.miniPages:
            print i 

        #hides the controls that are not on page 1
        for si in range(self.num):
            for i in range(2, self.numMiniPages+1):
                for ad in self.miniPages[i] + ["/pianoKey", "/scene", "/offGrid"]:
                    print "/" + str(i+1) + ad + "/visible"
                    self.sendToUI("/" + str(si+1) + ad + "/visible", 0.0)
            for ad in self.miniPages[1]:
                print "/" + str(si+1) + ad + "/visible"
                self.sendToUI("/" + str(si+1) + ad + "/visible", 1.0)


        #TODO: fill this in 
        self.noBounce = [] #addresses that do not get bounced to other pages 
            
        #TODO:  self.oscServUI.addMsgHandler("/address", lambda addr, tags, stuff, source: bounceBack(addr, tags, stuff, source, callback)) #(callback can be a lambda function)
        

        ##--------------- ASSIGNING CALLBACK HANLDERS TO OSC MESSAGES -------------------------

        self.gridcallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        self.pianocallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        self.offlinecallbacks = [[[0 for i in range(16)] for j in range (16)] for k in range(n)]
        
        self.recievedcallbacks = [[0 for i in range(16)] for j in range (16)]
        self.copycallbacks = [[0 for i in range(16)] for j in range (16)]
        
        self.oscServUI.addMsgHandler("/addiPad", self.addiPad)

        self.oscServUI.addMsgHandler("/save", self.saveSet)
        self.oscServUI.addMsgHandler("/load", self.loadSet)

        for k in range(n):
            
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/noisy", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.noiseFlip))
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/colsel", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.colsubflip))
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/funcSubToggle", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.algColsubFlip))
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/refresh", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.refreshHandler))
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/scaleApply", self.applyCustomScale)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/up", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/down", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/left", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/right", self.gridShiftHandler)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/arrowToggle", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.arrowTogHandler))
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/clear", self.gridClear)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/noiseHit", self.noiseHit)
            self.oscServUI.addMsgHandler("/" +str(k+1) + "/undo", self.undo)

            for i in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/miniStateSelect/" + str(i+1) + "/1", self.miniStateSelection)

            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/step/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.preStepJump))

            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/col/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.colsub))

            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/funcSub/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.algColsubHandler))
            
            for i in range(5):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/noiselev/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.noiseLevHandler))

            for i in range(16):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/custScale/" + str(i+1) + "/1", self.assignScale)
                
            for i in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/noiseSel/" + str(i+1) + "/1", lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.noiseSelector))
            
            for i in range(16):
                for j in range(16):
                    self.gridcallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].grid, addr, stuff, self.gridStates[int(addr.split("/")[1])-1].prog)
                    self.oscServUI.addMsgHandler("/" +str(k+1) + "/grid/" + str(i+1) + "/" + str(j+1),  self.simpleGridAssign)
            
            for i in range(16):
                for j in range(16):
                    self.offlinecallbacks[k][i][j] = lambda addr, tags, stuff, source: self.assign2(self.gridStates[int(addr.split("/")[1])-1].offlineGrid, addr, stuff, 0)
                    self.oscServUI.addMsgHandler("/" + str(k+1) + "/offGrid/" + str(i+1) + "/" + str(j+1), lambda addr, tags, stuff, source: self.bounceBack(addr, tags, stuff, source, self.offlinecallbacks[k][i][j]))

            for j in range(4):
                self.oscServUI.addMsgHandler("/" +str(k+1) + "/pageSelector/1/" + str(j+1), self.changeMiniPage)
            
            
    
    #TODO: for miniPage and piano mode, page changing should only happen for specific ipad that sent message
    

    #helper function for sending updates to touchOSC UI
    def sendToUI(self, addr, *args):
        msg = OSC.OSCMessage()
        msg.setAddress(addr)
        for i in args: msg.append(i)
        #print msg 
        for cli in self.iPadClients: cli.send(msg)


    ## wrapper function that allows for UI synchronization in "google docs mode"
    ## the function takes the input OSCmessage, calls the handler for the message
    ## and then sends the input message back out to the UI on all other iPads to update them 
    def bounceBack(self, addr, tags, stuff, source, callback):
        #TODO:  send stuff to addr (don't send it to where it came from (check source)

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
    

    #TODO:  register this handler and add a control to UI
    def addiPad(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        iPadIP = raw_input("\nEnter the IP address of your iPad (and set its port to 9000):")
        print "test 1"
        oscClient = OSC.OSCClient()
        oscClient.connect((iPadIP, 9000))
        print "test 2"
        self.iPadClients.append(oscClient)

    # stuff[0] is the gridState,
    # stuff[1] is which saved grid in the gridState needs to be pulled up
    # stuff[2] is the pad start position (ignored if it is 0)
    def padHitResponder(self, addr, tags, stuff, sournce):
        print "padHit", stuff
        state = self.gridStates[int(stuff[0])]
        state.melodyStatePadInd = int(stuff[1])

        melodyState = state.melodyStates[state.melodyStatePadInd]
        state.progInd = melodyState.startInd if int(stuff[2]) == 0 else int(stuff[2])
        msg = OSC.OSCMessage()
        msg.setAddress("/startMetronome")
        msg.append(stuff[0])
        msg.append(stuff[1])
        print "pulled up grid, sending back to SC to start metronome for instrument", stuff[0], "pad", stuff[1]
        self.superColliderClient.send(msg)

    def applyPadTranspose(self, chord, root, scale, transpose):
        sn = self.scaleNotes
        scaleNotes = list(set(sn(root-12, scale)) | set(sn(root, scale)) | set(sn(root+12, scale)))
        scaleNotes.sort()
        ch = phrase.Chord()
        #print scaleNotes
        for i in chord.n:
            if i == -1:
               return chord
            ch.append(scaleNotes[scaleNotes.index(i)+transpose])
        #print ch
        return ch

    #stuff[0] is the instrument index, stuff[1] is the value of the transpose
    def padTransposeResponder(self, addr, tags, stuff, sournce):
        state = self.gridStates[int(stuff[0])]
        state.padTranspose = int(stuff[1])
        print "insrtument", stuff[0], "tranpose", state.padTranspose

    def playChord(self, chord, channel = 0, piano = "normal", stepJumpFlag = False, progInd=-1):
        msg = OSC.OSCMessage()
        msg.setAddress("/playChord")
        msg.append(channel)
        msg.append(piano)
        msg.append(1 if stepJumpFlag else 0)
        msg.append(progInd)
        for i in chord.n:
            msg.append(i)
        self.superColliderClient.send(msg)

    ## function that determines what chord will be played based on the progInd
    def preChordPlay(self, si):
        colChord = phrase.Chord()  # placeholder 
        
        #calculates what column to play based on the index
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStatePadInd]
        with state.lock:
            if melodyState.isColSubLooping:
                state.progInd %= len(melodyState.columnSubsetLooping)
                playind = melodyState.columnSubsetLooping[state.progInd]
                
            else:
                state.progInd %= 16
                playind = state.progInd

            colChord = melodyState.prog.c[playind] # self.prog.c[playind] make this more efficient turn it into a PLAYER object?
            if melodyState.refreshModeOn:
                #print "pre refresh call "
                self.refreshColumn(playind, si)

        if state.padTranspose != 0:
            colChord = self.applyPadTranspose(colChord, melodyState.root, melodyState.scale, state.padTranspose)

        return colChord

    ## function that handles changing state (transformation functions, grid indexing, etc)
    ## that occurs when a loop repeats
    def postChordPlay(self, si):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStatePadInd]
        if (not melodyState.isColSubLooping and (state.progInd == 16))  or (melodyState.isColSubLooping and (state.progInd == len(melodyState.columnSubsetLooping))) or (state.progInd == -1):
            msg = OSC.OSCMessage()
            msg.setAddress("/lastBeats")
            msg.append(si)
            msg.append(state.melodyStatePadInd)
            self.superColliderClient.send(msg)
            if state.gridseqFlag and sum(state.gridseq) != -8:
                state.progInd = 0 #this fixes a indexing bug when mixing subset and nonsubset mini states 
                while state.gridseq[state.gridseqInd] == -1: 
                    state.gridseqInd = (state.gridseqInd + state.stepIncrement) % 8
                    print "       progressing to index", state.gridseqInd
                
                
                print "GRID SEQUENCING CHANGE ", si+1, "seq ind is ", state.gridseqInd, "seq value is", state.gridseq[state.gridseqInd]
                self.sendToUI("/" + str(si+1) + "/gridseq/" + str(state.gridseqInd+1) + "/1", 1)
                
                if state.gridseq[state.gridseqInd] == "blank": 
                    g = [[0 for i in range(16)] for j in range(16)]
                    scale = melodyState.scale
                    root = melodyState.root
                    colsub = []
                else:
                    g, scale, root, colsub = self.stringToMiniState(state.savedGrid[state.gridseq[state.gridseqInd]])
                
                if melodyState.noisy:
                    g = self.noiseChoice(si, True)
                    if not melodyState.refreshModeOn:
                        state.savedGrid[state.gridseq[state.gridseqInd]] = self.miniStateToString(g, scale, root, colsub, si)
                with state.lock:
                    self.putMiniStateLive(g, scale, root, colsub, si) 
                state.gridseqInd = (state.gridseqInd + state.stepIncrement) % 8
                print "done with sequencing update"
                
            else:
                #print "NOT SEQUENCING ", si+1
                if melodyState.noisy:
                    g = self.noiseChoice(si, True)
                    with state.lock:
                        self.putGridLive(g, si, True)

    ##the function that handles everything that needs to happen during the "step" of a metronome
    ##is called when an OSC message from the SuperCollider metronome is recieved
    ## stuff[0] is the instrument for which the metronome was hit
    ## stuff[1] is the melodyState to be switched to
    def realPlay(self, addr, tags, stuff, source): #MultiMetronome: give si as an argument, remove loops
        si = int(addr.split("-")[1])
        #print "                 played", si

        #calculates what column to play based on the index
        state = self.gridStates[si]
        state.melodyStatePadInd = int(stuff[1])
        melodyState = state.melodyStates[state.melodyStatePadInd]

        if state.skipHit: 
            state.skipHit = False
            return

        colChord = self.preChordPlay(si)
        #print "                 played", si, colChord

        #plays the chords that are defined by each column (phrase.play to be documented later)
        #print colChord, si
        self.playChord(colChord, channel = si, progInd=state.progInd)

        #updates progInd to the next step
        state.progInd += state.stepIncrement
        
        #noise moved to after playing so noise calculations can be done in downtime while note is "playing"
        #could move other stuff into this loop as well if performance is an issue
        self.postChordPlay(si)


                
    ## helper function is called to return columns to their saved state when snapshot mode is on 
    def refreshColumn(self, k, si):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStatePadInd]

        if melodyState.algSubsets:
            if not k in melodyState.algColumnSub: return

        print "REFRESH ON COL", k, "melodyScreenInd", state.melodyStateScreenInd, "melodyPadInd", state.melodyStatePadInd
        for i in range(len(melodyState.grid)):
            if melodyState.refreshmodeSavedGrid[k][i] != melodyState.grid[k][i]:
                if state.melodyStateScreenInd == state.melodyStatePadInd:
                    self.sendToUI("/" + str(si+1) + "/grid/" + str(k+1) + "/" + str(16-i), melodyState.refreshmodeSavedGrid[k][i])
                    print "VISUAL REFRESH ON", state.melodyStateScreenInd
                melodyState.grid[k][i] = melodyState.refreshmodeSavedGrid[k][i]
        melodyState.prog.c[k] = melodyState.refreshModeSavedProg.c[k]
    
    ## is the handler  for the snapshot mode control, OSCaddr: /si/refresh
    def refreshHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        if stuff[0] != 0:
            melodyState.refreshModeOn = True
            melodyState.refreshModeSavedProg = phrase.Progression(melodyState.prog)
            melodyState.refreshmodeSavedGrid = copy.deepcopy(melodyState.grid)
            print "                           refresh on"
        else:
            melodyState.refreshModeOn = False
            print "                           refresh off"

    def miniStateSelection(self, addr, tags, stuff, source):
        #TODO - create a pullUpMelodyState function
        if stuff[0] == 0: return

        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        ind, j = self.gridAddrInd(addr) #replace with gridAddrInd
        state.melodyStateScreenInd = ind
        melodyState = state.melodyStates[state.melodyStateScreenInd]


        self.pullUpGrid(melodyState.grid, "/" +str(si+1) + "/grid")
        print "grid pulled"
        self.pullUpScale(melodyState.scale, "/" +str(si+1) + "/custScale")
        print "scale pulled"
        self.updateNoteLabels(melodyState.customScale, si)
        print "note labels pulled"
        self.pullUpColSub(melodyState.columnSubsetLooping, melodyState.isColSubLooping, "/" + str(si+1) +"/col", selAddr="/" + str(si+1) +"/colsel")
        print "colsub pulled"
        self.pullUpAlgStatus(melodyState.noisy, melodyState.noiseInd, melodyState.noiselev/2, si) ##TODO: why is this x2? any good reasons?
        print "alg stuff pulled", melodyState.noisy, melodyState.noiseInd, melodyState.noiselev/2, si
        self.sendToUI("/" +str(si+1) + "/refresh", 1 if melodyState.refreshModeOn else 0)
        self.sendToUI("/" + str(si+1) + "/step/" + str(melodyState.startInd+1) + "/1", 1)
        print "refresh and start ind sent"

    def pullUpAlgStatus(self, algLooping, algSelection, algIntensity, si):
        self.sendToUI("/" +str(si+1) + "/noisy", 1 if algLooping else 0)
        self.sendToUI("/" +str(si+1) + "/noiseSel/" + str(algSelection) + "/1", 1)
        self.sendToUI("/" +str(si+1) + "/noiselev/" + str(algIntensity) + "/1", 1)

    ## is the handler  for the grid noise toggle control, OSCaddr: /si/noisy 
    def noiseFlip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        print "                               noise flip " + str(stuff[0] == 1)
        melodyState.noisy = (stuff[0] == 1)
    
    ## is the handler  for the noise level control, OSCaddr: /si/noiselev/i/1 
    def noiseLevHandler(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        i, j = self.gridAddrInd(addr)
        melodyState.noiselev = 2 * (i+1)
    
    ##is the handler  for the column subset control, OSCaddr: /si/col/i/1 
    def colsub(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        ind, j = self.gridAddrInd(addr) #replace with gridAddrInd
        s = ""
        if state.offlineEdit:
            colvar = state.offlineColumnSubsetLooping
            s = "OFFline"
        else:
            colvar = melodyState.columnSubsetLooping
            s = "online"

        if stuff[0] == 1 and ind not in colvar: #do we need 2nd conditional?
            colvar.append(ind)
            print s, colvar, "                            added " + str(ind)
        if stuff[0] == 0 and ind in colvar:
            colvar.remove(ind)
            print s, colvar, "                            removed " + str(ind)
        print "OFF COL", state.offlineColumnSubsetLooping
        print "ON COL ", melodyState.columnSubsetLooping
        colvar.sort()
    
    #i#s the handler  for the column sub toggle control, OSCaddr: /si/colsel/i/1
    def colsubflip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        with state.lock:
            melodyState.isColSubLooping = (stuff[0] == 1)
            state.progInd = 0 if stuff[0] == 1 else melodyState.columnSubsetLooping[state.progInd]
            print "                      colsub ", str(melodyState.isColSubLooping), "progind" + str(state.progInd)
        
    def algColsubHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        ind, j = self.gridAddrInd(addr) #replace with gridAddrInd
        colvar = melodyState.algColumnSub
        if stuff[0] == 1 and ind not in colvar: #do we need 2nd conditional?
            colvar.append(ind)
        if stuff[0] == 0 and ind in colvar:
            colvar.remove(ind)
        colvar.sort()

    def algColsubFlip(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        melodyState.algSubsets = (stuff[0] == 1)



    ## is the helper function used to take a grid and display it in the specified grid UI element  
    def pullUpGrid(self, grid, gridAddr): #add difG arguement? add reference to target grid object, and change object in this function itself?
        newGrid = self.rotateGridLeft(grid)
        for i in range(len(grid)):
            for j in range(len(grid)):
                self.sendToUI(gridAddr + "/"+str(i+1) +"/" + str(16-j), grid[i][j])
                if gridAddr in self.doubleMap.keys():
                    self.sendToUI(self.doubleMap[gridAddr] + "/"+str(i+1) +"/" + str(16-j), newGrid[i][j])
    
    ## helper function that calculates the "difference grid" between two grids
    @staticmethod
    def difGrid(g1, g2):
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

    def pullUpColSub(self, columnSubsetLooping, isColsubLooping, colAddr, selAddr=""): ##TODO: add this to putMiniStateLive()
        if selAddr != "":
            if isColsubLooping:
                self.sendToUI(selAddr, 1)
            else:
                self.sendToUI(selAddr, 0)
        for i in range(16):
            if i in columnSubsetLooping:
                self.sendToUI(colAddr + "/" + str(i+1) + "/1", 1)
            else:
                self.sendToUI(colAddr + "/" + str(i+1) + "/1", 0)


    ## is the handler  for the apply custom scale control,  OSCaddr: /si/scaleApply
    def applyCustomScale(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0:
            return
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        with state.lock:
            custScale = [i - min(melodyState.customScale) for i in melodyState.customScale]
            custScale.sort()
            print "custom scale", custScale
            melodyState.scale = custScale
            melodyState.prog = self.gridToProg(melodyState.grid, custScale, melodyState.root)
        self.updateNoteLabels(melodyState.scale, si)

    ## handler for custom-scale control OSCaddr: /si/custScale/i/1
    ## is used inside a lambda function that is the actual handler
    def assignScale(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        i = int(addr.split("/")[len(addr.split("/"))-2]) -1
        if stuff[0] != 0 and not i in melodyState.customScale:
            melodyState.customScale.append(i)
            print "                added note to scale", i 
        else:
            if i in melodyState.customScale:
                melodyState.customScale.remove(i)
                print "                removed note from scale", i
        melodyState.customScale.sort()
        for i in range(4):
            print "custom scale changed", state.melodyStates[i].customScale
    
    ## is handler  for the grid clear control, OSCaddr: /si/clear       
    def gridClear(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print source, addr
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        if state.offlineEdit:
            if melodyState.algSubsets:
                state.offlineGrid = self.columnOverlay(state.offlineGrid, [[0 for i in range(16)] for j in range (16)], melodyState.algColumnSub)
            else:
                state.offlineGrid = [[0 for i in range(16)] for j in range (16)]
            self.pullUpGrid(state.offlineGrid, "/" +str(si+1) + "/offGrid")
            return
        if state.gridseqEdit:
            state.gridseq[state.gridseqInd] = "blank"
            self.sendToUI("/" + str(si+1) + "/seqtext/" + str(state.gridseqInd+1), "b")
            return
        if melodyState.algSubsets:
            for i in melodyState.algColumnSub:
                melodyState.prog.c[i] = phrase.Chord([-1])
                melodyState.grid = self.columnOverlay(melodyState.grid, [[0 for i in range(16)] for j in range (16)], melodyState.algColumnSub)
        else:
            melodyState.prog.c = [phrase.Chord([-1]) for i in range(16)]
            melodyState.grid = [[0 for i in range(16)] for j in range (16)]
        self.pullUpGrid(melodyState.grid, "/" +str(si+1) + "/grid")
    
    
    ##is used to start the threading in the SkipStep initialization     
    def playStart(self):
        # self.audioThread = threading.Thread(target=self.oscServSelf.serve_forever)
        # #self.chuckThread.start()
        # self.audioThread.start()
        self.oscServSelf.serve_forever()
    
    ##is used to start the threading in the SkipStep initialization 
    def uiStart(self):
        # self.uiThread = threading.Thread(target=self.oscServUI.serve_forever)
        # self.uiThread.start()
        self.oscServUI.serve_forever()
    
    
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
    
    ## is the handler  for the arrow toggle control, OSCaddr: /si/arrowToggle
    def arrowTogHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        self.gridStates[si].arrowToggle = (stuff[0] == 1)
    
    ## is a helper function that takes a grid and "shifts" it the specified direction (up, down, left right)
    @staticmethod
    def gridShift(g, direction):
        grid = copy.deepcopy(g)
        
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
    
    ## is the handler  for the arrow pad control, OSCaddr: /si/up, /si/down, /si/left, /si/right
    def gridShiftHandler(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        if stuff[0] == 0:
            return
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        direction = addr.split("/")[2]
        print "                   direction:", direction
        if state.arrowToggle:
            if direction == "left":
                state.stepIncrement = -1
            if direction == "right":
                state.stepIncrement = 1
            if direction == "up":
                melodyState.root += 1
                with state.lock:
                    melodyState.prog = self.gridToProg(melodyState.grid, melodyState.scale, melodyState.root)
                print melodyState.root, melodyState.scale
                self.updateNoteLabels(melodyState.scale, si)
            if direction == "down":
                melodyState.root -= 1
                with state.lock:
                    melodyState.prog = self.gridToProg(melodyState.grid, melodyState.scale, melodyState.root)
                self.updateNoteLabels(melodyState.scale, si)
                    
        else:

            if state.offlineEdit:
                print "offline shift", direction
                g = self.gridShift(state.offlineGrid, direction)
                if melodyState.algSubsets:
                    g = self.columnOverlay(state.offlineGrid, g, melodyState.algColumnSub)

                print self.gridDif(g, state.offlineGrid)

                state.offlineGrid = g
                print self.gridDif(state.offlineGrid, melodyState.grid), "SHOULD BE DIF"
                self.pullUpGrid(state.offlineGrid, "/" +str(si+1) + "/offGrid")
            else: 
                print "shift", direction
                g = self.gridShift(melodyState.grid, direction)
                if melodyState.algSubsets:
                    g = self.columnOverlay(melodyState.grid, g, melodyState.algColumnSub)
                print self.gridDif(g, melodyState.grid)
                with state.lock:
                    melodyState.grid = g
                    melodyState.prog = self.gridToProg(melodyState.grid, melodyState.scale, melodyState.root)
                self.pullUpGrid(melodyState.grid, "/" +str(si+1) + "/grid")
            
    ## helper function that takes a scale and a root note and returns a list of 16 notes from the scale starting from the root
    @staticmethod
    def scaleNotes(root, scale):
        notes = [0]*16
        for i in range(16):
            notes[i] = root + (i/len(scale))*12 + scale[i%len(scale)] 
        return notes 
    
    ## helper function that converts a column in a grid into a phrase.chord object   
    def colToChord(self, col, root, scale):
        notes = self.scaleNotes(root, scale)
        if sum(col) == 0:
            return phrase.Chord([-1])
        else: 
            c = phrase.Chord()
            for j in range(len(col)):
                if col[j] != 0:
                    c.append(notes[j])
        return c

    def preStepJump(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        print "PRE JUMP"
        si = int(addr.split("/")[1]) - 1
        progInd, j = self.gridAddrInd(addr)
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        melodyState.startInd = progInd
        if state.isColSubLooping:
            if melodyState.startInd in state.columnSubsetLooping:
                state.progInd = state.columnSubsetLooping.index(melodyState.startInd)
            else:
                if melodyState.startInd > state.columnSubsetLooping[-1]:
                    state.progInd = len(state.columnSubsetLooping) - 1
                    self.sendToUI("/" + str(si+1) + "/step/" + str(state.progInd+1) + "/1", 1)
                    return
                i = len(state.columnSubsetLooping) - 1
                while state.columnSubsetLooping[i] >= melodyState.startInd and i > 0:
                    state.progInd = state.columnSubsetLooping[i]
                    i -= 1
                self.sendToUI("/" + str(si+1) + "/step/" + str(state.progInd+1) + "/1", 1)


    ## helper function that takes an OSC addres of a grid or selector from the touchOSC ui and returns the corrdinates of the picked element
    @staticmethod
    def gridAddrInd(addr):
        s = addr.split("/")
        i = int(s[3])-1
        j = 16-int(s[4])
        return i, j
    
    ## unused
    @staticmethod
    def indToUIInd(i, j):
        return i+1, 16-j

    ## helper function sums the number of on elements in the grid
    @staticmethod
    def gridSum(grid):
        return sum([sum(k) for k in grid])
    
    ## handler abstraction that turns on a specified element in a specified grid, OSCaddr: /si/grid, /si/offGrid, /recievedGrid, /copyGrid
    ## is used inside a lambda function that is the actual handler  
    def assign2(self, a, b, c, d): #a - grid, b - addr, c - stuff, d - prog
        si = int(b.split("/")[1]) - 1 #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        print si
        with state.lock:
            i, j = self.gridAddrInd(b)
            a[i][j] = c[0]
            print "grid count", self.gridSum(a)
            print "          assigned " + str(c[0]) + " to " + str(i+1) +" " + str(16-j), sum(a[i]) #correct?
            if d == 0:
                print "no prog"
                return
            d.c[i] = self.colToChord(a[i], melodyState.root, melodyState.scale)
            #print self.prog, "\n\n\n"

    def simpleGridAssign(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        with state.lock:
            i, j = self.gridAddrInd(addr)
            melodyState.grid[i][j] = stuff[0]
            print "grid count", self.gridSum(melodyState.grid )
            print "          assigned " + str(stuff[0]) + " to " + str(i+1) +" " + str(16-j), sum(melodyState.grid[i]) #correct?
            if melodyState.prog == 0:
                print "no prog"
                return
            melodyState.prog.c[i] = self.colToChord(melodyState.grid[i], melodyState.root, melodyState.scale)
            print melodyState.prog.c[i]

    def gridHandler(self, addr, tags, stuff, source):
        k = int(addr.split("/")[1]) - 1
        i = int(addr.split("/")[3]) - 1
        j = int(addr.split("/")[4]) - 1
        self.bounceBack(addr, tags, stuff, source, self.gridcallbacks[k][i][j])
        x, y = self.gridAddrInd(addr)
        addrStem = "/".join(addr.split("/")[0:3])
        if addrStem in self.doubleMap.keys():
            self.sendToUI(self.doubleMap[addrStem] + "/" + str(15-y + 1) + "/" + str(15-x + 1), stuff[0])
            print "SEND TO", self.doubleMap[addrStem] + "/" + str(15-y + 1) + "/" + str(15-x + 1)

    def doubleGridHandler(self, addr, tags, stuff, source):
        x, y = self.doubleGridAddrToInd(addr)
        print x, y
        addrStem = "/".join(addr.split("/")[0:2])
        if addrStem in self.doubleMap.keys():
            newAddr = self.doubleMap[addrStem] + "/" + str(x+1) + "/" + str(16-y)
            k = int(self.doubleMap[addrStem].split("/")[1]) - 1
            i = x
            j = 15 - y
            self.sendToUI(newAddr, 1)
            self.bounceBack(newAddr, tags, stuff, source, self.gridcallbacks[k][i][j])

    def doubleGridSelector(self, addr, tags, stuff, source):
        selectorInd = addr.split("/")[1].split("_")[1]
        selectedIndex = 4 - int(addr.split("/")[3])

        if "/doubleGrid_"+selectorInd in self.doubleMap.keys():
            self.doubleMap.pop(self.doubleMap.pop("/doubleGrid_"+selectorInd))

        self.doubleMap["/doubleGrid_"+selectorInd] = "/" + str(selectedIndex+1) + "/grid"
        self.doubleMap["/" + str(selectedIndex+1) + "/grid"] = "/doubleGrid_"+selectorInd

        rotatedGrid = self.rotateGridLeft(self.gridStates[selectedIndex].grid)
        for i in range(len(rotatedGrid)):
            for j in range(len(rotatedGrid)):
                self.sendToUI("/doubleGrid_"+selectorInd + "/"+str(i+1) +"/" + str(16-j), rotatedGrid[i][j])

    @staticmethod
    def normalToDoubleGridInd(x, y):
        return

    @staticmethod
    def doubleGridAddrToInd(addr):
        oldX = int(addr.split("/")[2]) - 1
        oldY = int(addr.split("/")[3]) - 1
        return 15-oldY, 15-oldX

    @staticmethod
    def rotateGridLeft(grid):
        newGrid = [[0 for i in range(16)] for j in range(16)]
        for i in range(16):
            for j in range(16):
                newGrid[15-j][i] = grid[i][j]
        return newGrid

    # helper function for saving
    @staticmethod
    def gridKeyToString(grid, key):
        strgrid = [[str(grid[i][j]) for i in range(len(grid))] for j in range(len(grid))]
        colstr = [",".join(strgrid[i]) for i in range(len(strgrid))]
        gridstring = ";".join(colstr)

        strkey = [str(i) for i in key]
        keystr = ",".join(strkey)
        return gridstring + "+" + keystr

    # helper function for saving
    @staticmethod
    def stringToGridKey(string): #rename
        gridstring = string.split("+")[0]
        colstr = gridstring.split(";")
        strgrid = [i.split(",") for i in colstr]
        grid = [[round(float(strgrid[i][j])) for i in range(len(strgrid))] for j in range(len(strgrid))]

        keystr = string.split("+")[1]
        strkey = keystr.split(",")
        key = [int(i) for i in strkey]
        return grid, key

    # helper function for saving
    def miniStateToString(self, grid, scale, root, colsub, si, colsel=False): #TODO: fix colsel keyword hack
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        if melodyState.isColSubLooping or colsel:
            colsublist = [str(i) for i in colsub]
        else:
            colsublist = []
        colsubstring = ";".join(colsublist)

        rootstr = str(root)

        return self.gridKeyToString(grid, scale) + "+" + rootstr + "+" + colsubstring

    ##TODO: NEEDS UPDATING
    # helper function for saving
    def stringToMiniState(self, string):
        grid, scale = self.stringToGridKey(string.split("+")[0]+"+"+string.split("+")[1])

        root = int(string.split("+")[2])
        if string.split("+")[3].split(";")[0] == "":
            colsub = []
        else:
            colsub = [int(i) for i in string.split("+")[3].split(";")]
        return grid, scale, root, colsub

    # helper function for saving
    def stateToString(self, si):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        liveMini = self.miniStateToString(state.grid, melodyState.scale, melodyState.root, melodyState.columnSubsetLooping, si)
        miniList = [liveMini]
        for i in range(len(state.savedGrid)):
            if state.savedGrid[i] == 0:
                miniList.append("")
            else:
                miniList.append(state.savedGrid[i])
        return ":".join(miniList)

    # helper function for saving
    def stringToState(self, stateString, si):
        state = self.gridStates[si]
        miniStrList = stateString.split(":")
        grid, key, root, col = self.stringToMiniState(miniStrList[0])
        self.putMiniStateLive(grid, key, root, col, si)
        for i in range(len(state.savedGrid)):
            if miniStrList[i+1] == "":
                state.savedGrid[i] = 0
            else:
                state.savedGrid[i] = miniStrList[i+1]
                self.sendToUI("/" + str(si+1) + "/gridsave/" + str(i+1) + "/1", 1)

    # helper function for saving
    def setToString(self):
        stateStrs = []
        for si in range(self.num):
            stateStrs.append(self.stateToString(si))
        return "-".join(stateStrs)

    # helper function for saving
    def stringToSet(self, setString):
        stateStrs = setString.split("-")
        for si in range(self.num):
            self.stringToState(stateStrs[si], si)

    # hanlder for set-save control, OSCaddr: /save
    def saveSet(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        f = open("SET_SkipStep.ss", "w")
        f.write(self.setToString())
        f.close()
        print "SET SAVED"

    # handler for set-load control, OSCaddr: /load 
    def loadSet(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        setString = open("SET_SkipStep.ss").read()
        self.stringToSet(setString)
        print "SET LOADED"

    # unused
    def saveState(self, si):
        f = open("savefile" + str(si) + ".ss", "w")
        f.write(self.stateToString(si))
        f.close()

    #unused 
    def loadState(self, si):
        stateStr = open("savefile" + str(si) + ".ss").read()
        self.stringToState(stateStr, si)
  
    
    ## helper function for game of life that counts the number of neighbors (with wraparound) of a cell
    @staticmethod
    def neighborCount(grid, i, j):
        count = 0
        for m in [-1, 0, 1]:
            for k in [-1, 0, 1]:
                if abs(m) + abs(k) == 0:
                    continue
                if grid[(i+m)%len(grid)][(j+k)%len(grid)] != 0:
                    count += 1
        return count       
    
    ## transformation helper function that transforms a grid to its next step according to conways game of life     
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
    
    # helper function for blending grids     
    @staticmethod
    def blend(grid1, grid2, direction, amount):
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
    
    ## transformation helper function that varries the grid respecting its structure
    @staticmethod
    def smartNoise(grid, noise):
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

    ## transformation helper function that randomly drops columns from the grid 
    @staticmethod
    def rhythmBreak(grid, noise):
        newgrid = copy.deepcopy(grid)
        cols = range(16)
        if random.uniform(0, 1) < .5:
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

    ## transformation helper function that adds harmonies to the grid
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
                                    newgrid[i%len(grid)][(j+v)%len(grid)] = 1
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


    ## handler  for the transformation function selector control, OSCaddr: /si/noiseSel/i/1                         
    def noiseSelector(self, addr, tags, stuff, source):
        if stuff[0] == 0: return
        si = int(addr.split("/")[1])  - 1 #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        i, j = self.gridAddrInd(addr)
        print i+1, "noise selector"
        melodyState.noiseInd = i+1
    
    ## handler  for the transformation trigger control, OSCaddr: /si/noiseHit
    def noiseHit(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]

        if stuff[0] == 0: return
        grid = self.noiseChoice(si, False)
        if state.offlineEdit:
            state.offlineGrid = grid
            self.pullUpGrid(grid, "/" + str(si+1) + "/offGrid")
        else:
            self.putGridLive(grid, si, False)
        
    ## transformation helper function that picks up to k (k is voices) elements to leave on from each column 
    @staticmethod
    def simplify(grid, voices):
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
    def noiseChoice(self, si, automatedNoise):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStatePadInd if automatedNoise else state.melodyStateScreenInd]
        inputGrid = [[]]
        if state.offlineEdit:     ##TODO: should noiseChoice be responsible for managing undo-stack?
            inputGrid = copy.deepcopy(state.offlineGrid)
            state.offlineUndoStack.append(copy.deepcopy(state.offlineGrid))
            print "OFFLINE NOISE", self.gridSum(inputGrid), len(state.offlineUndoStack)
        else:
            inputGrid = copy.deepcopy(melodyState.grid)
            melodyState.undoStack.append(copy.deepcopy(melodyState.grid))
        print "the noise that was selected was", melodyState.noiseInd

        g = 5

        if melodyState.noiseInd == 1:
            g = self.chordify(inputGrid, melodyState.noiselev/2)
            
        if melodyState.noiseInd == 2:
            g = self.smartNoise(inputGrid, melodyState.noiselev/2)
            
        if melodyState.noiseInd == 3:
            g = self.rhythmBreak(inputGrid, melodyState.noiselev/2)
            
        if melodyState.noiseInd == 4:
            g = self.simplify(inputGrid, melodyState.noiselev/2)

        if melodyState.algSubsets:
            g = self.columnOverlay(inputGrid, g, melodyState.algColumnSub)

        return g
    

    ## function that takes two grids and a subset of column indexes, and then for each
    ## index in the subset, replaces the first grid's column with the second
    ## RETURNS A NEW GRID - doesn't change the original grids
    @staticmethod
    def columnOverlay(baseGrid, overlayGrid, columnSet):
        g = [[0 for i in range(16)] for j in range(16)]
        for i in range(16):
            if i in columnSet:
                g[i] = copy.deepcopy(overlayGrid[i])
            else:
                g[i] = copy.deepcopy(baseGrid[i])
        return g
        
    ## handler  for the undo button, OSCaddr: /si/undo
    def undo(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1  #index of grid action was taken on
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        if stuff[0] == 0: return
        if state.offlineEdit:
            if len(state.offlineUndoStack) == 0: return
            topstack = state.offlineUndoStack.pop()
            print "offline undo", self.gridDif(topstack, state.offlineGrid), len(state.offlineUndoStack)
            state.offlineGrid = topstack
            self.pullUpGrid(state.offlineGrid, "/" + str(si+1) + "/offGrid")
        else:
            if len(melodyState.undoStack) == 0: return
            with state.lock:
                melodyState.grid = melodyState.undoStack.pop()
                melodyState.prog = self.gridToProg(melodyState.grid, melodyState.scale, melodyState.root)
                self.pullUpGrid(melodyState.grid, "/" +str(si+1) + "/grid")
    
    #helper function that returns the hamming distance between two grids   
    @staticmethod
    def gridDif(g1, g2):
        hamming = 0
        print "hamming", len(g1), len(g2)
        for i in range(len(g1)):
            for j in range(len(g2)):
                if g1[i][j] != g2[i][j]: #both not zero or both zero
                    print i, j, "index check", g1[i][j], g2[i][j]
                    hamming += 1
        return hamming
    
    ## transformation helper function that randomly flips elements of the grid on or off 
    @staticmethod
    def naiveNoise(grid, lev):
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

    #TODO: update for melodyStates
    #helper function that puts a grid into active use
    def putGridLive(self, grid, si, automatedChange):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStatePadInd if automatedChange else state.melodyStateScreenInd]
        melodyState.grid = grid
        if not automatedChange or state.melodyStateScreenInd == state.melodyStatePadInd:
            self.pullUpGrid(melodyState.grid, "/" + str(si+1) + "/grid")
        melodyState.prog = self.gridToProg(melodyState.grid, melodyState.scale, melodyState.root)

    ##TODO: update for melodyStates - CURRENTLY UNUSED
    ## helper function that takes the variables of a miniState and makes them the active mini state 
    def putMiniStateLive(self, grid, scale, root, columnSubsetLooping, si):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateInd]
        #with state.lock:
        melodyState.customScale = [1+i for i in scale]
        melodyState.grid = grid
        melodyState.scale = scale
        melodyState.root = root
        melodyState.columnSubsetLooping = columnSubsetLooping
        melodyState.prog = self.gridToProg(melodyState.grid, melodyState.scale, melodyState.root)
        if len(columnSubsetLooping) == 0:
            melodyState.isColSubLooping = False
            self.sendToUI("/" +str(si+1) + "/colsel", 0)        
            #change UI, switch and selecors
        else:
            melodyState.isColSubLooping = True
            self.sendToUI("/" +str(si+1) + "/colsel", 1)
        for i in range(16):
            if i in columnSubsetLooping:
                self.sendToUI("/" +str(si+1) + "/col/" + str(i+1) + "/1", 1)
            else:
                self.sendToUI("/" +str(si+1) + "/col/" + str(i+1) + "/1", 0)
            #change UI, switch and selecors
        self.pullUpGrid(grid, "/" +str(si+1) + "/grid")
        self.pullUpScale(scale, "/" +str(si+1) + "/custScale")
        self.updateNoteLabels(scale, si)

    
    ## helper function that changes the note labels when a scale is changed 
    def updateNoteLabels(self, scale, si):
        state = self.gridStates[si]
        melodyState = state.melodyStates[state.melodyStateScreenInd]
        notes = self.scaleNotes(melodyState.root, scale)
        print "in label update"
        for i in range(16):
            #print self.notenames[notes[i]%12]
            self.sendToUI("/"+str(si+1)+"/notelabel/" + str(i+1), self.notenames[notes[i]%12])

    ## handler  function for the minipage selector control, OSCaddr: /si/pageSelector/1/i 
    def changeMiniPage(self, addr, tags, stuff, source):
        si = int(addr.split("/")[1]) - 1
        state = self.gridStates[si]
        ind = 5 - int(addr.split("/")[4]) #used to be 4 - ...
        print "\nIND: ", ind, "\n"
            
        msg = OSC.OSCMessage()
        for ad in self.miniPages[ind]:
            msg.setAddress("/" + str(si+1) + ad + "/visible")
            msg.append(stuff[0])
            print msg
            for cli in self.iPadClients: 
                if cli.address()[0] == source[0]:
                    cli.send(msg) #self.oscClientUI.send(msg)
            msg.clear()

    ## TODO responsealgs: add button and handler for this method
    ## uses grid and offline grid of instrument 1 as old control grid and changed control grid respectively
    ## and uses the grid of instrument 2 as the target grid. a single button hit launches the
    ## response function which is copied and pasted into the responseAlg() function
    #currently quadShift
    def applyResponseAlg(self, addr, tags, stuff, source):

        if stuff[0] == 0: return

        state1 = self.gridStates[0]
        state2 = self.gridStates[1]

        newg = self.responseAlg(state1.grid, state1.offlineGrid, state2.grid)

        self.pullUpGrid(newg, "/2/grid")
        state2.grid = newg
        state2.prog = self.gridToProg(state2.grid, state2.scale, state2.root)

    def responseAlg(self, oldGrid, newGrid, targetGrid):
        shifts = [0] * 4
        g =  [[0 for i in range(16)] for j in range(16)]
        for i1 in range(4):
            oldYsum = 0
            newYsum = 0
            oldYcount = 0
            newYcount = 0
            for i2 in range(4):
                for j in range(16):
                    oldYcount += oldGrid[4*i1+i2][j]
                    newYcount += newGrid[4*i1+i2][j]
                    if oldGrid[4*i1+i2][j] == 1 : oldYsum += j
                    if newGrid[4*i1+i2][j] == 1 : newYsum += j
            print "oldYsum", oldYsum, "newYsum", newYsum, "oldYcount", oldYcount, "newYcount", newYcount
            shifts[i1] = int(1.0*newYsum/newYcount - 1.0*oldYsum/oldYcount)

            if shifts[i1] == 0 : continue
            if shifts[i1] > 0:
                oldCopy = copy.deepcopy(oldGrid)
                for i in range(shifts[i1]):
                    oldCopy = self.gridShift(oldCopy, "up")
                g = self.columnOverlay(g, oldCopy, range(4*i1, 4*i1+4))
            if shifts[i1] < 0:
                oldCopy = copy.deepcopy(oldGrid)
                for i in range(abs(shifts[i1])):
                    oldCopy = self.gridShift(oldCopy, "down")
                g = self.columnOverlay(g, oldCopy, range(4*i1, 4*i1+4))
        return g
                 
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
port = -1
if res[0] == 0: #solo
    #threading.Thread(target = startSoloBackend).start()
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
try:
    loop = MultiLoop(4, port)
    #loop2 = Looper(p, trans)
    #loop.check()
    loop.uiStart()
    loop.playStart()
    #loop.loopStart()
except KeyboardInterrupt:
    print "stopped"
    loop.oscServUI.close()
    loop.oscServSelf.close()

